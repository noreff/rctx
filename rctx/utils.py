import binascii
import logging
import os
import platform
import shlex
import subprocess

import yaml

logger = logging.getLogger(__name__)

PRESETS_FILE = os.path.expanduser("~/.rctx.yaml")
DEFAULT_PRESETS_FILE = os.path.join(os.path.dirname(__file__), 'default_presets.yaml')

from .tree import get_tree_string

def get_language_from_extension(file_path):
    name, ext = os.path.splitext(file_path)
    ext = ext.lower()
    ext_map = {
        '.py': 'python', '.pyw': 'python',
        '.js': 'javascript', '.mjs': 'javascript', '.cjs': 'javascript',
        '.ts': 'typescript', '.mts': 'typescript', '.cts': 'typescript',
        '.java': 'java', '.jar': 'java',
        '.c': 'c', '.h': 'c',
        '.cpp': 'cpp', '.cxx': 'cpp', '.cc': 'cpp', '.hpp': 'cpp',
        '.cs': 'csharp',
        '.go': 'go',
        '.rb': 'ruby',
        '.php': 'php',
        '.swift': 'swift',
        '.kt': 'kotlin', '.kts': 'kotlin',
        '.rs': 'rust',
        '.html': 'html', '.htm': 'html',
        '.css': 'css',
        '.scss': 'scss', '.sass': 'sass',
        '.json': 'json', '.jsonc': 'json',
        '.yaml': 'yaml', '.yml': 'yaml',
        '.md': 'markdown', '.markdown': 'markdown', '.rst': 'rst', '.txt': '',
        '.sh': 'bash', '.bash': 'bash', '.zsh': 'zsh', '.fish': 'fish',
        '.xml': 'xml', '.xsl': 'xml', '.xslt': 'xml', '.xsd': 'xml',
        '.sql': 'sql',
        '.dockerfile': 'dockerfile',
        '.jsx': 'jsx',
        '.tsx': 'tsx',
        '.m': 'objectivec', '.mm': 'objectivec',
        '.pl': 'perl', '.pm': 'perl',
        '.lua': 'lua',
        '.r': 'r',
        '.scala': 'scala',
        '.hs': 'haskell', '.lhs': 'haskell',
        '.ini': 'ini',
        '.toml': 'toml',
        '.cfg': 'ini',
        '.conf': '',
        '.tex': 'latex',
        '.vbs': 'vbscript', '.vb': 'vbnet',
        '.ps1': 'powershell', '.psm1': 'powershell',
        '.dart': 'dart',
        '.ex': 'elixir', '.exs': 'elixir',
        '.erl': 'erlang',
        '.clj': 'clojure', '.cljs': 'clojure', '.cljc': 'clojure',
        '.groovy': 'groovy',
        '.gql': 'graphql', '.graphql': 'graphql',
        '.vue': 'vue',
        '.svelte': 'svelte',
        '.tf': 'terraform', '.tfvars': 'terraform',
        '.http': 'http',
        '.sum': 'gosum',
        '.mod': 'gomod',
    }
    base_name = os.path.basename(file_path).lower()
    if base_name == 'dockerfile': return 'dockerfile'
    if 'makefile' in base_name : return 'makefile'
    if base_name.startswith('gemfile'): return 'ruby'
    if base_name.startswith('procfile'): return ''
    if base_name.startswith('jenkinsfile'): return 'groovy'
    if base_name == 'requirements.txt': return ''
    if base_name == 'pipfile': return 'toml'

    return ext_map.get(ext, '')

def load_presets():
    if os.path.exists(PRESETS_FILE):
        try:
            with open(PRESETS_FILE, 'r') as f:
                loaded_yaml = yaml.safe_load(f)
                return loaded_yaml if loaded_yaml else {}
        except yaml.YAMLError as e:
            logger.warning(f"Error parsing {PRESETS_FILE}: {e}. Using empty presets.")
        except Exception as e:
            logger.error(f"Error reading {PRESETS_FILE}: {e}. Using empty presets.")
    else:
        try:
            with open(DEFAULT_PRESETS_FILE, 'r') as df:
                content = df.read()
            with open(PRESETS_FILE, 'w') as f:
                f.write(content)
            logger.info(f"Created default presets file at {PRESETS_FILE}")
            loaded_yaml = yaml.safe_load(content)
            return loaded_yaml if loaded_yaml else {}
        except Exception as e:
            logger.error(f"Error reading or writing preset files: {e}. Using empty presets.")
    return {}

