"""
Main entry point - usa server.py com novo sistema de comissão
"""
import sys
import os

# Usa server.py com mongodb e novo sistema de comissão
from server import app

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print(f"🚀 Iniciando servidor na porta {port} com server.py e novo sistema de comissão")
    uvicorn.run(app, host="0.0.0.0", port=port)
