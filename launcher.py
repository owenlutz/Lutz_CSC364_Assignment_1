import subprocess
import time
import sys

# Order matters: start servers first
ROUTERS = [
    "router_6.py",
    "router_5.py",
    "router_4.py",
    "router_3.py",
    "router_2.py",
    "router_1.py",
]

processes = []

for router in ROUTERS:
    print(f"Starting {router}...")
    proc = subprocess.Popen([sys.executable, router])
    processes.append(proc)
    time.sleep(1)  # give each router time to bind/listen

print("All routers started.")

try:
    # Keep launcher alive while routers run
    for p in processes:
        p.wait()
except KeyboardInterrupt:
    print("\nShutting down routers...")
    for p in processes:
        p.terminate()
