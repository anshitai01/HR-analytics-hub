# main.py
# Located inside your COMPONENTS folder

from fastapi import FastAPI
# Corrected imports for your structure
from attendance import router as attendance_router

from exit_analysis import router as exit_router

app = FastAPI(
    title="HR AI Suite",
    version="1.0.0"
)

# Include the router from our attendance component
app.include_router(attendance_router.router)

app.include_router(exit_router.router)

@app.get("/", tags=["Health Check"])
def read_root():
    # This is the expected welcome message for our project
    return {"status": "HR AI Suite is running"}