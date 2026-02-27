"""
Main entry point - usa server_persistent.py (salva dados em arquivo)
"""
import sys
import os

# Usa server_persistent.py (dados salvos em JSON)
from server_persistent import app

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
