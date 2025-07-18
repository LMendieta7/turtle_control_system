# utils/network.py

import subprocess

def esp_ping(host: str, timeout_ms: int = 500) -> bool:
    """
    Ping `host` once, trying Linux/macOS syntax first, then Windows.
    - Linux/macOS: ping -c 1 -W <timeout_s> <host>
    - Windows:     ping -n 1 -w <timeout_ms> <host>
    Returns True if any succeeds.
    """
    # 1) Try Linux/macOS style
    try:
        timeout_s = max(1, int(timeout_ms / 1000))
        linux_args = ["ping", "-c", "1", "-W", str(timeout_s), host]
        res = subprocess.run(linux_args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode == 0:
            return True
    except FileNotFoundError:
        # ping command not found in this form
        pass
    except Exception:
        pass

    # 2) Fallback to Windows style
    try:
        windows_args = ["ping", "-n", "1", "-w", str(timeout_ms), host]
        res = subprocess.run(windows_args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return (res.returncode == 0)
    except Exception:
        return False
