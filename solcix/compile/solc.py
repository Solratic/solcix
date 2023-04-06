import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from solcix.errors import (
    ContractNotFoundError,
    InvalidOptionError,
    NoSolcVersionInstalledError,
    SolcError,
    UnrecognizedOptionError,
)
from solcix.installer import get_executable


def solc_execute(
    solc_path: Union[str, Path] = None,
    stdin: Optional[str] = None,
    source_files: Union[List[Union[str, Path]], str, Path, None] = None,
    import_remappings: Optional[Union[Dict[str, str], List[str], str]] = None,
    **kwargs: Any,
) -> Tuple[str, str, List[str], subprocess.Popen]:
    """
    This is an `low level function` which execute the solc binary with given arguments and return stdout, stderr, command and Popen object.

    Parameters
    ----------
        - solc_path: Optional path to solc binary.
            - default to local or global `solc` if not provided.
        - stdin: Optional string to pass as standard input to the solc process.
        - source_files: Optional list of source files to compile.
        - import_remappings: Optional import remappings as either dict, list or string.
        - **kwargs: Optional solc options and values.

    Returns
    -------
        A tuple containing the following:
        - stdout: The captured standard output from the solc process.
        - stderr: The captured standard error from the solc process.
        - command: The complete command passed to subprocess.Popen.
        - proc: The Popen object for the solc process.

    Raises
    ------
        - NoSolcInstalledError: If solc_path is provided but does not exist.
        - UnrecognizedOptionError: If an unrecognized option is provided.
        - InvalidOptionError: If an invalid option is provided.
        - SolcError: If solc exits with a non-zero status code.
    """
    if solc_path is not None:
        solc_path = Path(solc_path)
        if not solc_path.exists():
            raise NoSolcVersionInstalledError(version=solc_path.name)
    else:
        solc_path = get_executable()

    command: List[str] = [str(solc_path)]

    if source_files is not None:
        if isinstance(source_files, (str, Path)):
            command.append(str(source_files))
        else:
            command.extend([str(s) for s in source_files])

    if import_remappings is not None:
        if isinstance(import_remappings, str):
            command.append(import_remappings)
        else:
            if isinstance(import_remappings, dict):
                import_remappings = [f"{k}={v}" for k, v in import_remappings.items()]
            command.extend(import_remappings)

    for k, v in kwargs.items():
        if v is None or v is False:
            continue
        key = f"--{k.replace('_', '-')}"
        if isinstance(v, bool):
            command.append(key)
        else:
            command.extend([key, str(v)])

    if "standard_json" not in kwargs and not source_files:
        # Implies solc should read from stdin
        command.append("-")

    if stdin is not None:
        stdin = str(stdin)

    proc = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
    )

    stdout, stderr = proc.communicate(stdin)

    if proc.returncode != 0:
        if stderr.startswith("unrecognised option"):
            flag = stderr.split("'")[1]
            raise UnrecognizedOptionError(flag)
        elif stderr.startswith("Invalid option"):
            flag, option = stderr.split(": ")
            flag = flag.split(" ")[-1]
            raise InvalidOptionError(flag, option)
        raise SolcError(
            command=command,
            return_code=proc.returncode,
            stdin_data=stdin,
            stdout_data=stdout,
            stderr_data=stderr,
        )
    return stdout, stderr, command, proc


