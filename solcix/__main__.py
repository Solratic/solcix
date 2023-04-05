import click
from pprint import pprint
import solcix.installer
import solcix.resolver
from solcix.__version__ import __version__

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(version=__version__)
def cli():
    """Repo is a command line tool that showcases how to build complex
        command line interfaces with Click.
        This tool is supposed to look like a distributed version control
        system to show how something like this can be structured.
    )"""
    pass


@cli.command()
@click.argument("install", nargs=-1, required=True, type=str)
def install_handler(install: list[str]):
    solcix.installer.install_solc(install)


@cli.command()
@click.argument("version")
def list_handler():
    releases, latest = solcix.resolver.get_available_versions()
    pprint(releases)
    pprint(latest)


if __name__ == "__main__":
    install_handler()
    list_handler()
    cli()
