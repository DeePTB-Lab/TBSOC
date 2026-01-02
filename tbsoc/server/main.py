import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import threading
import webview
import sys
from tbsoc import __version__

# Create the FastAPI app
app = FastAPI(title="TBSOC", version=__version__)

# Allow CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routes (we will create api.py next)
from tbsoc.server.api import router as api_router
app.include_router(api_router, prefix="/api")

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/api/version")
def get_version():
    return {"version": __version__}

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Mount API
# app.include_router(api_router, prefix="/api") # Already done

# Serve Static Files (Frontend Build)
# We assume the frontend is built into ../frontend/dist (relative to this file's execution or configured path)
# Since we run from repo root, it is frontend/dist
frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../frontend/dist'))

if os.path.exists(frontend_dist):
    # Mount the entire dist directory to root. 
    # html=True allows serving index.html for /
    # This must be the LAST route/mount defined to avoid masking API.
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")
else:
    print(f"Warning: Frontend build not found at {frontend_dist}")

def start_server():
    # Use 0 port to find available, but for simplicity 8000
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")


from tbsoc.server.state import state

def start_desktop_app():
    t = threading.Thread(target=start_server, daemon=True)
    t.start()
    
    # Wait a bit for server
    import time
    time.sleep(1) 
    
    # Create and register window
    window = webview.create_window('TBSOC', 'http://127.0.0.1:8000/', width=1000, height=600)
    state.window = window
    
    webview.start(debug=False)

class MultiWriter:
    def __init__(self, *writers):
        self.writers = writers

    def write(self, message):
        for w in self.writers:
            w.write(message)

    def flush(self):
        for w in self.writers:
            w.flush()

if __name__ == "__main__":
    # Redirect stdout/stderr to capture logs
    # We want to keep printing to console AND write to buffer
    # Redirect stdout/stderr removed as per user revert
    # sys.stdout = MultiWriter(sys.stdout, state.log_buffer)
    # sys.stderr = MultiWriter(sys.stderr, state.log_buffer)
    
    start_desktop_app()
