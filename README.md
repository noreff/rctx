# Rctx: Rsync-Powered Code Stringification (Fork of Rstring)

[![PyPI version](https://badge.fury.io/py/rctx.svg)](https://badge.fury.io/py/rctx) <!-- Placeholder, update once published -->
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Rctx is a developer tool that uses [Rsync](https://linux.die.net/man/1/rsync) to efficiently gather and stringify code from your projects. It's designed to streamline the process of preparing code context for AI programming assistants, making it easy to get intelligent insights about your codebase. This is a fork of the original `rstring` project.

When you run `rctx`, it copies the selected file contents to your clipboard, prepended with a tree view of the matched files. The output is formatted using Markdown code blocks for easy pasting into LLMs or documents.

<div align="center">
  <!-- You might want to update the demo image -->
  <img alt="Rctx demo" src="https://github.com/user-attachments/assets/c85106e3-2b02-42ff-b585-4234a58e8b9a" width="600">
  <p><i>Quickly prompt an LLM with your whole project!</i></p>
</div>

## Installation

Rctx requires Python 3.8+. We recommend using `pipx` for installation, as it installs Rctx in an isolated environment, preventing conflicts with other packages.

### Using pipx (recommended)

1. Install pipx if you haven't already. Follow the [official pipx installation guide](https://pipx.pypa.io/stable/installation/) for your operating system.

2. Install Rctx:
   ```bash
   pipx install rctx
   ```

### Using pip

If you prefer to use pip, you can install Rctx with:

```bash
pip install rctx
```

### Updating Rctx

To update Rctx to the latest version:

With pipx:
```bash
pipx upgrade rctx
```

With pip:
```bash
pip install --upgrade rctx
```

For more detailed information about pipx and its usage, refer to the [pipx documentation](https://pipx.pypa.io/stable/).

## Quick Start

Basic usage (copies tree + content to clipboard):
```bash
rctx  # Use the default preset
```

Specify includes/excludes (copies tree + content to clipboard):
```bash
rctx --include=*/ --include=*.py --exclude=* # traverse all dirs, include .py files, exclude everything else
```

Get help:
```bash
rctx --help
```

Use a specific preset:
```bash
rctx --preset my_preset
```

Get a summary view (includes detailed summary, tree, and content, copied to clipboard):
```bash
rctx --summary
```

## Advanced Usage

### Custom Presets

Create a new preset:
```bash
rctx --save-preset python --include=*/ --include=*.py --exclude=*  # save it
rctx --preset python  # use it
```

### File Preview

Limit output to first N lines of each file:
```bash
rctx --preview-length=10
```

### Gitignore Integration

By default, Rctx automatically excludes .gitignore patterns. To ignore .gitignore:
```bash
rctx --no-gitignore
```

### Interactive mode:

Enter interactive mode to continuously preview and select matched files:
```bash
rctx -i
```

## Understanding Rctx

1. **Under the Hood**: Rctx efficiently selects files based on filters by running `rsync --archive --itemize-changes --dry-run --list-only <your filters>`. This means you can use Rsync's powerful include/exclude patterns to customize file selection.

2. **Preset System**: The default configuration file is at `~/.rctx.yaml`. The 'common' preset is used by default and includes sensible exclusions for most projects.

3. **Output Format (copied to clipboard)**:
   A tree view of the selected files is prepended, followed by:
   ```
   --- path/to/file1.py ---
   ```python
   [File contents]
   ```

   --- path/to/file2.js ---
   ```javascript
   [File contents]
   ```
   ```

4. **Binary Files**: Content of binary files is represented as a hexdump preview within a plain code block.

5. **Clipboard Integration**: Output (tree + content) is automatically copied to clipboard unless disabled with `--no-clipboard`. A colored tree is printed to the console.

6. **Git Integration**: By default, Rctx respects .gitignore patterns. Use `--no-gitignore` to ignore them.

## Pro Tips

1. **Explore the default preset**: Check `~/.rctx.yaml` to see how the 'common' preset works.

2. **Refer to Rsync documentation**: Rctx uses Rsync for file selection. Refer to the [Filter Rules](https://linux.die.net/man/1/rsync) section of the rsync man page to understand how include/exclude patterns work.

3. **Customize for your project**: Create a project-specific preset for quick context gathering.

4. **Use with AI tools**: Rctx is great for preparing code context for AI programming assistants, thanks to its Markdown output.

5. **Large projects may produce substantial output**: Use `--preview-length` or specific patterns for better manageability.

## Development

If you'd like to contribute to Rctx or set it up for local development, follow these steps:

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/rctx.git # Update with your fork's URL
   cd rctx
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

4. Install the package in editable mode:
   ```bash
   pip install -e .
   ```
   This will make the `rctx` command available in your environment, linked to your local source code.

5. Run the tests:
   ```bash
   pytest
   ```

### Running Rctx Locally (after `pip install -e .`)

Once installed in editable mode, you can run `rctx` directly:
```bash
rctx --help
rctx --include=*.md
```

Alternatively, without editable install, or to be explicit:
1. Make sure you're in the project root directory and your virtual environment is activated.
2. Run Rctx using the Python interpreter:
   ```bash
   python -m rctx [options]
   ```
   For example:
   ```bash
   python -m rctx --include=*/ --include=*.py --exclude=*
   ```

### Contributing

We welcome contributions to Rctx! Here are some guidelines:

1. Fork the repository and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. Ensure the test suite passes.
4. Make sure your code lints.
5. Issue a pull request!

For more details on contributing, please see our [CONTRIBUTING.md](CONTRIBUTING.md) file (if one exists, or create one).

## Support and Contributing

- Issues and feature requests: [GitHub Issues](https://github.com/noreff/rctx/issues) <!-- Update URL -->
- Contributions: Pull requests are welcome!

## License

Rctx is released under the MIT License. See the [LICENSE](LICENSE) file for details.