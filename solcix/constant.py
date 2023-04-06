from enum import Enum
from pathlib import Path
import os


class Platform(Enum):
    MACOS = "macosx-amd64"
    LINUX = "linux-amd64"
    WINDOWS = "windows-amd64"


class EarliestRelease(Enum):
    MACOS = "0.3.6"
    LINUX = "0.4.0"
    WINDOWS = "0.4.1"


HOME = Path(os.environ.get("VIRTUAL_ENV", Path.home()))
SOLCIX_DIR = HOME.joinpath(".solcix")
ARTIFACT_DIR = HOME.joinpath(".solcix", "artifacts")

CRYTIC_SOLC_ARTIFACTS = (
    "https://raw.githubusercontent.com/crytic/solc/master/linux/amd64/"
)
CRYTIC_SOLC_JSON = (
    "https://raw.githubusercontent.com/crytic/solc/new-list-json/linux/amd64/list.json"
)
