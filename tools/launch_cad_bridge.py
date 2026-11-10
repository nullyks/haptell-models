"""Start a local CAD application when needed, then serve its MCP connection."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time


def listening(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.5):
            return True
    except OSError:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("application", choices=("freecad", "blender"))
    args = parser.parse_args()
    base = Path(os.environ["LOCALAPPDATA"]) / "Haptell"
    manifest = json.loads((base / "Reports/tools.json").read_text(encoding="utf-8"))
    name, port, server = {
        "freecad": ("FreeCAD", 9875, "freecad-mcp.exe"),
        "blender": ("Blender", 9876, "mcp-for-blender.exe"),
    }[args.application]
    executable = Path(manifest[name]["executable"])
    if not listening(port):
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = 0
        with (base / "Reports" / f"{args.application}.log").open("a", encoding="utf-8") as log:
            process = subprocess.Popen([str(executable)], cwd=executable.parent,
                stdout=log, stderr=log, stdin=subprocess.DEVNULL,
                startupinfo=startup, creationflags=subprocess.CREATE_NO_WINDOW)
        deadline = time.monotonic() + 60
        while not listening(port):
            # FreeCAD's portable launcher exits successfully after starting
            # bin/freecad.exe; the child may still be loading its workbenches.
            if process.poll() not in (None, 0):
                raise RuntimeError(f"{name} exited ({process.returncode}); see {base / 'Reports' / (args.application + '.log')}")
            if time.monotonic() >= deadline:
                raise TimeoutError(f"{name}'s local bridge did not start within 60 seconds")
            time.sleep(0.5)
    command = [str(Path.home() / ".local/bin" / server)]
    environment = os.environ.copy()
    environment["PYTHONUTF8"] = "1"
    if args.application == "freecad":
        command.extend(["--host", "127.0.0.1", "--freecadcmd", str(executable.with_name("FreeCADCmd.exe"))])
    else:
        command.extend(["--host", "127.0.0.1", "--port", str(port)])
        environment["BLENDER_MCP_DISABLE_TELEMETRY"] = "true"
    return subprocess.call(command, env=environment)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"CAD bridge startup failed: {error}", file=sys.stderr)
        raise SystemExit(1)
