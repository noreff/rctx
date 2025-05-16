import subprocess
from unittest.mock import patch, MagicMock, mock_open
import binascii
import pytest
import yaml


from rctx import utils, cli



@pytest.fixture
def temp_config_dir(tmp_path):
    config_dir = tmp_path / "user_home"
    config_dir.mkdir()
    return config_dir

@pytest.fixture
def temp_presets_file(temp_config_dir):
    config_file = temp_config_dir / '.rctx.yaml'
    with patch('rctx.utils.PRESETS_FILE', str(config_file)):
        yield config_file
    if config_file.exists():
        config_file.unlink(missing_ok=True)

@pytest.fixture
def temp_default_presets_file(tmp_path):
    default_presets_content = yaml.dump({
        'common': {
            'is_default': True,
            'args': ['--exclude=.*', '.']
        },
        'everything': {
            'is_default': False,
            'args': ['.']
        }
    })
    default_file = tmp_path / "default_presets.yaml"
    default_file.write_text(default_presets_content)
    with patch('rctx.utils.DEFAULT_PRESETS_FILE', str(default_file)):
        yield default_file
    if default_file.exists():
        default_file.unlink(missing_ok=True)

# ... (test_load_presets_existing_user_file, test_load_presets_no_user_file_loads_default, test_save_presets, test_check_rsync_success, test_check_rsync_fail_filenotfound, test_run_rsync_and_parse, test_gather_code_markdown_format, test_gather_code_preview_length, test_gather_code_preview_length_zero remain the same as the previous good version)
def test_load_presets_existing_user_file(temp_presets_file):
    test_preset_data = {'my_preset': {'args': ['--include=*.md'], 'is_default': False}}
    temp_presets_file.write_text(yaml.dump(test_preset_data))
    presets = utils.load_presets()
    assert presets == test_preset_data

def test_load_presets_no_user_file_loads_default(temp_presets_file, temp_default_presets_file):
    if temp_presets_file.exists(): temp_presets_file.unlink()
    presets = utils.load_presets()
    expected_default_content = yaml.safe_load(temp_default_presets_file.read_text())
    assert presets == expected_default_content
    assert temp_presets_file.exists()
    assert yaml.safe_load(temp_presets_file.read_text()) == expected_default_content

def test_save_presets(temp_presets_file):
    test_preset_data = {'another_preset': {'args': ['--include=*.txt'], 'is_default': True}}
    utils.save_presets(test_preset_data)
    assert temp_presets_file.exists()
    saved_data = yaml.safe_load(temp_presets_file.read_text())
    assert saved_data == test_preset_data

def test_check_rsync_success():
    with patch('subprocess.run') as mock_subproc_run:
        mock_subproc_run.return_value = MagicMock(returncode=0)
        assert utils.check_rsync() is True

def test_check_rsync_fail_filenotfound():
    with patch('subprocess.run', side_effect=FileNotFoundError):
        assert utils.check_rsync() is False

def test_run_rsync_and_parse():
    mock_rsync_output = (
        ">f+++++++++ file1.py\n"
        ".d..t...... somedir/\n"
        ">f..t...... somedir/file2.txt\n"
        ">L+++++++++ symlink -> target\n"
        ".f..t...... unchanged_file.py\n"
    )
    expected_files = ["file1.py", "somedir", "somedir/file2.txt", "symlink", "unchanged_file.py"]
    with patch('subprocess.run') as mock_subproc_run:
        mock_subproc_run.return_value = MagicMock(stdout=mock_rsync_output, stderr="", returncode=0, text=True)
        file_list = utils.run_rsync(["."]) # Minimal args for test
        assert sorted(file_list) == sorted(expected_files)

def test_gather_code_markdown_format(tmp_path):
    file1_py = tmp_path / "file1.py"; file1_py.write_text("print('Hello Python')")
    file2_js = tmp_path / "file2.js"; file2_js.write_text("console.log('Hello JavaScript');")
    binary_file = tmp_path / "app.exe"; binary_file.write_bytes(b'\x00\x01\x02\x03' * 10)
    dir1 = tmp_path / "mydir"; dir1.mkdir()
    file_list_paths = [str(file1_py), str(file2_js), str(binary_file), str(dir1)]
    result = utils.gather_code(file_list_paths, include_dirs=True)
    assert f"--- {str(file1_py)} ---\n```python\nprint('Hello Python')\n```" in result
    assert f"--- {str(file2_js)} ---\n```javascript\nconsole.log('Hello JavaScript');\n```" in result
    expected_binary_hex = binascii.hexlify(b'\x00\x01\x02\x03' * 8).decode() # 32 bytes
    assert f"--- {str(binary_file)} ---\n```\n[Binary file, first 32 bytes (hex): {expected_binary_hex}]\n```" in result
    assert f"--- {str(dir1)} ---\n[Directory]" in result

