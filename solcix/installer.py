import hashlib
import json
import os
import sys
from collections import defaultdict
from glob import glob
from os import access, makedirs
from pathlib import Path
from typing import Iterable, Tuple, List, Union
from urllib.request import urlopen, urlretrieve
from zipfile import ZipFile
import shutil

from Crypto.Hash import keccak
from joblib import Memory

from solcix.__version__ import __version__
from solcix.constant import (
    ARTIFACT_DIR,
    CRYTIC_SOLC_ARTIFACTS,
    CRYTIC_SOLC_JSON,
    EarliestRelease,
    Platform,
)
from solcix.errors import (
    ChecksumMismatchError,
    ChecksumMissingError,
    NoSolcInstalledError,
    UnsupportedPlatformError,
)
from solcix.datatypes import Version, ProgressBar

cachedir = ARTIFACT_DIR.joinpath(".solcix", "cache", __version__)
memory = Memory(cachedir, verbose=0)


def clear_cache() -> None:
    """
    Clears the cache directory used by `solc_execute` and `solcx.compile_*` functions.

    Notes
    -----
    The cache directory is located at "{ARTIFACT_DIR}/.solcix/cache/{version}".
    This function deletes all files within that directory.

    """
    for file in ARTIFACT_DIR.joinpath(".solcix", "cache").iterdir():
        file.unlink()


def _get_platform() -> Platform:
    """Returns the platform name for the current platform."""
    if sys.platform.startswith("linux"):
        return Platform.LINUX
    elif sys.platform.startswith("darwin"):
        return Platform.MACOS
    elif sys.platform in {"win32", "cygwin"}:
        return Platform.WINDOWS
    else:
        raise UnsupportedPlatformError(sys.platform)


def _is_older_linux(version: str) -> bool:
    """
    Determines whether the specified version of Solidity is older than 0.4.0 on Linux.

    Args:
        version (str): The version of Solidity to check.

    Returns:
        A boolean value indicating whether the specified version of Solidity is older than 0.4.0 on Linux.

    Raises:
        None
    """
    return _get_platform() == Platform.LINUX and Version(version) <= Version("0.4.10")


def _is_older_windows(version: str) -> bool:
    return _get_platform() == Platform.WINDOWS and Version(version) <= Version("0.7.1")


def _get_url(version: str = None, artifact: str = "") -> Tuple[str, str]:
    platform = _get_platform()
    if platform == Platform.LINUX:
        if version is not None and _is_older_linux(version):
            return CRYTIC_SOLC_ARTIFACTS + artifact, CRYTIC_SOLC_JSON
    return (
        f"https://binaries.soliditylang.org/{platform.value}/{artifact}",
        f"https://binaries.soliditylang.org/{platform.value}/list.json",
    )


@memory.cache
def get_available_versions() -> Tuple[dict[str, str], str]:
    """
    Returns a tuple containing a dictionary of available Solidity compiler versions and the latest version.

    Returns
    -------
        tuple[dict[str], str]: A tuple containing a sorted dictionary of available Solidity compiler versions and the latest version.

    Examples
    --------
        >>> get_available_versions()
        ({'0.4.0': {...}, '0.4.1': {...}, '0.4.10': {...}, ...}, '0.8.4')
    """
    # Get the JSON URL for the platform
    (_, json_url) = _get_url()

    # Get the releases from the JSON file
    releases: dict = {}
    latest: str = ""
    with urlopen(json_url) as response:
        body = response.read()
        releases = json.loads(body)["releases"]
        latest = json.loads(body)["latestRelease"]

    # Add extra releases for Linux if the current platform is Linux
    if _get_platform() == Platform.LINUX:
        (_, extra_url) = _get_url(version=EarliestRelease.LINUX.value)
        with urlopen(extra_url) as response:
            extra = json.loads(response.read())["releases"]
            releases.update(extra)

    # Return the available versions and latest version as a tuple
    releases = {k: v for k, v in sorted(releases.items(), key=lambda x: Version(x[0]))}
    return releases, latest


