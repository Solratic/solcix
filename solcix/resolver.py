import re
from typing import List, Union, Callable
from pathlib import Path
import os
from solcix.errors import NoCompatibleVersionError
from solcix.installer import (
    get_earliest_release,
    _get_version_dict,
    get_version_objects,
    get_available_versions,
    get_installed_versions,
    install_solc,
)
from solcix.datatypes import PRAGMA_TYPE, Version


def resolve_version_from_solidity(
    source: Union[str, Path],
) -> PRAGMA_TYPE:
    """
    Attempts to extract Solidity version information from a source string.

    Parameters
    ----------
    source : str | Path
        The Solidity source code or file path to extract version information from.

    Returns
    -------
    Union[Tuple[Tuple[str, str, str, Optional[str]], Tuple[str, str, str, Optional[str]]], Tuple[Tuple[str, str, str, Optional[str]], None]] :
        A tuple containing two tuples of version information if available.
        The first tuple contains the version components for the first pragma statement found,
        and the second tuple contains the version components for the second pragma statement if found.
        If there is only one pragma statement, the second tuple will be None.
        If no pragma statements are found , the function returns None.
        If the second pragma statement is lower than the first pragma statement, the function returns None as well.

    Examples
    --------
    >>> resolve_version_from_solidity("pragma solidity >0.5.16 <=0.8.16;")
    (('>', '0', '5', '16'), ('<=', '0', '8', '16'))

    """
    if os.path.isfile(source):
        with open(source, "r") as f:
            for line in f:
                if line.strip().startswith("pragma"):
                    source = line
                    break
    pattern = r"pragma solidity(\s*(?P<first_comp>[>^=<]*)[\s\"\']*(?P<first_1>\d+)\s*\.\s*(?P<first_2>\d+)\s*\.*\s*(?P<first_3>\d+)*[\s\"\']*)((?P<second_comp>[>^=<]*)[\s\"\']*(?P<second_1>\d+)\s*\.\s*(?P<second_2>\d+)\s*\.*\s*(?P<second_3>\d+)*[\s\"]*)*;"
    match = re.match(pattern, source)
    if match is None:
        return None
    variables = match.groupdict()
    first_comp = variables["first_comp"]
    first_1 = variables["first_1"]
    first_2 = variables["first_2"]
    first_3 = variables["first_3"]
    second_comp = variables["second_comp"]
    second_1 = variables["second_1"]
    second_2 = variables["second_2"]
    second_3 = variables["second_3"]
    if second_comp is not None and all([second_1, second_2, second_3]):
        # Check second pragma is higher than first pragma
        first_version = (int(first_1), int(first_2), int(first_3))
        second_version = (int(second_1), int(second_2), int(second_3))
        if first_version > second_version:
            return None
        return (
            (first_comp, *first_version),
            (second_comp, *second_version),
        )
    else:
        return (first_comp, int(first_1), int(first_2), int(first_3)), None


def get_compatible_versions(pragma: PRAGMA_TYPE) -> Union[List[str], str, None]:
    """
    Get a list of all the available versions that are compatible with the given Solidity pragma statement.

    Parameters
    ----------
    pragma : Union[Tuple[Tuple[str, int, int, int], None], Tuple[Tuple[str, int, int, int], Tuple[str, int, int, int]]]
        A tuple representing the Solidity pragma statement, where the first element is a tuple of the form
        (operator, major, minor, patch) and the second element is another tuple of the same form or None.

    Returns
    -------
    compatibles : Union[List[str], str, None]
        If the input pragma is None, returns None. If the input pragma is valid and there are compatible versions,
        returns a list of strings representing the compatible versions. Otherwise, returns a string representing
        the highest available version that satisfies the pragma.

    Raises
    ------
    ValueError
        If the input pragma is invalid.

    Examples
    --------
    >>> pragma = ((">=", 0, 6, 0), ("<", 0, 8, 0))
    >>> get_compatible_versions(pragma)
    ['0.6.0', '0.6.1', '0.6.2', ..., '0.7.15']

    >>> pragma = (("", 0, 7, 3), None)
    >>> get_compatible_versions(pragma)
    '0.7.3'

    """
    if pragma is None:
        return None
    releases, _ = get_available_versions()
    versions = get_version_objects(releases)
    compatibles = []
    first_operator, first_major, first_minor, first_patch = pragma[0]
    first_version = Version(f"{first_major}.{first_minor}.{first_patch}")
    if first_operator == "":
        return str(first_version)
    if pragma[1] is None:
        if first_operator == "^":
            compatibles = [str(x) for x in versions if x ^ (first_version)]
        if first_operator == ">=":
            compatibles = [str(x) for x in versions if x >= (first_version)]
        if first_operator == "<=":
            compatibles = [str(x) for x in versions if x <= (first_version)]
        if first_operator == ">":
            compatibles = [str(x) for x in versions if x > (first_version)]
        if first_operator == "<":
            compatibles = [str(x) for x in versions if x < (first_version)]
    else:
        second_operator, second_major, second_minor, second_patch = pragma[1]
        second_version = Version(f"{second_major}.{second_minor}.{second_patch}")
        if first_operator == ">=" and second_operator == "<=":
            compatibles = [
                str(x) for x in versions if first_version <= x <= (second_version)
            ]
        if first_operator == ">" and second_operator == "<=":
            compatibles = [
                str(x) for x in versions if first_version < x <= (second_version)
            ]
        if first_operator == ">=" and second_operator == "<":
            compatibles = [
                str(x) for x in versions if first_version <= x < (second_version)
            ]
        if first_operator == ">" and second_operator == "<":
            compatibles = [
                str(x) for x in versions if first_version < x < (second_version)
            ]
    return compatibles