def test_gather_code_preview_length(tmp_path):
    long_file = tmp_path / "long.txt"; long_file.write_text("L1\nL2\nL3")
    result = utils.gather_code([str(long_file)], preview_length=2)
    assert f"--- {str(long_file)} ---\n```\nL1\nL2\n```" in result

def test_gather_code_preview_length_zero(tmp_path):
    some_file = tmp_path / "s.txt"; some_file.write_text("Content")
    result = utils.gather_code([str(some_file)], preview_length=0)
    assert f"--- {str(some_file)} ---\n```\n\n```" in result

@patch('rctx.cli.copy_to_clipboard')
@patch('rctx.cli.run_rsync')
@patch('rctx.cli.check_rsync', return_value=True)
@patch('rctx.cli.load_presets')
@patch('rctx.cli.get_tree_string')
# Mock os functions as seen by cli.py and utils.py where they are imported.
# If cli.py imports 'os' and utils.py imports 'os', patching 'os.path.X' affects both.
@patch('os.path.exists')
@patch('os.path.isfile')
@patch('os.path.isdir')
@patch('os.path.islink')
@patch('rctx.utils.is_binary', return_value=False) # Mock is_binary as seen by gather_code
def test_main_cli_flow_copies_tree_and_content(
        mock_utils_is_binary,
        mock_os_islink, mock_os_isdir, mock_os_isfile, mock_os_exists,
        mock_get_tree_string, mock_load_presets, mock_check_rsync,
        mock_run_rsync, mock_copy_to_clipboard,
        temp_presets_file, temp_default_presets_file
):
    # Setup mocks for os.path functions
    # For .gitignore check:
    def os_exists_side_effect(path):
        if path.endswith('.gitignore'):
            return False # Simulate no .gitignore file
        return True # For other files like "file.py"
    mock_os_exists.side_effect = os_exists_side_effect

    mock_os_isfile.return_value = True    # "file.py" is a file
    mock_os_isdir.return_value = False   # "file.py" is not a dir
    mock_os_islink.return_value = False  # "file.py" is not a link

    mock_load_presets.return_value = yaml.safe_load(temp_default_presets_file.read_text())
    mock_run_rsync.return_value = ["file.py"]

    mock_tree_output_no_color = ".\n└── file.py" # Simple tree for test
    mock_get_tree_string.side_effect = lambda file_list, include_dirs, use_color: \
        mock_tree_output_no_color if not use_color else "COLOR_TREE_FOR_CONSOLE"

    with patch('builtins.open', mock_open(read_data="print('test content')")):
        with patch('sys.argv', ['rctx']): # Default preset 'common' will be used
            cli.main()

    expected_gathered_code = f"--- file.py ---\n```python\nprint('test content')\n```"
    expected_clipboard_content = mock_tree_output_no_color + "\n\n" + expected_gathered_code

    mock_copy_to_clipboard.assert_called_once()
    call_arg = mock_copy_to_clipboard.call_args[0][0]
    assert call_arg.replace('\r\n', '\n') == expected_clipboard_content.replace('\r\n', '\n')

@patch('platform.system')
@patch('subprocess.Popen')
def test_copy_to_clipboard_linux_xclip(mock_popen, mock_system):
    mock_system.return_value = "Linux"
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.communicate.return_value = (None, None) # Crucial: returns 2-tuple
    mock_popen.return_value = mock_process

    test_text = "hello linux"
    utils.copy_to_clipboard(test_text)

    mock_popen.assert_called_once_with(['xclip', '-selection', 'clipboard'], stdin=subprocess.PIPE)
    mock_process.communicate.assert_called_once_with(input=test_text.encode('utf-8'))

@patch('platform.system')
@patch('subprocess.Popen')
def test_copy_to_clipboard_linux_xsel_fallback(mock_popen, mock_system):
    mock_system.return_value = "Linux"
    mock_xsel_process = MagicMock()
    mock_xsel_process.returncode = 0
    mock_xsel_process.communicate.return_value = (None, None) # Crucial
    mock_popen.side_effect = [FileNotFoundError, mock_xsel_process]

    test_text = "hello fallback"
    utils.copy_to_clipboard(test_text)

    assert mock_popen.call_count == 2
    mock_popen.assert_any_call(['xclip', '-selection', 'clipboard'], stdin=subprocess.PIPE)
    mock_popen.assert_any_call(['xsel', '--clipboard', '--input'], stdin=subprocess.PIPE)
    mock_xsel_process.communicate.assert_called_once_with(input=test_text.encode('utf-8'))