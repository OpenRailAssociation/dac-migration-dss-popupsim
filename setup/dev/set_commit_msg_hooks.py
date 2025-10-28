#!/usr/bin/env python3
"""Setup script for installing Git commit message validation hooks.

This script creates platform-specific Git hooks that validate commit messages
against the Conventional Commits format to ensure consistent commit history.
"""
import platform
import stat
import sys
from pathlib import Path


def create_validation_script() -> str:
    """Create a separate Python validation script for commit message validation.

    Returns
    -------
    str
        Path to the created validation script.
    """
    # Add shebang only for Unix-like systems
    shebang = "#!/usr/bin/env python3\n" if platform.system() != "Windows" else ""

    # Define commit types
    commit_types = "feat|fix|docs|style|refactor|perf|test|chore|ci|build|revert"

    script_content = f"""{shebang}import sys
import re

def validate_commit_message(commit_msg_file):
    with open(commit_msg_file, "r") as f:
        commit_msg = f.read().strip()

    if commit_msg.startswith("Merge"):
        return True

    pattern = r"^({commit_types})(\\(.+\\))?!?: .{{1,}}"

    if not re.match(pattern, commit_msg):
        print("\\nERROR: Commit message does not follow Conventional Commits format!\\n")
        print("Format: <type>[optional scope]: <description>\\n")
        print("Types: feat, fix, docs, style, refactor, perf, test, chore, ci, build, revert\\n")
        print("Examples:")
        print("  feat: add user login")
        print("  fix(auth): handle expired tokens")
        print("  docs: update API documentation\\n")
        return False

    return True

if __name__ == "__main__":
    if not validate_commit_message(sys.argv[1]):
        sys.exit(1)
"""

    script_path = Path('.git') / 'hooks' / 'validate_commit_msg.py'
    script_path.write_text(script_content, encoding='utf-8')
    return str(script_path)


def get_commit_msg_hook(script_path: str) -> str:
    """Generate platform-specific commit message hook content.

    Parameters
    ----------
    script_path : str
        Path to the validation script.

    Returns
    -------
    str
        Hook content appropriate for the current platform.
    """
    python_exe = sys.executable

    if platform.system() == 'Windows':
        return f'@echo off\n"{python_exe}" "{script_path}" %1\n'
    return f'#!/bin/bash\n"{python_exe}" "{script_path}" "$1"\n'


def setup_commit_msg_hook() -> bool:
    """Install Git commit message validation hook for the current platform.

    Returns
    -------
    bool
        True if installation succeeded, False otherwise.
    """
    hooks_dir = Path('.git') / 'hooks'

    if not hooks_dir.exists():
        print('ERROR: Not a git repository')
        return False

    # Create validation script
    script_path = create_validation_script()

    # Create hook file
    hook_name = 'commit-msg.bat' if platform.system() == 'Windows' else 'commit-msg'
    hook_path = hooks_dir / hook_name

    commit_msg_hook = get_commit_msg_hook(script_path)
    hook_path.write_text(commit_msg_hook, encoding='utf-8')

    # Make executable (Unix/Linux/macOS only)
    if platform.system() != 'Windows':
        st = hook_path.stat()
        hook_path.chmod(st.st_mode | stat.S_IEXEC)

    print('SUCCESS: Commit message hook installed successfully!')
    return True


if __name__ == '__main__':
    setup_commit_msg_hook()
