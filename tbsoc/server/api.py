from fastapi import APIRouter, HTTPException, BackgroundTasks
from tbsoc.server.schemas import FitConfig, FitStatus
from tbsoc.entrypoints.fitsoc import fitsoc
import os
import glob

router = APIRouter()

# Global status (simplistic for single-user desktop app)
import threading

# Global variables
stop_event = threading.Event()
current_status = FitStatus(status="idle", progress=0.0, message="Ready")

def run_fitting_task(config: FitConfig):
    global current_status
    try:
        current_status.status = "running"
        current_status.message = "Fitting in progress..."
        current_status.progress = 0.1
        
        # Reset cancel event
        stop_event.clear()
        
        def check_stop():
            if stop_event.is_set():
                raise Exception("Stopped by User")
        
        # Convert config to dict
        config_dict = config.dict()
        
        # Resolve paths relative to current_directory
        cwd = state.current_directory
        file_keys = ['posfile', 'winfile', 'hrfile', 'kpfile', 'eigfile']
        for key in file_keys:
            if key in config_dict and config_dict[key]:
                 # Only modify if it's not already absolute
                 if not os.path.isabs(config_dict[key]):
                     config_dict[key] = os.path.join(cwd, config_dict[key])
        
        # Pass check_stop to fitsoc
        result = fitsoc(config_dict, check_stop=check_stop)
        
        if not result["success"] and "Interrupted" in result["message"]:
             current_status.status = "error"
             current_status.message = result["message"]
        else:
             current_status.status = "completed"
             current_status.message = "Fitting completed successfully."
             
        current_status.progress = 1.0
        current_status.result = result
        
    except Exception as e:
        current_status.status = "error"
        current_status.message = str(e)
        print(f"Error during fitting: {e}")

@router.post("/fit")
async def start_fit(config: FitConfig, background_tasks: BackgroundTasks):
    global current_status
    if current_status.status == "running":
        raise HTTPException(status_code=400, detail="A fitting task is already running.")
    
    background_tasks.add_task(run_fitting_task, config)
    return {"message": "Fitting task started"}

@router.post("/fit/stop")
async def stop_fit():
    global current_status
    if current_status.status == "running":
        stop_event.set()
        current_status.message = "Stopping..."
        return {"message": "Stop signal sent"}
    return {"message": "No running task to stop"}

@router.get("/status", response_model=FitStatus)
async def get_status():
    global current_status
    return current_status

from tbsoc.server.state import state
import webview

@router.post("/choose-directory")
async def choose_directory():
    """Opens a native folder picker dialog and updates current directory."""
    if not state.window:
        raise HTTPException(status_code=500, detail="Window not available")
        
    # Open folder dialog (runs on main thread via pywebview)
    # result is a tuple of paths or None
    result = state.window.create_file_dialog(webview.FileDialog.FOLDER)
    
    if result and len(result) > 0:
        new_path = result[0]
        state.current_directory = new_path
        return {"path": new_path}
    
    return {"path": state.current_directory}

@router.get("/current-directory")
async def get_current_directory():
    return {"path": state.current_directory}

from tbsoc.server.schemas import FitConfig, FitStatus, TBBandsRequest

@router.post("/load-data")
async def load_data_endpoint(config: FitConfig):
    """Explicitly load data into cache for visualization."""
    try:
        config_dict = config.dict()
        cwd = state.current_directory
        file_keys = ['posfile', 'winfile', 'hrfile', 'kpfile', 'eigfile']
        for key in file_keys:
            if key in config_dict and config_dict[key]:
                 if not os.path.isabs(config_dict[key]):
                     config_dict[key] = os.path.join(cwd, config_dict[key])
        
        state.data_manager.load_if_needed(config_dict)
        
        dm = state.data_manager
        
        # Auto-align check on load
        # get_dft_bands will use best_offset if calculated in _precalculate
        
        return {
            "status": "loaded",
            "orb_labels": dm.orb_labels
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/structure")
async def get_structure():
    s = state.data_manager.get_structure()
    if not s:
        raise HTTPException(status_code=400, detail="Data not loaded. Trigger load first.")
    return s

@router.get("/bands/dft")
async def get_dft_bands():
    b = state.data_manager.get_dft_bands()
    if not b:
        raise HTTPException(status_code=400, detail="Data not loaded")
    return b

@router.post("/bands/tb")
async def get_tb_bands(req: TBBandsRequest):
    try:
        result = state.data_manager.calculate_tb_bands(req.lambdas)
        if result is None:
             raise HTTPException(status_code=400, detail="Data not loaded")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/save-hr")
async def save_hr(req: TBBandsRequest):
    try:
        path = state.data_manager.save_hr_file(req.lambdas)
        return {"message": "Success", "path": path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/files")
async def list_files():
    """List files in the current working directory."""
    path = state.current_directory
    
    if not os.path.exists(path):
         return [] 
         
    items = []
    try:
        with os.scandir(path) as it:
            for entry in it:
                items.append({
                    "name": entry.name,
                    "is_dir": entry.is_dir(),
                    "path": entry.path
                })
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))
         
    return sorted(items, key=lambda x: (not x['is_dir'], x['name']))
