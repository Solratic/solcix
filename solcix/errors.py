from typing import List, Dict, Any
import json


class UnsupportedPlatformError(Exception):
    def __init__(self, platform: str) -> None:
        self.platform = platform

    def __str__(self) -> str:
        return f"Unsupported platform: {self.platform}"


class ChecksumMissingError(Exception):
    def __init__(self, platform: str, version: str) -> None:
        self.platform = platform
        self.version = version

    def __str__(self) -> str:
        return f"Unable to retrieve checksum for {self.platform} - {self.version}"


class ChecksumMismatchError(Exception):
    def __init__(self, platform: str, version: str) -> None:
        self.platform = platform
        self.version = version

    def __str__(self) -> str:
        return f"Checksum mismatch {self.platform} - {self.version}"


class NoCompatibleVersionError(Exception):
    def __init__(self, type: str, value: str) -> None:
        self.type = type
        self.value = value

    def __str__(self) -> str:
        return f"No compatible version found, {self.type} version is {self.value}"


class NoSolcVersionInstalledError(Exception):
    def __init__(self, version: str = "") -> None:
        self.version = version

    def __str__(self) -> str:
        return f"Solc {self.version} is not installed. Call solcix.get_installable_versions() to view for available versions and solcix.install({self.version}) to install."


class UnrecognizedOptionError(Exception):
    def __init__(self, option: str) -> None:
        self.option = option

    def __str__(self) -> str:
        return f"solc does not support the '{self.option}' option"


class InvalidOptionError(Exception):
    def __init__(self, flag: str, option: str) -> None:
        self.flag = flag
        self.option = option

    def __str__(self) -> str:
        return f"solc does not accept '{self.option}' as an option for the '{self.flag}' flag"


class ContractNotFoundError(Exception):
    def __init__(self, input_data: Dict[str, Any]):
        self.input_data = json.dumps(input_data, sort_keys=True, indent=2)

    def __str__(self) -> str:
        return (
            "Input JSON does not contain any file"
            f"or contract information. Please check your input: {self.input_data}"
        )


class SolcError(Exception):
    message = "An error occurred during execution"

    def __init__(
        self,
        message: str = None,
        command: List = None,
        return_code: int = None,
        stdin_data: str = None,
        stdout_data: str = None,
        stderr_data: str = None,
        error_dict: Dict = None,
    ) -> None:
        if message is not None:
            self.message = message
        self.command = command or []
        self.return_code = return_code
        self.stdin_data = stdin_data
        self.stderr_data = stderr_data
        self.stdout_data = stdout_data
        self.error_dict = error_dict

    def __str__(self) -> str:
        return (
            f"{self.message}"
            f"\n> command: `{' '.join(str(i) for i in self.command)}`"
            f"\n> return code: `{self.return_code}`"
            "\n> stdout:"
            f"\n{self.stdout_data}"
            "\n> stderr:"
            f"\n{self.stderr_data}"
        ).strip()


class NotInstalledError(Exception):
    def __init__(self, msg: str) -> None:
        self.msg = msg

    def __str__(self) -> str:
        return self.msg
