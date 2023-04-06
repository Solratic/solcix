from typing import Union, Tuple, Optional
from tqdm import tqdm
from ..utils import is_valid_version

PRAGMA_TYPE = Union[
    None,
    Tuple[Tuple[str, int, int, int], Tuple[str, int, int, int]],
    Tuple[Tuple[str, int, int, int], None],
]


class Version:
    def __init__(self, version: str) -> None:
        """
        Initialize a Version object from a version string.

        Parameters
        ----------
            version: A string representing the version, in the format "major.minor.patch".

        Raises
        ------
            AssertionError: If the input version string does not have exactly three segments
                separated by periods.
        """
        assert is_valid_version(version), f"Invalid version string {version}"
        self.major, self.minor, self.patch = map(int, version.split("."))

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, Version):
            raise NotImplementedError
        return (
            self.major == __value.major
            and self.minor == __value.minor
            and self.patch == __value.patch
        )

    def __ne__(self, __value: object) -> bool:
        if not isinstance(__value, Version):
            raise NotImplementedError
        return (
            self.major != __value.major
            or self.minor != __value.minor
            or self.patch != __value.patch
        )

    def __lt__(self, __value: object) -> bool:
        if not isinstance(__value, Version):
            raise NotImplementedError
        return (self.major, self.minor, self.patch) < (
            __value.major,
            __value.minor,
            __value.patch,
        )

    def __gt__(self, __value: object) -> bool:
        if not isinstance(__value, Version):
            raise NotImplementedError
        return (self.major, self.minor, self.patch) > (
            __value.major,
            __value.minor,
            __value.patch,
        )

    def __le__(self, __value: object) -> bool:
        if not isinstance(__value, Version):
            raise NotImplementedError
        return (self.major, self.minor, self.patch) <= (
            __value.major,
            __value.minor,
            __value.patch,
        )

    def __ge__(self, __value: object) -> bool:
        if not isinstance(__value, Version):
            raise NotImplementedError
        return (self.major, self.minor, self.patch) >= (
            __value.major,
            __value.minor,
            __value.patch,
        )

    def __xor__(self, __value: object) -> bool:
        if not isinstance(__value, Version):
            raise NotImplementedError
        return (
            (self.major == __value.major)
            and (self.minor == __value.minor)
            and (self.patch >= __value.patch)
        )

    def __repr__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


class ProgressBar:
    def __init__(self, version: str) -> None:
        self.pbar = None
        self.last_block = 0
        self.version = version

    def __call__(
        self,
        block_num: int,
        block_size: int,
        total_size: Optional[int] = None,
    ):
        """
        Show progress bar of file download.

        Args:
            block_num (int): Number of blocks downloaded so far.
            block_size (int): Size of each block (in bytes).
            total_size (Optional[int]): Total size of the file being downloaded (in bytes).

        Returns:
            None
        """
        if not self.pbar:
            self.pbar = tqdm(
                total=total_size,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
                miniters=1,
            )
            self.pbar.set_description_str(f"Downloading solc-{self.version}")
        else:
            self.pbar.update((block_num - self.last_block) * block_size)
            self.last_block = block_num
