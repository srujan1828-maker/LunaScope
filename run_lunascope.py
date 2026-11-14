"""Convenience launcher for LunaScope application."""
import os
import subprocess
import sys

if __name__ == "__main__":
    app_path = os.path.join(os.path.dirname(__file__), "lunascope", "app.py")
    cmd = [sys.executable, "-m", "streamlit", "run", app_path]
    print(f"Launching LunaScope: {' '.join(cmd)}")
    subprocess.run(cmd)
