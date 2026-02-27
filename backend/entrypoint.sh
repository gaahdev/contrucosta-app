#!/bin/bash
set -e

# Instala dependências da pasta backend
cd /workspace/backend
pip install -r ../requirements.txt

# Executa o servidor persistente
python main.py
