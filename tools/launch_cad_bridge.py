"""Run a CAD MCP server for an application opened by the user."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("application", choices=("freecad", "blender"))
    args = parser.parse_args()
    server = {
        "freecad": "freecad-mcp.exe",
        "blender": "mcp-for-blender.exe",
    }[args.application]
    command = [str(Path.home() / ".local/bin" / server)]
    environment = os.environ.copy()
    environment["PYTHONUTF8"] = "1"
    if args.application == "freecad":
        manifest_path = Path(os.environ["LOCALAPPDATA"]) / "Haptell/Reports/tools.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        executable = Path(manifest["FreeCAD"]["executable"])
        command.extend(["--host", "127.0.0.1", "--freecadcmd", str(executable.with_name("FreeCADCmd.exe"))])
    else:
        command.extend(["--host", "127.0.0.1", "--port", "9876"])
        environment["BLENDER_MCP_DISABLE_TELEMETRY"] = "true"
    return subprocess.call(command, env=environment)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"CAD bridge startup failed: {error}", file=sys.stderr)
        raise SystemExit(1)
