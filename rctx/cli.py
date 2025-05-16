import argparse
import logging
import os

from .utils import (
    load_presets, save_presets, check_rsync, run_rsync, validate_rsync_args,
    gather_code, interactive_mode, get_tree_string, copy_to_clipboard,
    get_default_preset, set_default_preset, parse_gitignore
)

logging.basicConfig(level=logging.INFO) # Consider level=logging.WARNING for less verbose default
logger = logging.getLogger(__name__)


def main():
    if not check_rsync():
        print("Error: rsync is not installed on this system. Please install rsync and try again.")
        return

    parser = argparse.ArgumentParser(description="Stringify code with rsync and manage presets.", allow_abbrev=False)
    # ... (arguments are the same) ...
    parser.add_argument("-p", "--preset", help="Use a saved preset")
    parser.add_argument("-sp", "--save-preset", type=str, metavar="NAME", help="Save the command as a preset")
    parser.add_argument("-lp", "--list-presets", action="store_true", help="List all saved presets")
    parser.add_argument("-dp", "--delete-preset", help="Delete a saved preset")
    parser.add_argument("-sdp", "--set-default-preset", help="Set the default preset")
    parser.add_argument("-i", "--interactive", action="store_true", help="Enter interactive mode")
    parser.add_argument("-nc", "--no-clipboard", action="store_true", help="Don't copy output to clipboard")
    parser.add_argument("-pl", "--preview-length", type=int, metavar="N",
                        help="Show only the first N lines of each file")
    parser.add_argument("-s", "--summary", action="store_true", help="Print a summary including a tree of files, copied to clipboard")
    parser.add_argument("-id", "--include-dirs", action="store_true",
                        help="Include empty directories in output and summary")
    parser.add_argument("-ng", "--no-gitignore", action="store_false", dest="use_gitignore",
                        help="Don't use .gitignore patterns")


    args, unknown_args = parser.parse_known_args()
    presets = load_presets()

    # ... (list, delete, set-default preset logic remains the same) ...
    if args.list_presets:
        print("Saved presets:")
        for name, preset in presets.items():
            print(f"  {'*' if preset.get('is_default', False) else ' '} {name}: {' '.join(preset['args'])}")
        return

    if args.delete_preset:
        if args.delete_preset in presets:
            del presets[args.delete_preset]
            save_presets(presets)
            print(f"Preset '{args.delete_preset}' deleted.")
        else:
            print(f"Preset '{args.delete_preset}' not found.")
        return

    if args.set_default_preset:
        set_default_preset(presets, args.set_default_preset)
        return

    preset_name = args.preset or get_default_preset(presets) if not unknown_args else None
    rsync_args_from_preset_or_custom = []
    if preset_name:
        preset_obj = presets.get(preset_name)
        if preset_obj:
            rsync_args_from_preset_or_custom = preset_obj['args'][:] # Use a copy
        else:
            print(f"Error: Preset '{preset_name}' not found.")
            return

    rsync_args_from_preset_or_custom.extend(unknown_args)

    # This will be the final rsync_args after all modifications
    rsync_args = rsync_args_from_preset_or_custom[:]

    if args.save_preset:
        name = args.save_preset
        # Save the args *before* .gitignore modifications if --save-preset is used with them.
        # Or, decide if saved presets should reflect current .gitignore. Current behavior saves effective args.
        presets[name] = {'is_default': False, 'args': rsync_args_from_preset_or_custom} # Save args before gitignore
        save_presets(presets)
        print(f"Preset '{name}' saved.")
        return

    was_modified_by_gitignore = False
    applied_gitignore_patterns = []

    if args.use_gitignore:
        gitignore_path = os.path.join(os.getcwd(), '.gitignore')
        if os.path.exists(gitignore_path):
            gitignore_patterns = parse_gitignore(gitignore_path)
            if gitignore_patterns: # Only modify if there are actual patterns
                rsync_args = gitignore_patterns + rsync_args # Prepend gitignore patterns
                was_modified_by_gitignore = True
                applied_gitignore_patterns = gitignore_patterns
        else:
            # Only print warning if not using --no-gitignore explicitly and no .gitignore found
            if args.use_gitignore is not False: # Check if it's the default True or explicitly set to True
                print("Warning: No .gitignore file found. Use --no-gitignore to suppress this warning or create a .gitignore file.")

    # Ensure a source/destination is present (e.g., '.')
    # Check if any non-option argument (potential path) exists or if '.' is already there.
    has_path_arg = any(not arg.startswith('--') for arg in rsync_args)
    if not has_path_arg:
        rsync_args.append('.')

    if not validate_rsync_args(rsync_args):
        print("Error: Invalid rsync arguments. Please check and try again.")
        return

    if args.interactive:
        rsync_args = interactive_mode(rsync_args, args.include_dirs)

    file_list = run_rsync(rsync_args)
    base_content = gather_code(file_list, args.preview_length, args.include_dirs)

    tree_for_clipboard = get_tree_string(file_list, include_dirs=args.include_dirs, use_color=False)
    # num_files should count actual files found and processed by rsync
    num_files = len([f for f in file_list if os.path.exists(f) and (os.path.isfile(f) or os.path.islink(f))])


    final_result_for_clipboard = ""
    if args.summary:
        from datetime import datetime
        summary_header = [
            "### COLLECTION SUMMARY ###", "",
            "The following files have been collected using the Rctx command.",
            "Binary files are truncated to the first 32 bytes (hex).", "",
            f"Files: {num_files}",
            f"Lines in content: {len(base_content.splitlines()) if base_content else 0}",
            f"Collected at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ""
        ]
        if tree_for_clipboard:
            summary_header.append(tree_for_clipboard)
        summary_header.extend(["", "### FILE CONTENTS ###"])

        final_result_for_clipboard = "\n".join(summary_header)
        if base_content: # Add base_content only if it exists
            final_result_for_clipboard += "\n" + base_content
    else:
        if tree_for_clipboard:
            final_result_for_clipboard = tree_for_clipboard
            if base_content:
                final_result_for_clipboard += "\n\n" + base_content
        else:
            final_result_for_clipboard = base_content

    if final_result_for_clipboard:
        if final_result_for_clipboard.endswith("\n\n"):
            final_result_for_clipboard = final_result_for_clipboard[:-2]
        elif final_result_for_clipboard.endswith("\n"):
            final_result_for_clipboard = final_result_for_clipboard[:-1]

    if args.no_clipboard:
        print()
        colored_tree_for_console = get_tree_string(file_list, include_dirs=args.include_dirs, use_color=True)
        if colored_tree_for_console:
            print(colored_tree_for_console)
            if base_content or args.summary : print() # Add newline if content follows
        print(final_result_for_clipboard)
    else:
        colored_tree_for_console = get_tree_string(file_list, include_dirs=args.include_dirs, use_color=True)
        if colored_tree_for_console:
            print(colored_tree_for_console)
        copy_to_clipboard(final_result_for_clipboard)

    lines_in_final_output = len(final_result_for_clipboard.splitlines())
    action_message_verb = "Collected" if args.no_clipboard else "Copied"

    message_parts = [f"{action_message_verb} {lines_in_final_output} lines from {num_files} files"]
    if not args.no_clipboard:
        message_parts.append("to clipboard")

    current_effective_rsync_args_str = ' '.join(rsync_args)

    if preset_name:
        message_parts.append(f"using preset '{preset_name}'")
        # Check if the effective rsync args differ from the original preset args + unknown_args
        # (this primarily means checking if gitignore modified them)
        original_args_for_preset_context = presets.get(preset_name, {}).get('args', [])[:]
        original_args_for_preset_context.extend(unknown_args) # Add command-line args not part of preset definition

        # Reconstruct what rsync_args would be if only preset + unknown_args were used
        # This is rsync_args_from_preset_or_custom

        if was_modified_by_gitignore:
            message_parts.append("(modified by .gitignore)")
        # Further check if there were other modifications beyond gitignore (e.g. interactive mode)
        # For simplicity, if was_modified_by_gitignore is false, and preset args + unknown != current_effective, it's "with modified options"
        elif ' '.join(rsync_args_from_preset_or_custom) != current_effective_rsync_args_str:
            # Show the part of rsync_args that doesn't come from preset or gitignore (if gitignore was involved)
            # This gets complex; a simpler message might be better.
            # For now, if it's different and not by gitignore, just show the effective args.
            if not was_modified_by_gitignore : # if not modified by gitignore, but still different
                # This means interactive mode or some other direct manipulation changed it from preset + unknown
                custom_options_display = ' '.join(unknown_args) if unknown_args else current_effective_rsync_args_str
                message_parts.append(f"with rsync options: '{custom_options_display}'")


    else: # No preset used
        message_parts.append("using custom rsync options:")
        if was_modified_by_gitignore:
            # Show the custom args that were there *before* gitignore, and then note gitignore modification
            non_gitignore_part = ' '.join(rsync_args_from_preset_or_custom) # these were the initial custom args
            message_parts.append(f"'{non_gitignore_part}' (modified by .gitignore)")
        else:
            message_parts.append(f"'{current_effective_rsync_args_str}'")

    print(' '.join(message_parts))

if __name__ == '__main__':
    main()