def compile_source(
    source: str,
    solc_path: Optional[Union[str, Path]] = None,
    solc_version: Optional[str] = None,
    import_remappings: Optional[Union[Dict[str, str], List[str], str]] = None,
    base_path: Optional[Union[str, Path]] = None,
    allow_paths: Optional[Union[List[Union[str, Path]], str, Path]] = None,
    output_values: Optional[List[str]] = None,
    output_dir: Optional[Union[str, Path]] = None,
    overwrite: bool = False,
    evm_version: Optional[str] = None,
    revert_strings: Optional[Union[List[str], str]] = None,
    metadata_hash: Optional[str] = None,
    metadata_literal: bool = False,
    optimize: bool = False,
    optimize_runs: Optional[int] = None,
    optimize_yul: bool = False,
    yul_optimizations: Optional[int] = None,
):
    """
    Compile Solidity source code into EVM bytecode.

    Parameters:
    -----------
    - source : str
        - The Solidity source code to be compiled.
    - solc_path : Optional[Union[str, Path]]
        - The path to the Solidity compiler executable.
    - solc_version : Optional[str]
        - The version of the Solidity compiler to use.
    - import_remappings : Optional[Union[Dict[str, str], List[str], str]]
        - Remap import paths. This can be a string, a list of strings, or a dictionary.
    - base_path : Optional[Union[str, Path]]
        - The base path to use when resolving relative file paths.
    - allow_paths : Optional[Union[List[Union[str, Path]], str, Path]]
        - Additional paths to allow when resolving file paths.
    - output_values : Optional[List[str]]
        - A list of output types to include in the output JSON.
    - output_dir : Optional[Union[str, Path]]
        - The output directory to save the compiled contract artifacts.
    - overwrite : bool
        - Whether to overwrite existing output files.
    - evm_version : Optional[str]
        - The EVM version to compile the contract for.
    - revert_strings : Optional[Union[List[str], str]]
        - A list of revert strings to include in the contract metadata.
    - metadata_hash : Optional[str]
        - A string to include in the contract metadata.
    - metadata_literal : bool
        - Whether to use the metadata string as a literal or as a path to a file.
    - optimize : bool
        - Whether to enable bytecode optimization.
    - optimize_runs : Optional[int]
        - The number of optimization runs to perform.
    - optimize_yul : bool
        - Whether to optimize Yul code.
    - yul_optimizations : Optional[int]
        - The level of Yul optimizations to perform.

    Returns:
    --------
    A dictionary containing the compiled contract artifacts.
    """
    return _compile_combined_json(
        solc_path=solc_path,
        solc_version=solc_version,
        stdin=source,
        output_values=output_values,
        import_remappings=import_remappings,
        base_path=base_path,
        allow_paths=allow_paths,
        output_dir=output_dir,
        overwrite=overwrite,
        evm_version=evm_version,
        revert_strings=revert_strings,
        metadata_hash=metadata_hash,
        metadata_literal=metadata_literal,
        optimize=optimize,
        optimize_runs=optimize_runs,
        optimize_yul=optimize_yul,
        yul_optimizations=yul_optimizations,
    )


def compile_files(
    source_files: Union[List[Union[str, Path]], str, Path],
    solc_path: Optional[Union[str, Path]] = None,
    solc_version: Optional[str] = None,
    import_remappings: Optional[Union[Dict[str, str], List[str], str]] = None,
    base_path: Optional[Union[str, Path]] = None,
    allow_paths: Optional[Union[List[Union[str, Path]], str, Path]] = None,
    output_values: Optional[List[str]] = None,
    output_dir: Optional[Union[str, Path]] = None,
    overwrite: bool = False,
    evm_version: Optional[str] = None,
    revert_strings: Optional[Union[List[str], str]] = None,
    metadata_hash: Optional[str] = None,
    metadata_literal: bool = False,
    optimize: bool = False,
    optimize_runs: Optional[int] = None,
    optimize_yul: bool = False,
    yul_optimizations: Optional[int] = None,
):
    """
        Compile Solidity source code files into EVM bytecode.

    Parameters:
    -----------
    - source_files : Union[List[Union[str, Path]], str, Path]
        - The list of Solidity source code files to be compiled.
    - solc_path : Optional[Union[str, Path]]
        - The path to the Solidity compiler executable.
    - solc_version : Optional[str]
        - The version of the Solidity compiler to use.
    - import_remappings : Optional[Union[Dict[str, str], List[str], str]]
        - Remap import paths. This can be a string, a list of strings, or a dictionary.
    - base_path : Optional[Union[str, Path]]
        - The base path to use when resolving relative file paths.
    - allow_paths : Optional[Union[List[Union[str, Path]], str, Path]]
        - Additional paths to allow when resolving file paths.
    - output_values : Optional[List[str]]
        - A list of output types to include in the output JSON.
    - output_dir : Optional[Union[str, Path]]
        - The output directory to save the compiled contract artifacts.
    - overwrite : bool
        - Whether to overwrite existing output files.
    - evm_version : Optional[str]
        - The EVM version to compile the contract for.
    - revert_strings : Optional[Union[List[str], str]]
        - A list of revert strings to include in the contract metadata.
    - metadata_hash : Optional[str]
        - A string to include in the contract metadata.
    - metadata_literal : bool
        - Whether to use the metadata string as a literal or as a path to a file.
    - optimize : bool
        - Whether to enable bytecode optimization.
    - optimize_runs : Optional[int]
        - The number of optimization runs to perform.
    - optimize_yul : bool
        - Whether to optimize Yul code.
    - no_optimize_yul : bool
        - Whether to disable Yul optimization.
    - yul_optimizations : Optional[int]
        - The level of Yul optimizations to perform.

    Returns:
    --------
    A dictionary containing the compiled contract artifacts.

    """
    return _compile_combined_json(
        solc_path=solc_path,
        solc_version=solc_version,
        source_files=source_files,
        output_values=output_values,
        import_remappings=import_remappings,
        base_path=base_path,
        allow_paths=allow_paths,
        output_dir=output_dir,
        overwrite=overwrite,
        evm_version=evm_version,
        revert_strings=revert_strings,
        metadata_hash=metadata_hash,
        metadata_literal=metadata_literal,
        optimize=optimize,
        optimize_runs=optimize_runs,
        optimize_yul=optimize_yul,
        yul_optimizations=yul_optimizations,
    )


