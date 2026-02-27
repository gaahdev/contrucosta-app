"""
Servidor FastAPI com persistência em JSON (simula MongoDB)
Todos os dados são salvos em arquivo para não perder ao recarregar
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

# Modelos Pydantic
class DeliveryCreate(BaseModel):
    employee_id: str
    truck_type: str
    value: float

class OccurrenceCreate(BaseModel):
    employee_id: str
    employee_name: str
    occurrence_type: str
    description: str
    truck_type: str

# Criar diretório de dados se não existir
DATA_DIR = Path("/tmp/contrucosta_data")
DATA_DIR.mkdir(exist_ok=True)

DELIVERIES_FILE = DATA_DIR / "deliveries.json"
OCCURRENCES_FILE = DATA_DIR / "occurrences.json"

# Carregue dados de arquivo ou inicialize vazios
def load_data(filename):
    if filename.exists():
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_data(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Inicialize dados
deliveries = load_data(DELIVERIES_FILE)
occurrences = load_data(OCCURRENCES_FILE)

# Dados de funcionários (templates iniciais)
employees_data = {
    "emp_001": {"name": "João Silva", "role": "driver"},
    "emp_002": {"name": "Maria Santos", "role": "helper"},
    "emp_003": {"name": "Pedro Costa", "role": "driver"},
}

# Taxas por caminhão
TRUCK_RATES = {
    "BKO": 3.50,
    "PYW": 3.50,
    "NYC": 3.50,
    "GKY": 7.50,
    "GSD": 7.50,
    "AUA": 10.00
}

# Criar FastAPI app
app = FastAPI(title="Contrucosta API - Persistent")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------- ENDPOINTS ---------

@app.get("/api/status")
async def status():
    """Status do servidor"""
    return {
        "status": "ok",
        "backend": "persistent (JSON files)",
        "deliveries": len(deliveries),
        "occurrences": len(occurrences)
    }

@app.post("/api/deliveries")
async def create_delivery(payload: DeliveryCreate):
    """Registra uma entrega"""
    if payload.truck_type not in TRUCK_RATES:
        raise HTTPException(status_code=400, detail="Invalid truck type")
    
    delivery = {
        "id": f"del_{len(deliveries)+1}",
        "employee_id": payload.employee_id,
        "truck_type": payload.truck_type,
        "value": payload.value,
        "created_at": datetime.now().isoformat()
    }
    
    deliveries.append(delivery)
    save_data(DELIVERIES_FILE, deliveries)
    
    print(f"✅ Entrega registrada: {payload.employee_id} - {payload.truck_type} - R${payload.value:.2f}")
    return {"success": True, "delivery": delivery}

@app.post("/api/occurrences")
async def create_occurrence(payload: OccurrenceCreate):
    """Registra uma ocorrência"""
    occurrence = {
        "id": f"occ_{len(occurrences)+1}",
        "employee_id": payload.employee_id,
        "employee_name": payload.employee_name,
        "type": payload.occurrence_type,
        "description": payload.description,
        "truck_type": payload.truck_type,
        "created_at": datetime.now().isoformat()
    }
    
    occurrences.append(occurrence)
    save_data(OCCURRENCES_FILE, occurrences)
    
    print(f"✅ Ocorrência registrada: {payload.employee_id} - {payload.occurrence_type}")
    return {"success": True, "occurrence": occurrence}

@app.get("/api/admin/users")
async def get_admin_users():
    """Retorna lista de usuários para o AdminDashboard com dados por caminhão"""
    result = []
    
    for emp_id, emp_data in employees_data.items():
        # Busca entregas
        emp_deliveries = [d for d in deliveries if d['employee_id'] == emp_id]
        total_delivered = sum(d['value'] for d in emp_deliveries)
        
        # Agrupa por caminhão
        by_truck = {}
        for d in emp_deliveries:
            truck = d['truck_type']
            if truck not in by_truck:
                by_truck[truck] = {"count": 0, "total_value": 0}
            by_truck[truck]["count"] += 1
            by_truck[truck]["total_value"] += d['value']
        
        # Conta ocorrências
        emp_occ = [o for o in occurrences if o['employee_id'] == emp_id]
        occ_count = len(emp_occ)
        
        # Calcula percentual com base em ocorrências
        if occ_count >= 5:
            percentage = 0.8  # 80%
        elif occ_count >= 2:
            percentage = 0.9  # 90%
        else:
            percentage = 1.0  # 100%
        
        # Calcula valor a receber (percentage já é decimal: 0.8, 0.9, 1.0)
        value_to_receive = total_delivered * percentage
        commission = value_to_receive
        
        result.append({
            "user": {
                "id": emp_id,
                "name": emp_data["name"],
                "username": emp_data["name"].lower().replace(" ", "_"),
                "role": emp_data["role"],
                "assigned_day": "Monday"
            },
            "total_deliveries": len(emp_deliveries),
            "total_commission": round(commission, 2),
            "total_delivered_value": round(total_delivered, 2),
            "value_to_receive": round(value_to_receive, 2),
            "by_truck": by_truck,
            "statistics": {
                "occurrence_count": occ_count,
                "percentage": percentage
            }
        })
    
    print(f"📋 AdminDashboard: {len(result)} usuários retornados")
    return result

@app.get("/api/employees/{employee_id}")
async def get_employee_summary(employee_id: str):
    """Retorna resumo de entrega de um motorista"""
    if employee_id not in employees_data:
        # Se não existe, criar entrada de template
        employees_data[employee_id] = {"name": f"Motorista {employee_id}", "role": "driver"}
    
    emp_data = employees_data[employee_id]
    
    # Busca entregas
    emp_deliveries = [d for d in deliveries if d['employee_id'] == employee_id]
    total_delivered = sum(d['value'] for d in emp_deliveries)
    
    # Agrupa por caminhão
    by_truck = {}
    for d in emp_deliveries:
        truck = d['truck_type']
        if truck not in by_truck:
            by_truck[truck] = {"count": 0, "total_value": 0}
        by_truck[truck]["count"] += 1
        by_truck[truck]["total_value"] += d['value']
    
    # Conta ocorrências
    emp_occ = [o for o in occurrences if o['employee_id'] == employee_id]
    occ_count = len(emp_occ)
    
    # Calcula percentual
    if occ_count >= 5:
        percentage = 0.8
    elif occ_count >= 2:
        percentage = 0.9
    else:
        percentage = 1.0
    
    # Calcula valor a receber
    value_to_receive = total_delivered * percentage
    
    return {
        "employee_id": employee_id,
        "name": emp_data["name"],
        "total_delivered_value": round(total_delivered, 2),
        "value_to_receive": round(value_to_receive, 2),
        "by_truck": by_truck,
        "occurrence_count": occ_count,
        "percentage": percentage
    }

@app.get("/api/admin/stats")
async def get_admin_stats():
    """Retorna estatísticas geral do admin"""
    total_delivered = sum(d['value'] for d in deliveries)
    total_occurrences = len(occurrences)
    
    return {
        "total_deliveries": len(deliveries),
        "total_delivered_value": round(total_delivered, 2),
        "total_occurrences": total_occurrences,
        "unique_employees": len(set(d['employee_id'] for d in deliveries))
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
