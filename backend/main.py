"""
Main entry point - usa server_simple.py por padrão
"""
import sys
import os

# Sempre usa server_simple.py (sem MongoDB)
from server_simple import app

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
