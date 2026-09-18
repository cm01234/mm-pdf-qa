import subprocess
import sys
import time
import urllib.error
import urllib.request


APP_PORT = 8765


def test_streamlit_app_starts():
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "app.py",
            "--server.headless=true",
            f"--server.port={APP_PORT}",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        health_url = f"http://127.0.0.1:{APP_PORT}/_stcore/health"
        deadline = time.monotonic() + 15

        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise AssertionError("Streamlit exited before becoming healthy")

            try:
                with urllib.request.urlopen(health_url, timeout=1) as response:
                    if response.status == 200:
                        return
            except (urllib.error.URLError, TimeoutError):
                time.sleep(0.25)

        raise AssertionError("Streamlit did not become healthy within 15 seconds")
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