def save_presets(presets):
    try:
        with open(PRESETS_FILE, 'w') as f:
            yaml.dump(presets, f)
    except Exception as e:
        logger.error(f"Error saving presets to {PRESETS_FILE}: {e}")

def get_default_preset(presets):
    for name, preset in presets.items():
        if preset.get('is_default', False):
            return name
    return None

def set_default_preset(presets, preset_name):
    if preset_name not in presets:
        print(f"Error: Preset '{preset_name}' not found")
        return
    for name, preset_data in presets.items():
        preset_data['is_default'] = (name == preset_name)
    save_presets(presets)
    print(f"Default preset set to '{preset_name}'")

def parse_gitignore(gitignore_path):
    if not os.path.exists(gitignore_path):
        return []
    patterns = ['--exclude=.git']
    try:
        with open(gitignore_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if line.startswith('/'): line = line[1:]
                    if line.endswith('/'):
                        patterns.append(f'--exclude={line}*')
                        patterns.append(f'--exclude={os.path.normpath(line)}')
                    else:
                        patterns.append(f'--exclude={line}')
                        patterns.append(f'--exclude={line}/*')
        return list(dict.fromkeys(patterns))
    except Exception as e:
        logger.warning(f"Could not parse .gitignore file at {gitignore_path}: {e}")
        return ['--exclude=.git']

def check_rsync():
    try:
        subprocess.run(["rsync", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

# vvvvvvvvvvv REVERT THIS SECTION vvvvvvvvvvv
def run_rsync(args):
    # Original rstring command structure
    cmd = ["rsync", "-ain", "--list-only"] + args

    # Keep the debug prints for now
    print(f"DEBUG: Executing rsync command: {' '.join(shlex.quote(s) for s in cmd)}")
    logger.debug(f"Rsync command: {' '.join(shlex.quote(s) for s in cmd)}")
    try:
        result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors='ignore')
        print(f"DEBUG: Rsync stdout:\n{result.stdout}")
        if result.stderr: print(f"DEBUG: Rsync stderr:\n{result.stderr}")

        return parse_rsync_output(result.stdout) # Use the original parser
    except subprocess.CalledProcessError as e:
        logger.error(f"Rsync command failed: {e}")
        if e.stdout: logger.error(f"Stdout: {e.stdout}")
        if e.stderr: logger.error(f"Stderr: {e.stderr}")
        raise
    except Exception as e:
        logger.error(f"Failed to run rsync: {e}")
        raise

def parse_rsync_output(output):
    # Original rstring parser
    file_list = []
    print(f"DEBUG ORIGINAL PARSER: Full rsync output to parse:\n{output}\n--------------------") # Add debug
    for line in output.splitlines():
        print(f"DEBUG ORIGINAL PARSER: Processing line: '{line}'") # Add debug
        parts = line.split() # Split by whitespace
        if len(parts) >= 5 and not line.strip().endswith('/'): # Check if line ITSELF ends with / after stripping
            # Ensure that the path part (from parts[4:]) is not just "."
            file_path_candidate = ' '.join(parts[4:])
            print(f"DEBUG ORIGINAL PARSER: Candidate path: '{file_path_candidate}', Parts: {parts}") # Add debug
            if file_path_candidate != '.':
                print(f"DEBUG ORIGINAL PARSER: Appending '{file_path_candidate}'") # Add debug
                file_list.append(file_path_candidate)
            else:
                print(f"DEBUG ORIGINAL PARSER: Skipping '.' path.") # Add debug
        else:
            print(f"DEBUG ORIGINAL PARSER: Skipping line (len<5 or ends with /): '{line.strip()}'") # Add debug
    print(f"DEBUG ORIGINAL PARSER: Final parsed_list: {file_list}") # Add debug
    return file_list
# ^^^^^^^^^^^ END REVERT SECTION ^^^^^^^^^^^

def validate_rsync_args(args):
    try:
        # The validation call should also use --list-only if the main one does.
        # And it's good to have a timeout here.
        run_rsync(args + ['--timeout=1'])
        return True
    except Exception:
        return False

def is_binary(file_path):
    try:
        with open(file_path, 'rb') as file:
            chunk = file.read(1024)
            return b'\0' in chunk
    except IOError: return False
    except Exception as e:
        logger.warning(f"Could not check if file is binary {file_path}: {e}")
        return False

def gather_code(file_list, preview_length=None, include_dirs=False):
    result_parts = []
    for file_path_original in file_list:
        full_path = os.path.normpath(file_path_original)
        header_path = file_path_original

        if os.path.isfile(full_path) or os.path.islink(full_path):
            try:
                lang = get_language_from_extension(full_path)
                if is_binary(full_path):
                    if preview_length is None or preview_length > 0:
                        with open(full_path, 'rb') as file_content:
                            hex_preview = binascii.hexlify(file_content.read(32)).decode()
                        file_data_formatted = f"[Binary file, first 32 bytes (hex): {hex_preview}]"
                        result_parts.append(f"--- {header_path} ---\n```{lang}\n{file_data_formatted}\n```")
                else:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as file_content:
                        lines = file_content.readlines()
                    file_data = "".join(lines[:preview_length]) if preview_length is not None else "".join(lines)
                    file_data = file_data.rstrip('\n')
                    if preview_length == 0:
                        result_parts.append(f"--- {header_path} ---\n```{lang}\n\n```")
                    else:
                        result_parts.append(f"--- {header_path} ---\n```{lang}\n{file_data}\n```")
            except Exception as e:
                logger.error(f"Error reading {header_path} (resolved to {full_path}): {e}")
                result_parts.append(f"--- {header_path} ---\n[Error reading file: {e}]")
        elif include_dirs and os.path.isdir(full_path): # This check is for items that rsync might list as dirs
            result_parts.append(f"--- {header_path} ---\n[Directory]")
        else: # If it's not a file/link and not (include_dirs and a dir), it might be a dir rsync listed but we don't want content for
            if os.path.isdir(full_path) and not include_dirs:
                logger.debug(f"Skipping directory {full_path} as include_dirs is False.")
            else:
                logger.warning(f"Item '{full_path}' from rsync list was not a file, link, or processable directory.")


    return "\n\n".join(result_parts) if result_parts else ""

# ... (interactive_mode and copy_to_clipboard remain the same as your last working version of these)
def interactive_mode(initial_args, include_dirs=False):
    args = initial_args[:]
    while True:
        try:
            file_list = run_rsync(args)
            print("\nCurrent file list:")
            tree_str = get_tree_string(file_list, include_dirs=include_dirs, use_color=True)
            print(tree_str if tree_str else "(No files matched by current arguments)")
        except Exception:
            print("Error: Could not generate file list with current rsync arguments.")
        print(f"\nCurrent rsync arguments: {' '.join(shlex.quote(s) for s in args)}")
        action = input("Action: (a)dd include | (x)clude pattern | (e)dit args | (d)one: ").lower()
        if action in ['done', 'd']: break
        elif action in ['add', 'a']:
            pattern = input("Enter --include pattern (e.g., '*.py'): ")
            if pattern: args.extend(['--include', pattern])
        elif action in ['x', 'exclude']:
            pattern = input("Enter --exclude pattern (e.g., '*.log'): ")
            if pattern: args.extend(['--exclude', pattern])
        elif action in ['edit', 'e']:
            args_str = input(f"Current args: {' '.join(shlex.quote(s) for s in args)}\nEnter new full rsync arguments: ")
            new_args_candidate = shlex.split(args_str)
            if not any(not arg.startswith('--') for arg in new_args_candidate):
                new_args_candidate.append('.')
            if validate_rsync_args(new_args_candidate):
                args = new_args_candidate
            else: print("Error: Invalid rsync arguments after edit. Reverting to previous.")
        else: print("Invalid action. Try 'a', 'x', 'e', or 'd'.")
    return args

def copy_to_clipboard(text):
    system = platform.system()
    process = None
    cmd = []
    try:
        if system == 'Darwin':
            cmd = ['pbcopy']
            process = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        elif system == 'Windows':
            cmd = ['clip']
            process = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        elif system == 'Linux':
            try:
                cmd = ['xclip', '-selection', 'clipboard']
                process = subprocess.Popen(cmd, stdin=subprocess.PIPE)
            except FileNotFoundError:
                cmd = ['xsel', '--clipboard', '--input']
                process = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        else:
            print(f"Clipboard not supported on {system}. Output not copied.")
            return

        stdout_bytes, stderr_bytes = process.communicate(input=text.encode('utf-8'))

        if process.returncode != 0:
            err_msg = f"Failed to copy to clipboard (command: {' '.join(cmd)}). Exit code: {process.returncode}."
            if stderr_bytes is not None and stderr_bytes.strip():
                err_msg += f" Stderr: {stderr_bytes.decode('utf-8', 'ignore').strip()}"
            print(err_msg)

    except FileNotFoundError:
        tool_name = cmd[0] if cmd else "clipboard utility"
        print(f"Failed to copy to clipboard: {tool_name} not found. Please install it.")
    except Exception as e:
        print(f"An unexpected error occurred while copying to clipboard: {e}")