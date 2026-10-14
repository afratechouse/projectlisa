"""
Root entry point alias for Project Lisa.
Ensures seamless deployment across Render, Railway, and Heroku environments
whether executing 'uvicorn main:app' or 'uvicorn app.main:app'.
"""
from app.main import app

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)
