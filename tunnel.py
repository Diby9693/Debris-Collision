import subprocess
import time
import sys

def run_tunnel():
    cmd = [
        "ssh",
        "-o", "StrictHostKeyChecking=no",
        "-o", "ServerAliveInterval=15",
        "-o", "ServerAliveCountMax=5",
        "-R", "80:localhost:8080",
        "nokey@localhost.run"
    ]
    while True:
        try:
            print("Starting localhost.run SSH tunnel...", flush=True)
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in proc.stdout:
                print(line, end="", flush=True)
            proc.wait()
            print("Tunnel connection closed. Reconnecting in 3 seconds...", flush=True)
            time.sleep(3)
        except Exception as e:
            print(f"Tunnel error: {e}", flush=True)
            time.sleep(5)

if __name__ == "__main__":
    run_tunnel()
