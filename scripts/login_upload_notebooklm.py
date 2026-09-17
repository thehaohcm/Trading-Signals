#!/usr/bin/env python3
"""Login to NotebookLM and upload its authentication state to the server."""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV_FILE = PROJECT_ROOT / "osint_ai_worker" / ".env"


def load_env_file(path: Path) -> None:
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ.setdefault(key.strip(), value)


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    print("Running:", " ".join(command))
    return subprocess.run(command, check=False, text=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Login NotebookLM and upload storage_state.json to the production server."
    )
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    parser.add_argument("--account")
    parser.add_argument("--server")
    parser.add_argument("--user")
    parser.add_argument("--port")
    parser.add_argument("--storage", type=Path)
    parser.add_argument("--remote-path")
    parser.add_argument(
        "--skip-login",
        action="store_true",
        help="Upload the existing local storage file without logging in again.",
    )
    args = parser.parse_args()
    load_env_file(args.env_file)

    account = args.account or os.getenv("NOTEBOOKLM_ACCOUNT")
    server = args.server or os.getenv("DEPLOY_HOST")
    user = args.user or os.getenv("DEPLOY_USER")
    port = args.port or os.getenv("DEPLOY_PORT", "22")
    storage = args.storage or Path(
        os.getenv(
            "NOTEBOOKLM_LOCAL_STORAGE",
            str(Path.home() / ".notebooklm" / "profiles" / "default" / "storage_state.json"),
        )
    )
    remote_path = args.remote_path or os.getenv("NOTEBOOKLM_REMOTE_STORAGE")
    missing_config = [
        name
        for name, value in (
            ("NOTEBOOKLM_ACCOUNT", account),
            ("DEPLOY_HOST", server),
            ("DEPLOY_USER", user),
            ("NOTEBOOKLM_REMOTE_STORAGE", remote_path),
        )
        if not value
    ]
    if missing_config:
        print(f"Missing configuration in {args.env_file}: {', '.join(missing_config)}", file=sys.stderr)
        return 1

    notebooklm = shutil.which("notebooklm")
    scp = shutil.which("scp")
    ssh = shutil.which("ssh")
    missing = [name for name, path in (("notebooklm", notebooklm), ("scp", scp), ("ssh", ssh)) if not path]
    if missing:
        print(f"Missing required command(s): {', '.join(missing)}", file=sys.stderr)
        return 1

    if not args.skip_login:
        result = run_command([notebooklm, "login", "--master-token", "--account", account])
        if result.returncode != 0:
            print("NotebookLM login failed; upload was not attempted.", file=sys.stderr)
            return result.returncode

    if not storage.is_file():
        print(f"Authentication file was not found: {storage}", file=sys.stderr)
        return 1

    target = f"{user}@{server}:{remote_path}"
    result = run_command(
        [
            scp,
            "-P",
            str(port),
            "-o",
            "StrictHostKeyChecking=accept-new",
            str(storage),
            target,
        ]
    )
    if result.returncode != 0:
        print("Upload failed.", file=sys.stderr)
        return result.returncode

    local_hash = sha256(storage)
    remote_hash_result = subprocess.run(
        [
            ssh,
            "-p",
            str(port),
            "-o",
            "StrictHostKeyChecking=accept-new",
            f"{user}@{server}",
            "sha256sum",
            remote_path,
        ],
        stdout=subprocess.PIPE,
        text=True,
        check=False,
    )
    if remote_hash_result.returncode != 0:
        print("Upload completed, but remote checksum verification failed.", file=sys.stderr)
        return remote_hash_result.returncode

    remote_hash = remote_hash_result.stdout.split()[0] if remote_hash_result.stdout.split() else ""
    if local_hash.lower() != remote_hash.lower():
        print("Checksum mismatch: the remote file may be incomplete.", file=sys.stderr)
        return 1

    print(f"Upload verified: {remote_path}")
    print(f"SHA-256: {local_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())