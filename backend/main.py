"""
Main entry point - usa server_persistent.py (salva dados em arquivo JSON persistente)
Versão deployável no Koyeb com todos os endpoints do novo sistema
"""
import sys
import os

# Sempre usa server_persistent.py (dados salvos em JSON)
from server_persistent import app

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print(f"🚀 Iniciando servidor na porta {port} com server_persistent.py")
    uvicorn.run(app, host="0.0.0.0", port=port)
