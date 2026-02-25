#!/usr/bin/env python3
"""Run all 5 services in subprocesses for local dev. Kill with Ctrl+C."""
import os
import sys
import subprocess
import signal
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
env = os.environ.copy()
env["PYTHONPATH"] = ROOT
env["ENV"] = "dev"

PORTS = [
    ("orchestration", "services.orchestration.main:app", 8000),
    ("commerce", "services.commerce.main:app", 8001),
    ("memory", "services.memory.main:app", 8002),
    ("agent", "services.agent.main:app", 8003),
    ("gateway", "services.gateway.main:app", 8080),
]

procs = []


def main():
    for name, app, port in PORTS:
        cmd = [sys.executable, "-m", "uvicorn", app, "--host", "0.0.0.0", "--port", str(port)]
        p = subprocess.Popen(cmd, env=env, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        procs.append((name, p))
        print(f"Started {name} on port {port} (pid={p.pid})")
        time.sleep(0.5)

    def on_sig(sig, frame):
        for name, p in procs:
            p.terminate()
            print(f"Stopped {name}")
        sys.exit(0)

    signal.signal(signal.SIGINT, on_sig)
    signal.signal(signal.SIGTERM, on_sig)
    print("\nAll services running. Gateway: http://localhost:8080  Ctrl+C to stop.\n")
    while True:
        time.sleep(1)
        for name, p in procs:
            if p.poll() is not None:
                print(f"{name} exited with {p.returncode}")
                on_sig(None, None)


if __name__ == "__main__":
    main()