def get_installed_versions() -> set[str]:
    """Returns a set of installed versions."""
    return {f.removeprefix("solc-") for f in glob("solc-*", root_dir=ARTIFACT_DIR)}


def get_installable_versions() -> list[str]:
    """Returns a list of installable versions ordered by version."""
    releases, _ = get_available_versions()
    installable = list(set(releases.keys()) - get_installed_versions())
    installable.sort(key=Version)
    return installable


def get_latest_version() -> str:
    """Returns the latest version of Solidity."""
    _, latest = get_available_versions()
    return latest


@memory.cache
def _get_version_dict(releases: dict[str, str]) -> dict[int, dict[int, dict[int, str]]]:
    """
    Returns a nested dictionary of Solidity compiler releases, organized by major, minor, and patch version numbers.

    Parameters
    ----------
        releases (dict[str, str]): A sorted dictionary of Solidity compiler releases, where the keys are version numbers and the values are artifact names.

    Returns
    -------
        dict[int, dict[int, dict[int, str]]]: A nested dictionary of Solidity compiler releases, where the outermost keys are major version numbers, the second-level keys are minor version numbers, and the innermost keys are patch version numbers. The values are the corresponding artifact paths.

    Examples
    --------
        >>> releases = {'0.4.0': 'solc-0.4.0', '0.4.1': 'solc-0.4.1', '0.4.10': 'solc-0.4.10', '0.8.4': 'solc-0.8.4'}
        >>> get_version_dict(releases)
        {
            0: {
                4: {
                    0: 'solc-0.4.0',
                    1: 'solc-0.4.1',
                    10: 'solc-0.4.10'
                }
            },
            8: {
                4: {
                    0: 'solc-0.8.4'
                }
            }
        }
    """
    version_dict = defaultdict(lambda: defaultdict(lambda: defaultdict(str)))
    for version, artifact in releases.items():
        major, minor, patch = map(int, version.split("."))
        version_dict[major][minor][patch] = artifact
    return version_dict


@memory.cache
def _get_version_objects(releases: dict[str, str]) -> list[Version]:
    """
    Retrieve a list of Version objects from a dictionary of release versions.

    Parameters
    ----------
        releases: A dictionary of release versions, where the keys are version
            strings and the values are release dates.

    Returns
    -------
        A list of Version objects corresponding to the release versions in the
        input dictionary.
    """
    return [Version(version) for version in releases.keys()]


def _get_checksums(version: str) -> Tuple[str, str]:
    """
    Returns the SHA256 and Keccak256 checksums for the specified Solidity compiler version.

    Parameters
    ----------
        version (str): The version of the Solidity compiler.

    Returns
    -------
        tuple[str, str]: A tuple containing the SHA256 and Keccak256 checksums for the specified version.

    Raises
    ------
        ValueError: If the specified version or platform is not supported, or if the checksums cannot be retrieved.

    Examples
    --------
        >>> get_checksums('0.8.0')
        ('771eaa082fe8b3002ed0e526d7b9c883ea8a670d2e0e64378739cb1cafa32d8c', 'ce12f0f0ed9c65438f5c5de81b5dcd14e6c007711f8e49c30710975d62b01c23')

        >>> get_checksums('latest')
        ('b635a39a6e669f607a45dcbd5d02e5c5f5e41dd63c63d46b66ecf7e6a1b6d725', 'a27b2a9db3f3f1d7a6e4d2c7b3a3a48de7c4a4f9ad7a84c4bc45ec7d6781d62c')
    """
    (_, list_url) = _get_url(version=version)
    with urlopen(list_url) as response:
        builds = json.loads(response.read())["builds"]
        matches = list(filter(lambda b: b["version"] == version, builds))
    if not matches or not matches[0]["sha256"]:
        raise ChecksumMissingError(_get_platform().value, version)
    return matches[0]["sha256"], matches[0]["keccak256"]


