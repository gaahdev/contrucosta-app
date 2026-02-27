"""
Servidor simplificado SEM MongoDB para teste rápido
Endpoint de comissão e ocorrências funcional
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dados em memória (mock)
occurrences = []
commissions = []
deliveries = []  # Entregas por caminhão

# Mock de motoristas
employees_data = {
    "emp_001": {"name": "João Silva", "role": "driver"},
    "emp_002": {"name": "Maria Santos", "role": "helper"},
    "emp_003": {"name": "Pedro Costa", "role": "driver"},
}

# Caminhões disponíveis
TRUCK_TYPES = {
    "BKO": 3.50,
    "PYW": 3.50,
    "NYC": 3.50,
    "GKY": 7.50,
    "GSD": 7.50,
    "AUA": 10.00
}

# Models
class DeliveryRequest(BaseModel):
    employee_id: str
    truck_type: str
    value: float

class OccurrenceRequest(BaseModel):
    employee_id: str
    employee_name: str
    occurrence_type: str
    description: str
    truck_type: str

class CommissionRequest(BaseModel):
    employee_id: str
    total_delivered_value: float
    month: int
    year: int

class CommissionPostRequest(BaseModel):
    employee_id: str
    employee_name: str
    total_delivered_value: float
    percentage: float
    commission_amount: float
    month: int
    year: int
    occurrence_count: int
    tier: str

# Endpoints de Ocorrência
@app.post("/api/occurrences")
async def log_occurrence(occurrence: OccurrenceRequest):
    """Registra ocorrência"""
    occ_data = occurrence.model_dump()
    occurrences.append(occ_data)
    
    print(f"✅ Ocorrência registrada: {occurrence.employee_name} - {occurrence.occurrence_type}")
    
    return {
        "message": "Occurrence logged successfully",
        "occurrence_id": f"occ_{len(occurrences)}",
        "occurrence": occ_data
    }

@app.get("/api/occurrences")
async def get_occurrences(month: int, year: int):
    """Obtém todas as ocorrências"""
    return {
        "month": month,
        "year": year,
        "total_occurrences": len(occurrences),
        "occurrences": occurrences
    }

@app.get("/api/occurrences/employee/{employee_id}")
async def get_employee_occurrences(employee_id: str, month: int, year: int):
    """Obtém ocorrências de um funcionário"""
    emp_occ = [o for o in occurrences if o['employee_id'] == employee_id]
    return {
        "employee_id": employee_id,
        "month": month,
        "year": year,
        "occurrence_count": len(emp_occ),
        "occurrences": emp_occ
    }

# Endpoints de Comissão
@app.post("/api/commission/calculate")
async def calculate_commission(data: CommissionRequest):
    """Calcula comissão baseada em ocorrências"""
    # Conta ocorrências deste funcionário
    emp_occurrences = [o for o in occurrences if o['employee_id'] == data.employee_id]
    count = len(emp_occurrences)
    
    # Determina percentual por tier
    if count >= 5:
        percentage = 0.8
        tier = "high"
    elif count >= 2:
        percentage = 0.9
        tier = "median"
    else:
        percentage = 1.0
        tier = "low"
    
    commission = data.total_delivered_value * (percentage / 100)
    
    print(f"📊 Comissão calculada: {data.employee_id} - {percentage}% - R$ {commission:.2f}")
    
    return {
        "percentage": percentage,
        "commission_amount": round(commission, 2),
        "occurrence_count": count,
        "tier": tier
    }

@app.post("/api/commission/post")
async def post_commission(data: CommissionPostRequest):
    """Lança comissão no sistema"""
    com_data = data.model_dump()
    commissions.append(com_data)
    
    print(f"💰 Comissão lançada: {data.employee_name} - R$ {data.commission_amount:.2f}")
    
    return {
        "message": "Commission posted successfully",
        "commission_id": f"com_{len(commissions)}",
        "commission": com_data,
        "notification_sent": True
    }

@app.get("/api/commission/history")
async def get_commissions(month: Optional[int] = None, year: Optional[int] = None):
    """Obtém histórico de comissões"""
    filtered = commissions
    if month and year:
        filtered = [c for c in commissions if c['month'] == month and c['year'] == year]
    return {
        "total": len(filtered),
        "commissions": filtered
    }

@app.get("/api/commission/statistics")
async def get_statistics(month: int, year: int):
    """Obtém estatísticas de comissão"""
    month_commissions = [c for c in commissions if c['month'] == month and c['year'] == year]
    
    if not month_commissions:
        return {
            "month": month,
            "year": year,
            "total_commission": 0,
            "total_employees": 0
        }
    
    total = sum(c['commission_amount'] for c in month_commissions)
    
    return {
        "month": month,
        "year": year,
        "total_commission": round(total, 2),
        "total_employees": len(set(c['employee_id'] for c in month_commissions)),
        "commissions": month_commissions
    }

@app.get("/api/employees")
async def get_employees():
    """Retorna lista de Motoristas/Ajudantes com Valor Total Entregue e Valor a Receber"""
    result = []
    
    for emp_id, emp_data in employees_data.items():
        # Conta ocorrências
        emp_occ = [o for o in occurrences if o['employee_id'] == emp_id]
        occ_count = len(emp_occ)
        
        # Calcula percentual
        if occ_count >= 5:
            percentage = 0.8
        elif occ_count >= 2:
            percentage = 0.9
        else:
            percentage = 1.0
        
        # Calcula valor a receber
        total_delivered = emp_data["total_delivered"]
        value_to_receive = total_delivered * (percentage / 100)
        
        result.append({
            "employee_id": emp_id,
            "name": emp_data["name"],
            "role": emp_data["role"],
            "total_delivered_value": round(total_delivered, 2),
            "value_to_receive": round(value_to_receive, 2),
            "occurrence_count": occ_count,
            "percentage": percentage
        })
    
    print(f"📋 {len(result)} motoristas retornados")
    return result

@app.get("/api/employees/{employee_id}")
async def get_employee_summary(employee_id: str):
    """Retorna dados de um motorista específico com entregas por caminhão"""
    # Busca motorista
    emp_name = "Motorista"
    if employee_id in employees_data:
        emp_name = employees_data[employee_id]["name"]
    else:
        # Se o ID não existe, cria dados mock para o novo usuário
        emp_name = f"Usuário {employee_id[-4:]}"
        # Adiciona algumas entregas fictícias para teste
        if not any(d['employee_id'] == employee_id for d in deliveries):
            deliveries.append({
                'employee_id': employee_id,
                'truck_type': 'BKO',
                'value': 5000.0
            })
            deliveries.append({
                'employee_id': employee_id,
                'truck_type': 'GKY',
                'value': 3500.0
            })
    
    # Busca entregas deste motorista
    emp_deliveries = [d for d in deliveries if d['employee_id'] == employee_id]
    
    # Agrupa por caminhão
    by_truck = {}
    for d in emp_deliveries:
        truck = d['truck_type']
        if truck not in by_truck:
            by_truck[truck] = {"count": 0, "total_value": 0}
        by_truck[truck]["count"] += 1
        by_truck[truck]["total_value"] += d['value']
    
    # Calcula ocorrências
    emp_occ = [o for o in occurrences if o['employee_id'] == employee_id]
    occ_count = len(emp_occ)
    
    # Calcula percentual
    if occ_count >= 5:
        percentage = 0.8
    elif occ_count >= 2:
        percentage = 0.9
    else:
        percentage = 1.0
    
    # Calcula total
    total_delivered = sum(d['value'] for d in emp_deliveries)
    value_to_receive = total_delivered * (percentage / 100)
    
    return {
        "employee_id": employee_id,
        "name": emp_name,
        "total_delivered_value": round(total_delivered, 2),
        "value_to_receive": round(value_to_receive, 2),
        "by_truck": by_truck,
        "occurrence_count": occ_count,
        "percentage": percentage
    }

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
        
        # Calcula percentual
        if occ_count >= 5:
            percentage = 0.8
        elif occ_count >= 2:
            percentage = 0.9
        else:
            percentage = 1.0
        
        # Calcula valor a receber
        value_to_receive = total_delivered * (percentage / 100)
        commission = value_to_receive * (percentage / 100)
        
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

@app.post("/api/employees/{employee_id}/update-value")
async def update_employee_value(employee_id: str, data: dict):
    """Atualiza o valor total entregue de um motorista"""
    if employee_id not in employees_data:
        return {"error": "Employee not found"}, 404
    
    employees_data[employee_id]["total_delivered"] = data.get("total_delivered", employees_data[employee_id]["total_delivered"])
    
    return {
        "message": "Employee value updated",
        "employee_id": employee_id,
        "new_value": employees_data[employee_id]["total_delivered"]
    }

# Endpoints de Entregas por Caminhão
@app.post("/api/deliveries")
async def register_delivery(delivery: DeliveryRequest):
    """Registra entrega de um motorista em um caminhão específico"""
    if delivery.truck_type not in TRUCK_TYPES:
        return {"error": "Invalid truck type"}, 400
    
    delivery_data = {
        "id": f"del_{len(deliveries)+1}",
        "employee_id": delivery.employee_id,
        "truck_type": delivery.truck_type,
        "value": delivery.value,
        "timestamp": __import__('datetime').datetime.now().isoformat()
    }
    deliveries.append(delivery_data)
    
    print(f"📦 Entrega registrada: {delivery.employee_id} - {delivery.truck_type} - R$ {delivery.value:.2f}")
    return {"success": True, "delivery": delivery_data}

@app.get("/api/employees/{employee_id}/deliveries")
async def get_employee_deliveries(employee_id: str):
    """Retorna entregas de um motorista agrupadas por caminhão"""
    emp_deliveries = [d for d in deliveries if d['employee_id'] == employee_id]
    
    # Agrupa por caminhão
    by_truck = {}
    for d in emp_deliveries:
        truck = d['truck_type']
        if truck not in by_truck:
            by_truck[truck] = {"count": 0, "total_value": 0}
        by_truck[truck]["count"] += 1
        by_truck[truck]["total_value"] += d['value']
    
    # Calcula ocorrências
    emp_occ = [o for o in occurrences if o['employee_id'] == employee_id]
    occ_count = len(emp_occ)
    
    # Calcula percentual
    if occ_count >= 5:
        percentage = 0.8
    elif occ_count >= 2:
        percentage = 0.9
    else:
        percentage = 1.0
    
    # Calcula total entregue
    total_delivered = sum(d['value'] for d in emp_deliveries)
    value_to_receive = total_delivered * (percentage / 100)
    
    return {
        "employee_id": employee_id,
        "by_truck": by_truck,
        "total_delivered_value": round(total_delivered, 2),
        "value_to_receive": round(value_to_receive, 2),
        "occurrence_count": occ_count,
        "percentage": percentage
    }

# Health check
@app.get("/api/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    print("🚀 Servidor simplificado rodando em http://localhost:8000")
    print("📚 Docs em http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
