import os
import ast
import sys
import json
import textwrap
from typing import List, Union
import pyfiglet
import subprocess

import click
from colorama import Fore, Style

import solcix.installer
import solcix.resolver
from solcix.datatypes import Version
from solcix.errors import NotInstalledError
from .constant import ARTIFACT_DIR

CONTEXT_SETTINGS = dict(
    help_option_names=["-h", "--help"],
)

WELCOME_MESSAGE = (
    f"{Fore.YELLOW}{pyfiglet.figlet_format('welcome to solcix')}{Style.RESET_ALL}"
)
VERSION_INFO = f"version  |  %(version)s \n"

# fmt: off
@click.group(context_settings=CONTEXT_SETTINGS, invoke_without_command=True, no_args_is_help=True,)
@click.version_option(package_name="solcix", message=f"{Fore.YELLOW}{pyfiglet.figlet_format('welcome to solcix')}{Style.RESET_ALL} {VERSION_INFO}")
def cli():
    pass


@cli.command(help="Install solc binaries.")
@click.argument("version", nargs=-1, required=True, type=click.STRING)
@click.option("--use-cache/--no-use-cache", default=True, is_flag=True)
def install(version: Union[List[str], str], use_cache: bool):
    success, skipped, error = solcix.installer.install_solc(version, use_cache)
    print(Fore.GREEN + f"success: {', '.join(success)}" + Style.RESET_ALL)
    print(Fore.YELLOW + f"skipped: {', '.join(skipped)}" + Style.RESET_ALL)
    print(Fore.RED + f"error  : {', '.join(error)}" + Style.RESET_ALL)


@cli.command(help="List available solc versions.")
def ls():
    releases, latest = solcix.get_available_versions()
    for release, artifact in releases.items():
        print(f"release: {release:6s} | artifact: {artifact}")
    print(Fore.GREEN + f"latest: {latest}" + Style.RESET_ALL)


@cli.command(help="List all installed solc versions.")
def installed():
    installed = solcix.get_installed_versions()
    installed = sorted(installed, key=Version)
    if len(installed) == 0:
        print(Fore.YELLOW + "No solc binary is installed. Please use `solcix install` or `solc use` to install solc." + Style.RESET_ALL)
        return
    try:
        current, _ = solcix.current_version()
        for version in installed:
            if current == version:
                print(Fore.GREEN + f"{version} <- current" + Style.RESET_ALL)
            else:
                print(version)
    except NotInstalledError as e:
        print(Fore.YELLOW + f"{e}" + Style.RESET_ALL)
        for version in installed:
            print(version)

@cli.command(help="Show current solc version.")
def current():
    try:
        current, _ = solcix.current_version()
        print(f"{Fore.GREEN}solc-{current}{Style.RESET_ALL} is currently used.")
    except NotInstalledError as e:
        print(Fore.YELLOW + f"{e}" + Style.RESET_ALL)


@cli.command(help="Switch between solc versions. If the version is not installed, it will be installed.")
@click.argument("scope", nargs=1, required=True, type=click.Choice(["global", "local"]))
@click.argument("version", nargs=1, required=True, type=click.STRING)
def use(scope: str, version: str):
    if version == "latest":
        _, version = solcix.get_available_versions()
    if scope == "global":
        solcix.manage.switch_global_version(version, True)
    elif scope == "local":
        solcix.manage.switch_local_version(version, True)


@cli.command(help="Uninstall solc binaries.")
@click.argument("version", nargs=-1, required=True, type=click.STRING)
def uninstall(version: Union[List[str], str]):
    success, skipped, error = solcix.uninstall_solc(version)
    print(Fore.GREEN + f"success: {', '.join(success)}" + Style.RESET_ALL)
    print(Fore.YELLOW + f"skipped: {', '.join(skipped)}" + Style.RESET_ALL)
    print(Fore.RED + f"error  : {', '.join(error)}" + Style.RESET_ALL)

@cli.command(help="Uninstall all solc binaries.")
def prune():
    opt = click.confirm(default=False, text="Are you sure to uninstall all solc binaries, caches, and config files?")
    if opt is False:
        print(f"👀{Fore.YELLOW} You have canceled the operation. Indeed, a wise choice!{Style.RESET_ALL} 👀")
        return
    # Delete all cached versions
    solcix.clear_cache()
    # Delete all config files
    solcix.manage.clear_config()
    # Delete all installed versions
    versions = solcix.get_installed_versions()
    success, skipped, error = solcix.uninstall_solc(versions)
    print(Fore.GREEN + f"success: {', '.join(success)}" + Style.RESET_ALL)
    print(Fore.YELLOW + f"skipped: {', '.join(skipped)}" + Style.RESET_ALL)
    print(Fore.RED + f"error  : {', '.join(error)}" + Style.RESET_ALL)


