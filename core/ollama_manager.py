import os
import subprocess
import time
import requests

OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODELS_PATH = "/usr/share/ollama/.ollama/models"

def is_ollama_running() -> bool:
    try:
        requests.get(OLLAMA_URL, timeout=1)
        return True
    except requests.exceptions.ConnectionError:
        return False

def start_ollama(timeout: int = 15):
    """Start Ollama if it's not already running. Returns the process if we
    started it (so we know to stop it later), or None if it was already up."""
    if is_ollama_running():
        return None

    env = os.environ.copy()
    env["OLLAMA_MODELS"] = OLLAMA_MODELS_PATH

    process = subprocess.Popen(
        ["ollama", "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
    )

    waited = 0
    while not is_ollama_running():
        time.sleep(0.5)
        waited += 0.5
        if waited >= timeout:
            raise RuntimeError("Ollama did not start in time")

    return process

def stop_ollama(process) -> None:
    """Only stop it if we're the ones who started it."""
    if process is not None:
        process.terminate()
        process.wait()