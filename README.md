# Solcix

[![Version](https://img.shields.io/pypi/v/solcix?color=brightgreen)](https://pypi.org/project/solcix?style=flat) [![Release](https://img.shields.io/github/v/release/Solratic/solcix?display_name=tag&include_prereleases?color=brightgreen)](https://github.com/Solratic/solcix)  [![Code Style](https://img.shields.io/badge/code%20style-black-black)](https://github.com/psf/black) [![Python Versions](https://img.shields.io/pypi/pyversions/solcix?style=flat)](https://pypi.org/project/solcix/) [![Activity](https://img.shields.io/github/commit-activity/w/Solratic/solcix?color=orange)](https://github.com/Solratic/solcix)

Solcix is a Solidity version manager written in Python that allows for seamless switching between versions, easy compilation, and simple management of artifacts.

## Installation

To install Solcix, you can use pip, the Python package manager:

### With pip For Windows

```bash
pip install solcix
```

### With pip3 For Linux / Mac

```bash
pip3 install solcix
```

### With pipx

[pipx](https://github.com/pypa/pipx) installs packages in their own virtual environment, so there's less chance of conflicting dependencies. You can run the following command in your terminal to install:

```bash
pipx install solcix
```

### With poetry

Uses the [poetry](https://github.com/python-poetry/poetry) package manager to install solcix in a project-specific virtual environment. poetry manages dependencies for you and allows you to isolate your project from the global environment. You can run the following command in your terminal to add solcix to your poetry project, and use our wrapped solc api in your code:

```bash
poetry add solcix
```

### With pipenv

Uses the [pipenv](https://pipenv.pypa.io/en/latest/) package manager to install solcix in a project-specific virtual environment. pipenv also manages dependencies and isolates your project from the global environment, and use our wrapped solc api in your code. You can run the following command in your terminal to install:

```bash
pipenv install solcix
```

## Enable Auto-Completion

Enable auto-completion for `solcix` by running the following command:

### With Bash

```bash
_SOLCIX_COMPLETE=bash_source solcix > ~/.solcix-complete.bash
source ~/.solcix-complete.bash
```

### With Zsh

```zsh
_SOLCIX_COMPLETE=zsh_source solcix > ~/.solcix-complete.zsh
source ~/.solcix-complete.zsh
```

### With Fish

```fish
_SOLCIX_COMPLETE=fish_source solcix > ~/.config/fish/completions/solcix.fish
```

## Usage - CLI

Solcix can be used as a library or as a command line tool. Here are the available commands:

### Listing available Solidity compilers

The `ls` command can be used to list all available versions of the Solidity compiler:

Example usage:

```bash
solcix ls
```

### Installing Solidity compilers

The `install` command can be used to install one or more versions of the Solidity compiler:

Example usage:

```bash
solcix install 0.8.4 0.7.6
```

### Listing installed Solidity compilers

The `installed` command can be used to list all available versions of the Solidity compiler:

Example usage:

```bash
solcix installed
```

If global / local version is set, it will be displayed as below:

```bash
0.8.19
0.5.2
0.5.1
0.5.0
0.8.0 <- current
0.8.0
0.8.16
```

### Switching between Solidity compilers

The `use` command can be used to switch between installed versions of the Solidity compiler, either globally or locally.

- If the specified version is not installed, it will be installed automatically.

- If you use the `local` option, it will create a `.solcix` file in the current directory.

Example usage:

```bash
# Setting global version to 0.8.16
solcix use global 0.8.16
```

```bash
# Setting local version to 0.8.16, it will create a .solcix file in the current directory
solcix use local 0.8.16
```

Simply run the command will see the changes:

```bash
solc --version
```

### Show current Solidity compiler version

The `current` command can be used to show the current version of the Solidity compiler (local version takes precedence over global version):

Example usage:

```bash
solcix current
```

### Uninstalling Solidity compilers

The `uninstall` command can be used to uninstall one or more versions of the Solidity compiler:

```bash
solcix uninstall 0.8.4 0.7.6
```

### Uninstall all Solidity compilers

To uninstall all versions of Solidity compiler that have been installed using solcix, you can use the following command:

```bash
solcix prune
```

This will remove all versions of the Solidity compilers that have been installed by solcix, all cached files, and the solcix configuration file (local config takes precedence over global config).

### Verify Solidity compilers

The `verify` command is used to verify the checksums of installed solc binaries and to reinstall any that are malformed.

Example usage:

```bash
solcix verify 0.8.0 0.8.1
```

### Clear cache of Solidity compilers

The `clear` command is used to remove all cached files. The cache is used to store the downloaded file list. The binary will not be deleted.

Example usage:

```bash
solcix clear
```

### Compile Solidity files

The `compile` command is used to compile Solidity files and print the result. If the output is a TTY, the result will be formatted. Otherwise, the result will be printed as a JSON string.

Example usage:

```bash
solcix compile <file.sol>
```

The command also supports the `-o` or `--output` option to specify an output directory for the compilation result.

Example usage:

```bash
solcix compile <filename>.sol -o <output_dir>
```

Additional optional arguments can be passed to the command using the kwargs argument, it will be taken by the [solc command](https://docs.soliditylang.org/en/v0.8.19/using-the-compiler.html#basic-usage).

Example usage:

```bash
solcix compile <file.sol> --optimize=True --optimize-runs=200 --overwrite=True
```

Or you can redirect the output to a single json file:

```bash
solcix compile <file.sol> > output.json
```

### Resolve compatible versions from solidity file

The `resolve` command is used to determine the recommended solc version for a Solidity file based on its pragma statement. It can also be used to list all versions that are compatible with the Solidity file.

Example usage:

```bash
solcix resolve <file.sol>
```

By default, the command prints the recommended solc version for the Solidity file.

Solidity Example:

```solidity
// SPDX-License-Identifier: MIT
// compiler version must be `0.8.5`, `0.8.6` or `0.8.7`
pragma solidity >=0.8.5 <=0.8.7;
contract HelloWorld {
    string public greet = "Hello World!";
}
```

Example output:

```bash
The recommended version is 0.8.5, use `solcix resolve --no-recommand` to see all compatible versions.
```

If the `--no-recommand` option is used, the command will print all compatible versions for the Solidity file.

Example output:

```bash
These versions are compatible with the pragma.
0.8.5
0.8.6
0.8.7
```

### Upgrade Solcix

The `upgrade` command is used to upgrade the architecture of the installed solc binaries, it will remove all old binaries and download the new ones.

Example usage:

```bash
pip3 install -U

# Migrate to the new architecture and Reinstall all binaries
solcix upgrade
```

### Project Acknowledgements

We would like to thank the original projects [solc-select](https://github.com/crytic/solc-select) and [py-solc-x](https://github.com/ApeWorX/py-solc-x) for providing excellent code base, upon which we have optimized and improved to make the project more robust and user-friendly.

Our project is an improved and optimized version of solc-select and py-solc-x, with more features and excellent performance.

If you enjoyed the original projects, we strongly recommend trying out our project to enjoy a better user experience and more efficient code execution.
