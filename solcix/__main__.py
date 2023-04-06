import os
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
from solcix.__version__ import __version__
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
@click.version_option(version=__version__, prog_name="solcix", message=f"{Fore.YELLOW}{pyfiglet.figlet_format('welcome to solcix')}{Style.RESET_ALL} {VERSION_INFO}")
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
def versions():
    releases, latest = solcix.get_available_versions()
    for release, artifact in releases.items():
        print(f"release: {release:6s} | artifact: {artifact}")
    print(Fore.GREEN + f"latest: {latest}" + Style.RESET_ALL)


@cli.command(help="List all installed solc versions.")
def installed():
    installed = solcix.get_installed_versions()
    try:
        current, _ = solcix.manage.current_version()
        for version in installed:
            if current == version:
                print(Fore.GREEN + f"{version} <- current" + Style.RESET_ALL)
            print(version)
    except NotInstalledError as e:
        print(Fore.YELLOW + f"{e}" + Style.RESET_ALL)
        for version in sorted(installed, key=Version):
            print(version)


@cli.command(help="Switch between solc versions. If the version is not installed, it will be installed.")
@click.argument("scope", nargs=1, required=True, type=click.Choice(["global", "local"]))
@click.argument("version", nargs=1, required=True, type=click.STRING)
def use(scope: str, version: str):
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


@cli.command(
    help="Verify checksums of installed solc binaries, and reinstall malformed ones."
)
@click.argument("version", nargs=-1, required=True, type=click.STRING)
def verify(version: Union[List[str], str]):
    solcix.verify_solc(version)


@cli.command(help="Remove all cached files.")
def clear():
    solcix.clear_cache()


@cli.command(context_settings=dict(ignore_unknown_options=True), help="Compile Solidity files and print the result, if the output is a TTY, the result will be formatted. Otherwise the result will be printed as a JSON string.")
@click.argument("file", nargs=1, required=True, type=click.Path(exists=True))
@click.option("-o", "--output", default=None, type=click.Path(), help="Output directory, will be create if not exists.")
@click.argument("kwargs", nargs=-1, type=click.UNPROCESSED)
def compile(file: str, output: str, **kwargs):
    if output is not None:
        os.makedirs(output, exist_ok=True)
        kwargs["output_dir"] = output
    compile_result = solcix.compile.compile_files(file, **kwargs)
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
            print(Fore.CYAN + "* Print to a single json file by", Fore.YELLOW + "`solcix compile <FILE> <filename>.json`" + Style.RESET_ALL, "to view whole result.")
        else:
            print(json.dumps(compile_result, indent=4, sort_keys=True))


@cli.command()
@click.argument("file", nargs=1, required=True, type=click.Path(exists=True, dir_okay=False, readable=True))
@click.option("--recommand/--no-recommand", default=True, is_flag=True)
def resolve(file: str, recommand: bool):
    pragma = solcix.resolve_version_from_solidity(file)
    if recommand:
        version = solcix.get_recommended_version(pragma)
        print(f"The recommended version is {version}, use `solcix resolve --no-recommand` to see all compatible versions.")
    else:
        versions = solcix.get_compatible_versions(pragma)
        print("These versions are compatible with the pragma.")
        for version in versions:
            print(version)


def solc() -> None:
    try:
        current = solcix.manage.current_version()
        version, _ = current
        path = ARTIFACT_DIR.joinpath(f"solc-{version}", f"solc-{version}")
        subprocess.run([str(path), *sys.argv[1:]], check=True)
    except NotInstalledError as e:
        print(Fore.RED + str(e) + Style.RESET_ALL)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)
