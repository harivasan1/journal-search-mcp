#!/usr/bin/env python3
"""Entrypoint that ensures `/data` is writable by the runtime user and then
drops privileges to the `appuser` before exec'ing the given command.

This allows the image to perform necessary chown/chmod operations at container
start time (when volumes are mounted) and still run the main application as a
non-root user.
"""
import os
import pwd
import sys


def drop_privileges_and_exec(cmd):
    try:
        pw = pwd.getpwnam("appuser")
        uid = pw.pw_uid
        gid = pw.pw_gid
    except KeyError:
        # appuser not found; just exec the command
        os.execvp(cmd[0], cmd)

    # If running as root, fix /data ownership and drop privileges
    try:
        if os.geteuid() == 0:
            try:
                os.chown("/data", uid, gid)
                os.chmod("/data", 0o750)
            except Exception:
                # best-effort; continue even if chown/chmod fails
                pass
            # drop to appuser
            os.setgid(gid)
            os.setuid(uid)
    except AttributeError:
        # Some minimal platforms may not have geteuid; ignore
        pass

    os.execvp(cmd[0], cmd)


def main():
    # Expect '--' separator then the command, otherwise default to uvicorn
    if "--" in sys.argv:
        idx = sys.argv.index("--")
        cmd = sys.argv[idx + 1 :]
    else:
        cmd = [
            "uvicorn",
            "fastapi_app:app",
            "--host",
            "0.0.0.0",
            "--port",
            os.environ.get("PORT", "8000"),
        ]

    if not cmd:
        cmd = [
            "uvicorn",
            "fastapi_app:app",
            "--host",
            "0.0.0.0",
            "--port",
            os.environ.get("PORT", "8000"),
        ]

    drop_privileges_and_exec(cmd)


if __name__ == "__main__":
    main()