def _verify_checksum(version: str) -> None:
    """
    Verifies the SHA256 and Keccak256 checksums of the local Solidity compiler artifact file.

    Parameters
    ----------
        version : str
            The version of the Solidity compiler.

    Raises
    ------
        ValueError
            If the specified version or platform is not supported, or if the checksums do not match.

    Examples
    --------
        >>> verify_checksum('0.8.0')
        None
    """
    # Get the SHA256 and Keccak256 checksums of the specified Solidity compiler version
    sha256_hash, keccak256_hash = _get_checksums(version)

    # Calculate the SHA256 and Keccak256 checksums of the local file
    path = f"solc-{version}"
    with open(ARTIFACT_DIR.joinpath(path, path), "rb") as f:
        sha256_factory = hashlib.sha256()
        keccak_factory = keccak.new(digest_bits=256)

        for chunk in iter(lambda: f.read(1024000), b""):
            sha256_factory.update(chunk)
            keccak_factory.update(chunk)

    # Compare the calculated checksums with the expected checksums
    local_sha256_file_hash = f"0x{sha256_factory.hexdigest()}"
    local_keccak256_file_hash = f"0x{keccak_factory.hexdigest()}"
    if (sha256_hash, keccak256_hash) != (
        local_sha256_file_hash,
        local_keccak256_file_hash,
    ):
        raise ChecksumMismatchError(_get_platform().value, version)


def _get_earliest_release() -> str:
    """
    Returns the earliest release version of the Solidity compiler.

    Returns
    -------
        str: The earliest release version of the Solidity compiler by OS.

    Examples
    --------
        >>> get_earliest_release()
        '0.4.0'
    """
    if _get_platform() == Platform.LINUX:
        return EarliestRelease.LINUX.value
    elif _get_platform() == Platform.MACOS:
        return EarliestRelease.MACOS.value
    elif _get_platform() == Platform.WINDOWS:
        return EarliestRelease.WINDOWS.value


def _get_default_solc_path(program: Union[str, Path]) -> Union[Path, None]:
    def is_executable(path: Path) -> bool:
        return path.is_file() and access(path, os.X_OK)

    fpath, _ = os.path.split(program)
    if fpath:
        if is_executable(fpath):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = Path(path).joinpath(program)
            if is_executable(exe_file):
                return exe_file
    return None


def install_solc(
    versions: str | Iterable[str],
    use_cache: bool = True,
    verbose: bool = True,
) -> tuple[list[str], list[str], list[str]]:
    """
    Downloads and installs Solidity compiler versions specified in the `versions` parameter.

    Parameters
    ----------
    - versions : str | Iterable[str]
        The version(s) of the Solidity compiler to download and install. If a string is provided,
        only one version will be installed. If an iterable is provided, multiple versions can be installed at once.
        If the string 'latest' is provided, the latest version of the Solidity compiler will be installed.
    - use_cache : bool, optional
        If True, the function will check the local cached version list before downloading a new version. The default is True.

    Returns
    -------
    tuple[list[str], list[str], list[str]]
        A tuple containing three lists: (1) the list of successfully installed versions, (2) the list of
        skipped versions (i.e., already installed), and (3) the list of versions that could not be installed.

    Raises
    ------
    ValueError
        If the version provided is not valid or if the checksums do not match.

    Examples
    --------
    >>> install('0.8.0')
    (['0.8.0'], [], [])

    >>> install(['0.7.6', 'latest'])
    (['0.7.6', '0.8.0'], ['0.8.0'], [])
    """
    # Clear cache if requested
    if not use_cache:
        memory.clear()

    if isinstance(versions, str):
        versions = [versions]

    # Get available versions from remote server
    releases, latest = get_available_versions()

    # Map available versions to a dictionary
    version_dict = _get_version_dict(releases)

    # Replace 'latest' with latest version available
    versions = [latest if v == "latest" else v for v in versions]

    installed = get_installed_versions()

    success = []
    skipped = []
    errors = []

    # Download and install specified versions
    for version in versions:
        try:
            major, minor, patch = map(int, version.split("."))
        except ValueError:
            errors.append(version)
            continue

        if version in installed:
            skipped.append(version)
            continue

        artifact = version_dict[major][minor][patch]
        if artifact == "":
            errors.append(version)
            continue

        # Download artifact
        (url, _) = _get_url(version=version, artifact=artifact)
        artifact_parent = Path(ARTIFACT_DIR.joinpath(f"solc-{version}"))
        artifact_path = Path(artifact_parent.joinpath(f"solc-{version}"))
        makedirs(artifact_parent, exist_ok=True)
        urlretrieve(
            url=url,
            filename=artifact_path,
            reporthook=ProgressBar(version) if verbose else None,
        )

        # Verify artifact checksum
        _verify_checksum(version)

        # Extract artifact and rename if necessary
        if _is_older_windows(version):
            with ZipFile(artifact_path, "r") as f:
                f.extractall(path=artifact_parent)
                f.close()
            artifact_path.unlink()
            executable = Path(artifact_parent.joinpath("solc.exe"))
            executable.rename(artifact_parent.joinpath(f"solc-{version}"))
        else:
            artifact_path.chmod(0o755)

        success.append(version)

    return success, skipped, errors


