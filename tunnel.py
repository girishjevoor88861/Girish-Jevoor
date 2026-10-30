"""
CivicAI - Live Public HTTPS Tunnel Manager
Keeps an encrypted public HTTPS tunnel active for real-time worldwide access.
"""

import subprocess
import time
import re
import sys

def run_tunnel():
    print("Initiating CivicAI Live Public HTTPS Tunnel...")
    cmd = [
        'ssh',
        '-o', 'StrictHostKeyChecking=no',
        '-o', 'ServerAliveInterval=20',
        '-o', 'ServerAliveCountMax=5',
        '-R', '80:127.0.0.1:8000',
        'nokey@localhost.run'
    ]

    while True:
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )

            for line in iter(proc.stdout.readline, ''):
                line_str = line.strip()
                if line_str:
                    print(line_str)
                    match = re.search(r'https://[a-zA-Z0-9\.\-]+\.(?:lhr\.life|localhost\.run)', line_str)
                    if match and 'admin.localhost.run' not in match.group(0):
                        live_url = match.group(0)
                        print("=" * 65)
                        print(f" LIVE PUBLIC DEMO URL: {live_url}")
                        print("=" * 65)
                        with open("tunnel_url.txt", "w", encoding="utf-8") as f:
                            f.write(live_url)

            proc.wait()
            print("Tunnel connection dropped. Reconnecting in 3 seconds...")
            time.sleep(3)
        except Exception as e:
            print(f"Tunnel exception: {e}")
            time.sleep(3)

if __name__ == "__main__":
    run_tunnel()