def compile_standard(
    input_data: Dict[str, Any],
    solc_path: Optional[Union[str, Path]] = None,
    solc_version: Optional[str] = None,
    base_path: Optional[str] = None,
    allow_paths: Optional[Union[List[Union[str, Path]], str, Path]] = None,
    output_dir: Optional[Union[str, Path]] = None,
    overwrite: bool = False,
) -> Dict[str, Any]:
    """
    Compile Solidity contracts from standard JSON input.

    Parameters:
    - input_data (Dict[str, Any]): The standard JSON input containing the Solidity contract(s) to compile.
    - solc_path (Optional[Union[str, Path]]): The path to the solc binary to use. If not specified, the latest version of solc available on the system will be used.
    - solc_version (Optional[str]): The specific version of solc to use. If specified, `solc_path` will be ignored.
    - base_path (Optional[str]): Base path to use for resolving relative import statements.
    - allow_paths (Optional[Union[List[Union[str, Path]], str, Path]]): Paths to search for the referenced files.
    - output_dir (Optional[Union[str, Path]]): The directory to output the compiled contracts to.
    - overwrite (bool): Whether or not to overwrite existing output files.

    Returns:
    - Dict[str, Any]: The compiled contracts and related data as returned by solc.

    Raises:
    - ContractNotFoundError: If no Solidity source files are found in the input data.
    - SolcError: If there is an error encountered while compiling the contracts. This includes both compilation errors and other errors, such as invalid input data.

    Note:
    - This function is intended to compile Solidity contracts using standard JSON input format. For other input formats, see `compile_files` or `compile_source`.

    """
    if not input_data.get("sources"):
        raise ContractNotFoundError(input_data)

    if solc_path is None:
        solc_path = get_executable(solc_version)

    stdout, stderr, command, proc = solc_execute(
        solc_path=solc_path,
        stdin=json.dumps(input_data),
        standard_json=True,
        base_path=base_path,
        allow_paths=allow_paths,
        output_dir=output_dir,
        overwrite=overwrite,
    )

    compiler_output = json.loads(stdout)
    if "errors" in compiler_output:
        has_errors = any(
            error["severity"] == "error" for error in compiler_output["errors"]
        )
        if has_errors:
            error_message = "\n".join(
                tuple(
                    error["formattedMessage"]
                    for error in compiler_output["errors"]
                    if error["severity"] == "error"
                )
            )
            raise SolcError(
                error_message,
                command=command,
                return_code=proc.returncode,
                stdin_data=json.dumps(input_data),
                stdout_data=stdout,
                stderr_data=stderr,
                error_dict=compiler_output["errors"],
            )
    return compiler_output


