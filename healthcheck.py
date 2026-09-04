import os
import sys
import urllib.error
import urllib.request

port = os.getenv("PORT", "8000")
try:
    resp = urllib.request.urlopen(f"http://localhost:{port}/ready", timeout=5)
    sys.exit(0 if resp.getcode() == 200 else 1)
except (OSError, urllib.error.URLError):
    sys.exit(1)
