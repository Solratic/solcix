import argparse
import os
import shutil
from typing import Any, List, Tuple
from solcix.errors import NotInstalledError, NoSolcVersionInstalledError
from solcix.constant import SOLCIX_DIR, ARTIFACT_DIR
from solcix.installer import (
    get_available_versions,
    get_installed_versions,
    install_solc,
)


def current_version() -> Tuple[str, str]:
    """
    Get the current version of the Solidity compiler.
    Local version takes precedence over global version.

    Returns:
    --------
    A tuple containing the current version and the source of the version information.
    """
    if os.path.isfile(".solcix"):
        with open(".solcix", "r", encoding="utf-8") as f:
            version = f.read()
            source = ".solcix"
    else:
        source: str = "SOLC_VERSION"
        version: Any = os.environ.get(source)

    if not version:
        source_path = SOLCIX_DIR.joinpath("global-version")
        source = source_path.as_posix()

        if source_path.is_file():
            with open(source_path, encoding="utf-8") as f:
                version = f.read()
        else:
            raise NotInstalledError(
                "💫 No solc version set. Run `solcix global VERSION`, `solcix local Version` or set SOLC_VERSION environment variable. 💫"
            )

    versions: List[str] = get_installed_versions()

    if version not in versions:
        raise NotInstalledError(
            f"\n😱 Version '{version}' not installed (set by {source}). 😱"
            f"\nRun `solcix install {version}`."
            f"\nOr use one of the following versions: {versions}"
        )

    return version, source


def switch_local_version(version: str, always_install: bool) -> None:
    """
    Switches the local version of the Solidity compiler to the specified version.

    Parameters:
    -----------
    version : str
        The version of the Solidity compiler to switch to.
    always_install : bool
        Whether to automatically install the specified version if it is not already installed.

    Raises:
    -------
    argparse.ArgumentTypeError:
        - If the specified version is not installed and always_install is False.
        - If the specified version is unknown.

    Returns:
    --------
    None
    """

    if version in get_installed_versions():
        with open(".solcix", "w", encoding="utf-8") as f:
            f.write(version)
        print(f"✨ Switched local version to {version} ✨")
        return

    releases, _ = get_available_versions()
    if version in releases:
        if always_install:
            install_solc([version])
            switch_local_version(version, always_install)
        else:
            raise NotInstalledError(f"'{version}' must be installed prior to use.")
    else:
        raise NoSolcVersionInstalledError(version)


def switch_global_version(version: str, always_install: bool) -> None:
    """
    Switches the global version of the Solidity compiler to the specified version.

    Parameters:
    -----------
    version : str
        The version of the Solidity compiler to switch to.
    always_install : bool
        Whether to automatically install the specified version if it is not already installed.

    Raises:
    -------
    argparse.ArgumentTypeError:
        - If the specified version is not installed and always_install is False.
        - If the specified version is unknown.

    Returns:
    --------
    None
    """
    if version in get_installed_versions():
        with open(SOLCIX_DIR.joinpath("global-version"), "w", encoding="utf-8") as f:
            f.write(version)
        print(f"✨ Switched global version to {version} ✨")
        return

    releases, _ = get_available_versions()
    if version in releases:
        if always_install:
            install_solc([version])
            switch_global_version(version, always_install)
        else:
            raise NotInstalledError(f"'{version}' must be installed prior to use.")
    else:
        raise NoSolcVersionInstalledError(version)


def upgrade_architecture() -> None:
    """
    Upgrade the architecture.

    If there are installed versions of solc, remove the current ARTIFACT_DIR directory and install the latest
    version of solc.

    Raises:
    -------
    argparse.ArgumentTypeError
        If there are no installed versions of solc.

    """
    currently_installed = get_installed_versions()
    if len(currently_installed) > 0:
        shutil.rmtree(ARTIFACT_DIR)
        os.makedirs(ARTIFACT_DIR, exist_ok=True)
        install_solc(currently_installed)
        print("🔥 solcix is now up to date! 🔥")
    else:
        raise argparse.ArgumentTypeError(
            "Run `solcix install --help` for more information"
        )
