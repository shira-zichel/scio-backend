"""
SCiO Backend - Main Entry Point
Run this file to start the API server.
"""

import uvicorn

from api import app


if __name__ == "__main__":
    print("Starting SCiO Backend API...")
    print("API Documentation: http://localhost:8000/docs")
    print("Scan Reports: http://localhost:8000/scan-reports")
    print("-" * 50)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)

