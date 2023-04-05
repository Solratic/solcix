import os
from .constant import ARTIFACT_DIR
from .__version__ import __version__
from .solcixtype import PRAGMA_TYPE, Version
from .installer import (
    get_available_versions,
    get_installable_versions,
    get_installed_versions,
    get_latest_version,
    get_executable,
    clear_cache,
    install_solc,
    uninstall_solc,
)
from .resolver import (
    get_compatible_versions,
    get_recommended_version,
    install_solc_from_solidity,
    resolve_version_from_solidity,
)
from .compile import (
    compile_files,
    compile_source,
    compile_standard,
    solc_execute,
)


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
    # Resolver
    "get_compatible_versions",
    "get_recommended_version",
    "install_solc_from_solidity",
    "resolve_version_from_solidity",
    # Compile
    "compile_files",
    "compile_source",
    "compile_standard",
    "solc_execute",
    # Types
    "PRAGMA_TYPE",
    "Version",
]


def __init__() -> None:
    """
    Initialize the module.
    """
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
