import re


def is_valid_version(version: str) -> bool:
    """
    Check if a version string is valid.

    Parameters
    ---------
        version: A string representing a version number.

    Returns
    -------
        A boolean value indicating whether the version string is valid.

    Raises
    ------
        None

    Examples
    --------
        >>> is_valid_version("1.2.3")
        True
        >>> is_valid_version("1.2.3.4")
        False
        >>> is_valid_version("1.2.alpha")
        False
    """
    pattern = r"^\d+\.\d+\.\d+$"
    return bool(re.match(pattern, version))
