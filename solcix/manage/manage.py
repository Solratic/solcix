import os
import shutil
from solcix.errors import NotInstalledError, NoSolcVersionInstalledError
from solcix.constant import SOLCIX_DIR, ARTIFACT_DIR
from solcix.installer import (
    get_available_versions,
    get_installed_versions,
    install_solc,
)


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
    NotInstalledError
        If there are no installed versions of solc.

    """
    currently_installed = get_installed_versions()
    if len(currently_installed) > 0:
        shutil.rmtree(ARTIFACT_DIR)
        os.makedirs(ARTIFACT_DIR, exist_ok=True)
        install_solc(currently_installed)
        print("🔥 solcix is now up to date! 🔥")
    else:
        raise NotInstalledError("Run `solcix install --help` for more information")


def clear_config() -> None:
    """
    Clears the current (may be global or local) configuration file.

    Returns:
    --------
    None
    """
    if os.path.exists(".solcix"):
        os.remove(".solcix")
        print("✨ Cleared local configuration ✨")
    elif os.path.exists(SOLCIX_DIR.joinpath("global-version")):
        os.remove(SOLCIX_DIR.joinpath("global-version"))
        print("✨ Cleared global configuration ✨")
