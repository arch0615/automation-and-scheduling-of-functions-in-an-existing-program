"""
Store the Anthropic API key in this project's .env file.

Usage:
    python set_api_key.py
        (prompts for the key)

    python set_api_key.py sk-ant-api03-...
        (passes the key directly — convenient but appears in shell history)

The key is written to housoft-meta/.env and is loaded automatically by
python-dotenv when the PoC and main app run.
"""
import getpass
import sys
from pathlib import Path

ENV_PATH = Path(__file__).parent / ".env"
VAR_NAME = "ANTHROPIC_API_KEY"


def get_key_from_args_or_prompt() -> str:
    if len(sys.argv) > 1:
        return sys.argv[1].strip()
    print("Paste your Anthropic API key (input is hidden):")
    return getpass.getpass("> ").strip()


def upsert_env_var(name: str, value: str) -> str:
    """Add or update a single line in .env. Returns 'added' or 'updated'."""
    if not ENV_PATH.exists():
        ENV_PATH.write_text(f"{name}={value}\n", encoding="utf-8")
        return "added (new file)"

    lines = ENV_PATH.read_text(encoding="utf-8").splitlines()
    found = False
    new_lines = []
    for line in lines:
        if line.strip().startswith(f"{name}="):
            new_lines.append(f"{name}={value}")
            found = True
        else:
            new_lines.append(line)
    if not found:
        new_lines.append(f"{name}={value}")

    ENV_PATH.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    return "updated" if found else "added"


def main() -> int:
    key = get_key_from_args_or_prompt()

    if not key:
        print("ERROR: Empty key. Aborted.")
        return 1
    if not key.startswith("sk-ant-"):
        print(f"WARNING: Key doesn't start with 'sk-ant-' (got '{key[:8]}...').")
        print("Anthropic keys typically start with sk-ant-. Continue anyway? [y/N]")
        if input("> ").strip().lower() != "y":
            print("Aborted.")
            return 1

    action = upsert_env_var(VAR_NAME, key)
    masked = f"{key[:10]}...{key[-4:]}" if len(key) > 14 else "***"
    print(f"OK: {VAR_NAME} {action} in {ENV_PATH}")
    print(f"    Value: {masked}")
    print()
    print("Verify:")
    print('    python -c "from dotenv import load_dotenv; import os; '
          'load_dotenv(); print(\'set:\', bool(os.getenv(\'ANTHROPIC_API_KEY\')))"')
    return 0


if __name__ == "__main__":
    sys.exit(main())