@cli.command(help="Verify checksums of installed solc binaries, and reinstall malformed ones.")
@click.argument("version", nargs=-1, required=True, type=click.STRING)
def verify(version: Union[List[str], str]):
    solcix.verify_solc(version)

@cli.command(help="Remove all cached files.")
def clear():
    solcix.clear_cache()


@cli.command(context_settings=dict(ignore_unknown_options=True, allow_extra_args=True), help="Compile Solidity files and print the result, if the output is a TTY, the result will be formatted. Otherwise the result will be printed as a JSON string. If you want to show the help message of solc, please use `solc --help`.")
@click.argument("file", nargs=1, required=True, type=click.Path(exists=True))
@click.option("-o", "--output", default=None, type=click.Path(), help="Output directory, will be create if not exists.")
@click.pass_context
def compile(ctx: click.Context, file: str, output: str):
    # Parse arguments
    params = dict()
    for segment in ctx.args:
        if segment.startswith("--") and segment.find("=") != 1:
            key, value = segment.strip("--").split("=")
            params[key.replace("-","_")] = ast.literal_eval(value)

    # check output directory
    if output is not None:
        params["output_dir"] = output
        if os.path.exists(output) and "overwrite" not in params:
            click.confirm(f"Output path `{output}` already exists, do you want to overwrite it?", default=False, abort=True)
            params["overwrite"] = True

    # check solc version is installed
    try:
        version = solcix.install_solc_from_solidity(source=file)
        params["solc_version"] = version
        params["source_files"] = file
    except Exception as e:
        print(e)
        sys.exit(1)

    # compile
    compile_result = solcix.compile.compile_files(**params)
    if output is not None:
        print(f"Compilation result is saved in the output directory {output}.")
    else:
        if sys.stdout.isatty():
            width = 70
            wrapper = textwrap.TextWrapper(width=width, initial_indent="    ", subsequent_indent="    ")
            for contract, result in compile_result.items():
                print(Fore.GREEN +  f"Contract: {contract}" )
                for field, value in result.items():
                        print(Fore.BLUE + f"  {field}"+ Style.RESET_ALL)
                        shortend_str = textwrap.shorten(f"    {value}", width=width*5, placeholder="...")
                        padded_str = wrapper.fill(shortend_str)
                        print(padded_str)
            print(Fore.CYAN + "* Output to directory by", Fore.YELLOW + "`solcix compile <FILE> -o <output dir>`" + Style.RESET_ALL)
            print(Fore.CYAN + "* Print to a single json file by", Fore.YELLOW + "`solcix compile <FILE> <output file>.json`" + Style.RESET_ALL, "to view whole result.")
        else:
            print(json.dumps(compile_result, indent=4, sort_keys=True))


@cli.command(help="Resolve the version of solc from the pragma in the Solidity file, and print the recommended version. If you want to see all compatible versions, use `solcix resolve --no-recommand`.")
@click.argument("file", nargs=1, required=True, type=click.Path(exists=True, dir_okay=False, readable=True))
@click.option("--recommand/--no-recommand", default=True, is_flag=True)
def resolve(file: str, recommand: bool):
    pragma = solcix.resolve_version_from_solidity(file)
    if recommand:
        version = solcix.get_recommended_version(pragma)
        print(f"The recommended version is {Fore.YELLOW}{version}.{Style.RESET_ALL}\nUse {Fore.YELLOW}`solcix resolve --no-recommand`{Style.RESET_ALL} to see all compatible versions.")
    else:
        versions = solcix.get_compatible_versions(pragma)
        print("These versions are compatible with the pragma.")
        for version in versions:
            print(version)


@cli.command(help="Reinstall all solc binaries.")
def upgrade():
    solcix.manage.upgrade_architecture()


def solc() -> None:
    try:
        version, _  = solcix.current_version()
        path = ARTIFACT_DIR.joinpath(f"solc-{version}", f"solc-{version}")
        subprocess.run([str(path), *sys.argv[1:]], check=True)
    except NotInstalledError as e:
        print(Fore.RED + str(e) + Style.RESET_ALL)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)

if __name__ == "__main__":
    cli()
