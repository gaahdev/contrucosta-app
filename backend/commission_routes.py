"""
Novo sistema de comissões baseado em valor entregue com ocorrências
Endpoints para gerenciamento de comissões e ocorrências
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import List, Optional, Dict
import uuid
from motor.motor_asyncio import AsyncIOMotorDatabase
from push_notifications import notify_commission_update

# Models
class OccurrenceRecord(BaseModel):
    employee_id: str  # ID do funcionário
    employee_name: str = None  # Nome do funcionário
    occurrence_type: str  # "delay", "damage", "accident", "other"
    description: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    month: int = Field(default_factory=lambda: datetime.now(timezone.utc).month)
    year: int = Field(default_factory=lambda: datetime.now(timezone.utc).year)

    class Config:
        json_schema_extra = {
            "example": {
                "employee_id": "emp_123",
                "employee_name": "João Silva",
                "occurrence_type": "delay",
                "description": "Atraso na entrega de 2 horas",
                "month": 2,
                "year": 2026
            }
        }

class CommissionRequest(BaseModel):
    employee_id: str
    total_delivered_value: float  # Valor total de mercadorias entregues
    month: int
    year: int
    notes: Optional[str] = None

class CommissionPostRequest(BaseModel):
    employee_id: str
    employee_name: str
    total_delivered_value: float
    percentage: float
    commission_amount: float
    month: int
    year: int
    occurrence_count: int = 0
    tier: str = "median"
    notes: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "employee_id": "emp_123",
                "employee_name": "João Silva",
                "total_delivered_value": 10500.00,
                "percentage": 0.9,
                "commission_amount": 94.50,
                "month": 2,
                "year": 2026,
                "occurrence_count": 5,
                "tier": "median"
            }
        }

class CommissionRecord(BaseModel):
    employee_id: str
    employee_name: str
    month: int
    year: int
    total_delivered_value: float
    percentage: float  # Percentual aplicado (0.8%, 0.9%, 1.0%)
    commission_amount: float  # Valor final da comissão
    occurrence_count: int  # Total de ocorrências no mês
    tier: str  # "high", "median", "low" - baseado em ocorrências
    posted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    notes: Optional[str] = None

def create_commission_router(db: AsyncIOMotorDatabase, security_dependency) -> APIRouter:
    """Cria router com endpoints de comissões"""
    router = APIRouter(prefix="/api/commission", tags=["commission"])

    # Endpoints
    @router.post("/occurrences")
    async def log_occurrence(occurrence: OccurrenceRecord):
        """
        Lançar uma ocorrência de funcionário
        Ocorrências são usadas para calcular o percentual de comissão
        """
        occurrence_doc = occurrence.model_dump()
        occurrence_doc['created_at'] = occurrence_doc['created_at'].isoformat()
        
        result = await db.occurrences.insert_one(occurrence_doc)
        if not result.inserted_id:
            raise HTTPException(status_code=500, detail="Error saving occurrence")
        
        return {
            "message": "Occurrence logged successfully",
            "occurrence_id": str(result.inserted_id),
            "occurrence": occurrence
        }

    @router.get("/occurrences")
    async def get_all_occurrences(month: int, year: int):
        """
        Obter todas as ocorrências de um mês/ano
        Usado para calcular percentuais
        """
        occurrences = await db.occurrences.find(
            {"month": month, "year": year},
            {"_id": 0}
        ).to_list(1000)
        
        return {
            "month": month,
            "year": year,
            "total_occurrences": len(occurrences),
            "occurrences": occurrences
        }

    @router.get("/occurrences/employee/{employee_id}")
    async def get_employee_occurrences(employee_id: str, month: int, year: int):
        """
        Obter ocorrências de um funcionário específico
        """
        occurrences = await db.occurrences.find(
            {
                "employee_id": employee_id,
                "month": month,
                "year": year
            },
            {"_id": 0}
        ).to_list(100)
        
        return {
            "employee_id": employee_id,
            "month": month,
            "year": year,
            "occurrence_count": len(occurrences),
            "occurrences": occurrences
        }

    @router.post("/calculate")
    async def calculate_commission(commission_req: CommissionRequest):
        """
        Calcular comissão com base em:
        1. Valor total entregue (base 1%)
        2. Número de ocorrências (ajuste para 0.8%, 0.9% ou 1.0%)
        
        Lógica:
        - Buscar todas as ocorrências do mês
        - Agrupar por funcionário
        - Ordenar por quantidade
        - Dividir em 3 tiers iguais
        - Tier alto: 0.8%, Tier médio: 0.9%, Tier baixo: 1.0%
        """
        # Buscar todas as ocorrências do mês
        all_occurrences = await db.occurrences.find(
            {"month": commission_req.month, "year": commission_req.year},
            {"_id": 0}
        ).to_list(1000)
        
        # Agrupar ocorrências por funcionário
        employee_occurrences: Dict[str, int] = {}
        for occ in all_occurrences:
            emp_id = occ['employee_id']
            employee_occurrences[emp_id] = employee_occurrences.get(emp_id, 0) + 1
        
        # Obter contagem de ocorrências do funcionário atual
        current_employee_count = employee_occurrences.get(commission_req.employee_id, 0)
        
        # Determinar o percentual baseado em ocorrências
        percentage = determine_percentage_by_tier(
            commission_req.employee_id,
            employee_occurrences
        )
        
        # Calcular valor da comissão
        commission_amount = round(
            commission_req.total_delivered_value * (percentage / 100),
            2
        )
        
        # Determinar tier
        tier = get_employee_tier(commission_req.employee_id, employee_occurrences)
        
        return {
            "employee_id": commission_req.employee_id,
            "total_delivered_value": commission_req.total_delivered_value,
            "occurrence_count": current_employee_count,
            "percentage": percentage,
            "commission_amount": commission_amount,
            "tier": tier,
            "calculation_breakdown": {
                "value": commission_req.total_delivered_value,
                "percentage": f"{percentage}%",
                "formula": f"{commission_req.total_delivered_value} × {percentage}% = {commission_amount}"
            }
        }

    @router.post("/post")
    async def post_commission(commission_data: CommissionPostRequest):
        """
        Lançar a comissão calculada no sistema
        Triggers notificação para o funcionário
        """
        commission = CommissionRecord(
            employee_id=commission_data.employee_id,
            employee_name=commission_data.employee_name,
            month=commission_data.month,
            year=commission_data.year,
            total_delivered_value=commission_data.total_delivered_value,
            percentage=commission_data.percentage,
            commission_amount=commission_data.commission_amount,
            occurrence_count=commission_data.occurrence_count,
            tier=commission_data.tier,
            notes=commission_data.notes
        )
        
        commission_doc = commission.model_dump()
        commission_doc['posted_at'] = commission_doc['posted_at'].isoformat()
        
        result = await db.commissions.insert_one(commission_doc)
        if not result.inserted_id:
            raise HTTPException(status_code=500, detail="Error posting commission")
        
        # Enviar notificação para o funcionário
        # TODO: Implementar sistema de notificações em tempo real
        await send_commission_notification(
            db,
            commission.employee_id,
            commission.employee_name,
            commission.commission_amount,
            commission.percentage
        )
        
        return {
            "message": "Commission posted successfully",
            "commission_id": str(result.inserted_id),
            "commission": commission.model_dump(),
            "notification_sent": True
        }

    @router.get("/commissions/employee/{employee_id}")
    async def get_employee_commissions(employee_id: str, month: Optional[int] = None, year: Optional[int] = None):
        """
        Obter histórico de comissões de um funcionário
        """
        query = {"employee_id": employee_id}
        if month and year:
            query["month"] = month
            query["year"] = year
        
        commissions = await db.commissions.find(query, {"_id": 0}).sort("posted_at", -1).to_list(100)
        
        return {
            "employee_id": employee_id,
            "commissions": commissions,
            "total": len(commissions),
            "total_commission": sum(c['commission_amount'] for c in commissions)
        }

    @router.get("/commissions")
    async def get_all_commissions(month: Optional[int] = None, year: Optional[int] = None):
        """
        Obter todas as comissões (admin)
        Filtrar por mês/ano se fornecido
        """
        query = {}
        if month and year:
            query = {"month": month, "year": year}
        
        commissions = await db.commissions.find(query, {"_id": 0}).sort("posted_at", -1).to_list(1000)
        
        return {
            "month": month,
            "year": year,
            "total_commissions": len(commissions),
            "total_amount": sum(c['commission_amount'] for c in commissions),
            "commissions": commissions
        }

    @router.get("/statistics")
    async def get_commission_statistics(month: int, year: int):
        """
        Obter estatísticas de comissões de um mês
        """
        commissions = await db.commissions.find(
            {"month": month, "year": year},
            {"_id": 0}
        ).to_list(1000)
        
        occurrences = await db.occurrences.find(
            {"month": month, "year": year},
            {"_id": 0}
        ).to_list(1000)
        
        # Agrupar por tier
        tiers = {"high": 0, "median": 0, "low": 0}
        total_commission = 0
        
        for commission in commissions:
            tiers[commission['tier']] += 1
            total_commission += commission['commission_amount']
        
        return {
            "month": month,
            "year": year,
            "total_commissions_posted": len(commissions),
            "total_occurrences_logged": len(occurrences),
            "tier_distribution": tiers,
            "average_commission": round(total_commission / len(commissions), 2) if commissions else 0,
            "total_commission_amount": round(total_commission, 2)
        }

    return router

# Helper functions
def determine_percentage_by_tier(employee_id: str, employee_occurrences: Dict[str, int]) -> float:
    """
    Determinar o percentual de comissão baseado no tier do funcionário
    Divisão em 3 tiers iguais:
    - Top 33%: 0.8% (mais ocorrências)
    - Middle 33%: 0.9%
    - Bottom 33%: 1.0% (menos ocorrências)
    """
    if not employee_occurrences:
        return 1.0
    
    # Ordenar funcionários por contagem de ocorrências (decrescente)
    sorted_employees = sorted(
        employee_occurrences.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    employee_positions = {emp_id: idx for idx, (emp_id, _) in enumerate(sorted_employees)}
    employee_position = employee_positions.get(employee_id, len(sorted_employees) - 1)
    
    # Dividir em 3 tiers
    total_employees = len(sorted_employees)
    tier_size = total_employees / 3
    
    if employee_position < tier_size:
        return 0.8  # Top tier (mais ocorrências = menor percentual)
    elif employee_position < tier_size * 2:
        return 0.9  # Middle tier
    else:
        return 1.0  # Bottom tier (menos ocorrências = maior percentual)

def get_employee_tier(employee_id: str, employee_occurrences: Dict[str, int]) -> str:
    """Obter o tier (high, median, low) do funcionário"""
    if not employee_occurrences:
        return "low"
    
    sorted_employees = sorted(
        employee_occurrences.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    employee_positions = {emp_id: idx for idx, (emp_id, _) in enumerate(sorted_employees)}
    employee_position = employee_positions.get(employee_id, len(sorted_employees) - 1)
    
    total_employees = len(sorted_employees)
    tier_size = total_employees / 3
    
    if employee_position < tier_size:
        return "high"  # Mais ocorrências
    elif employee_position < tier_size * 2:
        return "median"  # Ocorrências medianas
    else:
        return "low"  # Menos ocorrências

async def send_commission_notification(db: AsyncIOMotorDatabase, employee_id: str, employee_name: str, commission_amount: float, percentage: float):
    """
    Enviar notificação para funcionário quando comissão é lançada
    TODO: Implementar integração com sistema de notificações
    - Notificação em tempo real na app React
    - Push notification para Android/iOS
    - Email para administrador
    """
    result = await notify_commission_update(
        db=db,
        employee_id=employee_id,
        employee_name=employee_name,
        amount=commission_amount,
        percentage=percentage,
    )
    print(
        f"[NOTIFICATION] {employee_name}: Comissão de R$ {commission_amount:.2f} lançada "
        f"(sent={result.get('sent', 0)}, failed={result.get('failed', 0)})"
    )
