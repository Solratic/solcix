import os
from .constant import ARTIFACT_DIR
from .installer import (
    get_available_versions,
    get_installable_versions,
    get_installed_versions,
    get_latest_version,
    get_executable,
    clear_cache,
    install_solc,
    uninstall_solc,
    verify_solc,
    current_version,
)
from .resolver import (
    get_compatible_versions,
    get_recommended_version,
    install_solc_from_solidity,
    resolve_version_from_solidity,
)
from . import datatypes, compile, manage


__all__ = [
    # Installer
    "get_available_versions",
    "get_installable_versions",
    "get_installed_versions",
    "get_latest_version",
    "get_executable",
    "clear_cache",
    "install_solc",
    "uninstall_solc",
    "verify_solc",
    "current_version",
    # Resolver
    "get_compatible_versions",
    "get_recommended_version",
    "install_solc_from_solidity",
    "resolve_version_from_solidity",
    # Compile
    "compile",
    # Manage
    "manage",
    # Types
    "datatypes",
]


def __init__() -> None:
    """
    Initialize the module.
    """
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
