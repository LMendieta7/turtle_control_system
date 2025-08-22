# utils/network.py

import subprocess
import platform

def esp_ping(host: str, timeout_ms: int = 500) -> bool:
    """
    Cross-platform ping: tries Linux/macOS and Windows.
    Returns True if any succeeds.
    Prints the actual command and result for debugging.
    """
    system = platform.system()
    if system in ("Linux", "Darwin"):
        # Use Linux/macOS ping: -c 1 -W timeout_s
        timeout_s = max(1, int(round(timeout_ms / 1000)))
        linux_args = ["ping", "-c", "1", "-W", str(timeout_s), host]
        print("Trying Linux/macOS ping:", " ".join(linux_args))
        try:
            res = subprocess.run(linux_args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"Linux ping return code: {res.returncode}")
            return res.returncode == 0
        except Exception as e:
            print("Linux ping exception:", e)
    else:
        # Use Windows ping: -n 1 -w timeout_ms
        windows_args = ["ping", "-n", "1", "-w", str(timeout_ms), host]
        print("Trying Windows ping:", " ".join(windows_args))
        try:
            res = subprocess.run(windows_args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"Windows ping return code: {res.returncode}")
            return res.returncode == 0
        except Exception as e:
            print("Windows ping exception:", e)
    return False