def _get_combined_json_outputs(solc_path: Union[Path, str] = None) -> str:
    """
    Get the combined JSON output options for a given `solc_path`.

    Parameters
    -----------
    solc_path : Union[Path, str], optional
        The path to the solc executable. If not provided, it will try to locate the executable.

    Returns
    --------
    str
        The combined JSON output options for solc.

    Raises
    -------
    SolcNotFoundError
        If the `solc_path` is not provided and the executable is not found.

    Examples:
    ---------
    >>> _get_combined_json_outputs('/usr/local/bin/solc')
    'bin,abi,interface,metadata,ir,ast'

    """
    if solc_path is None:
        solc_path = get_executable()

    # help_str = solc_execute(solc_path=solc_path, help=True)[0].split("\n")

    # Execute solc with the `--help` flag to get the combined JSON output options.
    cmd = [str(solc_path), "--help"]
    output = subprocess.run(
        cmd,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    help_str = output.stdout.decode("utf-8").split("\n")

    combined_json_args = next(i for i in help_str if i.startswith("  --combined-json"))
    return combined_json_args.split(" ")[-1]


def _parse_compiler_output(stdout: str) -> Dict[str, Any]:
    """
    Parses the compiler output from JSON to a dictionary.

    Parameters
    ----------
    - stdout (str)
        - The standard output from the Solidity compiler.

    Returns
    -------
    - Dict[str, Any]
        - A dictionary of the compiled contracts and their details.

    """
    output = json.loads(stdout)

    contracts = output.get("contracts", {})
    sources = output.get("sources", {})

    for path_str, data in contracts.items():
        if "abi" in data and isinstance(data["abi"], str):
            data["abi"] = json.loads(data["abi"])
        key = path_str.rsplit(":", maxsplit=1)[0]
        if "AST" in sources.get(key, {}):
            data["ast"] = sources[key]["AST"]

    return contracts


def _compile_combined_json(
    output_values: Optional[List] = None,
    solc_path: Union[str, Path, None] = None,
    solc_version: Optional[str] = None,
    output_dir: Union[str, Path, None] = None,
    overwrite: Optional[bool] = False,
    allow_empty: Optional[bool] = False,
    **kwargs: Any,
) -> Dict[str, Dict[str, Any]]:
    """
    Compile Solidity source code into a combined JSON file.

    Parameters
    ----------
    - output_values (Optional[List])
        - A list of output values.
    - solc_path (Union[str, Path, None])
        - The path to the solc binary.
    - solc_version (Optional[str])
        - The solc version to use. If `None`, the global version `solc` will be used.
    - output_dir (Union[str, Path, None])
        - The directory to save the combined JSON file. If `None`, the file will not be saved.
    - overwrite (Optional[bool])
        - Whether to overwrite the existing output file with the same name. Default is `False`.
    - allow_empty (Optional[bool])
        - Whether to allow the function to return an empty dictionary when no contract is found in the source code. Default is `False`.
    - **kwargs
        - Additional keyword arguments to pass to the solc compiler.

    Returns
    -------
    - Dict[str, Any]
        - A dictionary containing the compiled contracts.

    Raises
    ------
    - FileExistsError: If `output_dir` is a file or the output file already exists and `overwrite` is `False`.
    - ContractNotFoundError: If the solc compiler fails to compile the source code or no contract is found in the source code.

    Notes
    -----
    - See the [Solidity documentation](https://docs.soliditylang.org/en/v0.8.14/using-the-compiler.html) for more information on how to use the solc compiler.
    """
    if solc_path is None:
        solc_path = get_executable(solc_version)

    if output_values is None:
        combined_json = _get_combined_json_outputs(solc_path)
    else:
        combined_json = ",".join(output_values)

    if output_dir:
        output_dir = Path(output_dir)
        if output_dir.is_file():
            raise FileExistsError("`output_dir` must be as a directory, not a file")
        if output_dir.joinpath("combined.json").exists() and not overwrite:
            target_path = output_dir.joinpath("combined.json")
            raise FileExistsError(
                f"Target output file {target_path} already exists - use overwrite=True to overwrite"
            )

    stdoutdata, stderrdata, command, proc = solc_execute(
        solc_path=solc_path,
        combined_json=combined_json,
        output_dir=output_dir,
        overwrite=overwrite,
        **kwargs,
    )

    if output_dir:
        output_path = Path(output_dir).joinpath("combined.json")
        if stdoutdata:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with output_path.open("w") as fp:
                fp.write(stdoutdata)
        else:
            with output_path.open() as fp:
                stdoutdata = fp.read()

    contracts = _parse_compiler_output(stdoutdata)

    if not contracts and not allow_empty:
        raise ContractNotFoundError(
            {
                "command": command,
                "return_code": proc.returncode,
                "stdout_data": stdoutdata,
                "stderr_data": stderrdata,
            }
        )
    return contracts
