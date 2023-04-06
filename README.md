# Solcix

Solcix is a Solidity compiler manager for Python. You can switch between versions, compile, and manage artifacts easily.

## Installation

To install Solcix, you can use pip, the Python package manager:

### For Windows

```bash
pip install solcix
```

### For Linux / Mac

```bash
pip3 install solcix
```

## Usage - CLI

Solcix can be used as a library or as a command line tool. Here are the available commands:

### Installing Solidity compilers

The `install` command can be used to install one or more versions of the Solidity compiler:

Example usage:

```bash
solcix install 0.8.4 0.7.6
```

### Listing available Solidity compilers

The `versions` command can be used to list all available versions of the Solidity compiler:

Example usage:

```bash
solcix versions
```

### Listing installed Solidity compilers

The `versions` command can be used to list all available versions of the Solidity compiler:

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

### Uninstalling Solidity compilers

The `uninstall` command can be used to uninstall one or more versions of the Solidity compiler:

```bash
solcix uninstall 0.8.4 0.7.6
```

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
solcix compile <file.sol> --optimize
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
