"""
Local FastAPI server that receives job application data from the
browser extension and hands it off to the PyQt GUI thread safely.
"""

import uvicorn
from fastapi import FastAPI
from PyQt6.QtCore import QObject, pyqtSignal
from myapp.api_models import ExtensionJob

class ApiBridge(QObject):
    """
    Bridges the FastAPI (background thread) and Qt GUI (main thread).
    Emitting a Qt signal from a non-GUI thread and connecting it to a
    slot on the GUI thread is thread-safe by design in Qt.
    """
    job_received = pyqtSignal(dict)

bridge = ApiBridge()

app = FastAPI()

@app.get("/ping")
async def ping():
    """Lets the extension check whether the app is running before posting data."""
    return {"status": "ok"}


@app.post("/jobs")
async def receive_job(job: ExtensionJob):
    """
    Receives job application data posted by the browser extension.
    Sends the data to Qt for it to update the database.
    """
    job = job.model_dump()
    bridge.job_received.emit(job)
    return {"status": "received"}


def run_server(host: str = "127.0.0.1", port: int = 8765):
    """Blocking call — intended to be run inside a background thread."""
    config = uvicorn.Config(app, host=host, port=port, log_level="warning")
    uvicorn.Server(config).run()