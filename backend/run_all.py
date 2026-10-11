from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _command(app: str, port: int, reload_enabled: bool) -> list[str]:
    command = [
        sys.executable,
        "-m",
        "uvicorn",
        app,
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
    ]
    if reload_enabled:
        command.append("--reload")
    return command


def main() -> int:
    parser = argparse.ArgumentParser(description="Run all distributed library APIs")
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()

    definitions = [
        ("coordinator", "backend.coordinator.main:app", 8000, None),
        ("site1", "backend.site_service.main:app", 8001, 1),
        ("site2", "backend.site_service.main:app", 8002, 2),
        ("site3", "backend.site_service.main:app", 8003, 3),
    ]
    processes: list[tuple[str, subprocess.Popen[bytes]]] = []
    try:
        for name, app, port, site_id in definitions:
            environment = os.environ.copy()
            if site_id is not None:
                environment["SITE_ID"] = str(site_id)
            process = subprocess.Popen(
                _command(app, port, args.reload),
                cwd=PROJECT_ROOT,
                env=environment,
            )
            processes.append((name, process))
            print(f"Started {name} on http://127.0.0.1:{port}")

        while True:
            for name, process in processes:
                return_code = process.poll()
                if return_code is not None:
                    print(f"{name} exited with code {return_code}", file=sys.stderr)
                    return return_code
            time.sleep(0.5)
    except KeyboardInterrupt:
        return 0
    finally:
        for _, process in processes:
            if process.poll() is None:
                process.terminate()
        for _, process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()


if __name__ == "__main__":
    raise SystemExit(main())