def get_executable(
    version: Union[str, Version] = None, solc_path: Union[Path, str] = None
) -> Union[Path, None]:
    """
    Get the path of the installed solc binary.

    Parameters
    ----------
    version: str or Version, optional
        The version of solc to look for. If None, returns the default installed solc binary.
    solc_path: Path or str, optional
        The path to a solc binary. If provided, ignores version param and returns the path to the binary if it exists.

    Returns
    -------
    Path or None
        Returns the path of the installed solc binary if it exists, otherwise returns None.

    Raises
    ------
    NoSolcInstalledError
        If the specified solc version is not installed or if no default solc binary is installed.
    """
    if solc_path is not None:
        executable_path = Path(solc_path)
        if executable_path.exists():
            return executable_path
        raise NoSolcInstalledError(f"solc binary not found at path: {executable_path}")

    if version is None:
        default_executable_path = _get_default_solc_path("solc")
        if default_executable_path is None:
            raise NoSolcInstalledError("No default solc binary found")
        return default_executable_path

    artifact_parent = Path(ARTIFACT_DIR.joinpath(f"solc-{version}"))
    artifact_path = Path(artifact_parent.joinpath(f"solc-{version}"))

    if not artifact_path.exists():
        raise NoSolcInstalledError(f"solc version {version} is not installed")

    return artifact_path


def uninstall_solc(
    versions: str | Iterable[str],
    verbose: bool = True,
) -> Tuple[List[str], List[str], List[str]]:
    """
        Uninstall solc version(s) by deleting their artifacts from disk.

    Parameters
    ----------
        - versions (str or Iterable[str]): The version(s) of solc to uninstall. The format of the version should be in major.minor.patch format.
        - verbose (bool): If True, print uninstallation status for each version.

    Returns
    -------
        Tuple[List[str], List[str], List[str]]: A tuple containing 3 lists:
        - success: versions that have been successfully uninstalled
        - skipped: versions that were not found and therefore were skipped
        - errors: versions that caused errors during uninstallation

    Raises
    ------
        None

    Example
    -------
    `Uninstall a single version`
    >>> uninstall_solc("0.8.0")
    (['0.8.0'], [], [])

    `Uninstall multiple versions`
    >>> uninstall_solc(["0.8.0", "0.7.0"])
    (['0.8.0', '0.7.0'], [], [])

    `Uninstall a version that does not exist`
    >>> uninstall_solc("0.9.0")
    ([], ['0.9.0'], [])

    `Uninstall a version that causes errors (e.g. in use, permission denied)`
    >>> uninstall_solc("0.6.0")
    ([], [], ['0.6.0'])

    """
    if isinstance(versions, str):
        versions = [versions]

    installed = get_installed_versions()

    success = []
    skipped = []
    errors = []

    for version in versions:
        if version not in installed:
            skipped.append(version)
            continue
        artifact_path = Path(ARTIFACT_DIR.joinpath(f"solc-{version}"))
        try:
            if artifact_path.is_dir():
                shutil.rmtree(artifact_path)
            else:
                artifact_path.unlink()
            if verbose:
                print(f"Uninstalling solc version {version}")
        except Exception as e:
            if verbose:
                print(f"solc version {version} cannot remove, since {e}")
            errors.append(version)

        success.append(version)

    return success, skipped, errors