def get_recommended_version(pragma: PRAGMA_TYPE) -> str:
    """
    Get the recommended version based on the given pragma.

    Parameters
    ----------
    pragma : PRAGMA_TYPE
        The pragma to use for determining the recommended version.

    Returns
    -------
    str
        A string representing the recommended version.

    Raises
    ------
    Exception
        If no compatible version is found.

    Notes
    -----
    The supported operators are "", "^", ">", ">=", "<=", and "<". The format
    for the version string is "major.minor.patch".

    If the operator is "", "^", ">=", or "<=", the recommended version will be
    the same as the given version.

    If the operator is ">", the recommended version will be the smallest
    version greater than the given version, or the minimum version of the
    next minor release if no such version exists.

    If the operator is "<", the recommended version will be the largest
    version smaller than the given version, or the maximum version of the
    previous minor release if no such version exists.

    """
    if pragma is None:
        return None
    releases, latest = get_available_versions()
    version_dict = _get_version_dict(releases)
    first_operator, first_major, first_minor, first_patch = pragma[0]
    if first_operator in {"^", ">=", "<=", ""}:
        return f"{first_major}.{first_minor}.{first_patch}"
    if first_operator == ">":
        if Version(f"{first_major}.{first_minor}.{first_patch}") >= Version(latest):
            raise NoCompatibleVersionError("latest", latest)
        patches = {p for p in version_dict[first_major][first_minor]}
        if first_patch >= max(patches):
            patch = min(version_dict[first_major + 1], default=0)
            return f"{first_major}.{first_minor +1}.{patch}"
        else:
            return f"{first_major}.{first_minor}.{first_patch + 1}"
    if first_operator == "<":
        earliest = Version(get_earliest_release())
        if Version(f"{first_major}.{first_minor}.{first_patch}") <= earliest:
            NoCompatibleVersionError("earliest", earliest)
        patches = {p for p in version_dict[first_major][first_minor]}
        if first_patch <= min(patches):
            patch = max(version_dict[first_major][first_minor - 1], default=0)
            return f"{first_major}.{first_minor - 1}.{patch}"
        else:
            return f"{first_major}.{first_minor}.{first_patch - 1}"
    return None


def install_solc_from_solidity(
    source: Union[str, Path],
    version_resolver: Callable[[PRAGMA_TYPE], str] = None,
    verbose: bool = True,
) -> str:
    """
    Install the solc version specified in the given source code.

    Parameters
    ----------
    - source : str | Path
        - The source code or file path to parse for the solc version.
    - version_resolver : Callable[[PRAGMA_TYPE], str], optional
        - A function that takes a PRAGMA_TYPE and returns a recommended version, by default None
        If not provided, `get_recommended_version` is used as default resolver.
    - verbose : bool, optional
        - Whether to print the installation progress, by default True

    Returns
    -------
    str
        The version extracted by version resolver solc version.

    Raises
    ------
    ValueError
        If the solc version cannot be resolved from the source code.

    Notes
    -----
    This function will install the recommended version of solc as determined by
    the Solidity version pragma in the given source code. The supported operators
    are "", "^", ">", ">=", "<=", and "<". The format for the version string is
    "major.minor.patch".

    - If the operator is "", "^", ">=", or "<=", the recommended version will be
    the same as the given version.

    - If the operator is ">", the recommended version will be the smallest version
    greater than the given version, or the minimum version of the next minor
    release if no such version exists.

    - If the operator is "<", the recommended version will be the largest version
    smaller than the given version, or the maximum version of the previous minor
    release if no such version exists.
    """
    version = resolve_version_from_solidity(source)
    if version_resolver is None:
        version_resolver = get_recommended_version
    recommended_version = version_resolver(version)
    installed = get_installed_versions()
    if recommended_version not in installed:
        install_solc(recommended_version, verbose=verbose)
    return recommended_version
