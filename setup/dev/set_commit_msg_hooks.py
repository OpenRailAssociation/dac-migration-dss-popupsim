#!/usr/bin/env python3
import os
import stat

COMMIT_MSG_HOOK = """#!/usr/bin/env python3
import sys
import re

def validate_commit_message(commit_msg_file):
    with open(commit_msg_file, 'r') as f:
        commit_msg = f.read().strip()

    # Skip merge commits
    if commit_msg.startswith('Merge'):
        return True

    pattern = r'^(feat|fix|docs|style|refactor|perf|test|chore|ci|build|revert)(\(.+\))?!?: .{1,}'

    if not re.match(pattern, commit_msg):
        print("\\n❌ Commit message does not follow Conventional Commits format!\\n")
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


def setup_commit_msg_hook():
    hooks_dir = ".git/hooks"
    hook_path = os.path.join(hooks_dir, "commit-msg")

    if not os.path.exists(hooks_dir):
        print("❌ Not a git repository")
        return False

    with open(hook_path, "w") as f:
        f.write(COMMIT_MSG_HOOK)

    # Make executable
    st = os.stat(hook_path)
    os.chmod(hook_path, st.st_mode | stat.S_IEXEC)

    print("✅ Commit message hook installed successfully!")
    return True


if __name__ == "__main__":
    setup_commit_msg_hook()
