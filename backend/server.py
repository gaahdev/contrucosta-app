from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Tuple
import uuid
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
import jwt

# Import commission routes
from commission_routes import create_commission_router
from push_notifications import notify_commission_update, register_device_token

ROOT_DIR = Path(__file__).parent
# Carregar .env local se existir
env_file = ROOT_DIR / '.env'
if env_file.exists():
    load_dotenv(env_file)

# MongoDB connection - tenta variável de ambiente primeiro, depois .env
mongo_url = os.environ.get('MONGO_URL') or os.environ.get('MONGODB_URI')
if not mongo_url:
    raise ValueError("MONGO_URL ou MONGODB_URI não configurada!")

db_name = os.environ.get('DB_NAME', 'commission_tracker')

print(f"🔗 Conectando ao MongoDB...")
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]
print(f"✅ Conectado a {db_name}")

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
ALGORITHM = "HS256"

# Truck rates configuration
TRUCK_RATES = {
    "BKO": 3.50,
    "PYW": 3.50,
    "NYC": 3.50,
    "GKY": 7.50,
    "GSD": 7.50,
    "AUA": 10.00
}

# Day assignments for drivers
DAY_ASSIGNMENTS = {
    "Davi": "Monday",
    "Ivaney": "Tuesday",
    "Claudio": "Wednesday",
    "Valdiney": "Thursday"
}

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# Models
class UserRegister(BaseModel):
    username: str
    password: str
    name: str
    role: str  # 'driver' or 'helper'

class UserLogin(BaseModel):
    username: str
    password: str

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    name: str
    role: str
    assigned_day: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DeliveryRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: str
    truck_type: str
    value: float
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DeliveryCreate(BaseModel):
    employee_id: str
    truck_type: str
    value: float

class OccurrenceRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: str
    employee_name: str
    occurrence_type: str
    description: str
    truck_type: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class OccurrenceCreate(BaseModel):
    employee_id: str
    employee_name: str
    occurrence_type: str
    description: str
    truck_type: str

class UserDashboard(BaseModel):
    user: User
    deliveries: dict
    total_deliveries: int
    total_commission: float

class AdminUserSummary(BaseModel):
    user: User
    total_deliveries: int
    total_commission: float


class DeviceTokenRegister(BaseModel):
    token: str
    platform: str = "android"

# Helper functions
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = decode_token(token)
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return User(**user)
    except Exception:
        raise HTTPException(status_code=401, detail="Authentication required")

async def get_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

def get_week_start(date: datetime = None) -> str:
    """Get the Monday of the current week in ISO format"""
    if date is None:
        date = datetime.now(timezone.utc)
    # Get the Monday of the week
    days_since_monday = date.weekday()
    monday = date - timedelta(days=days_since_monday)
    return monday.date().isoformat()

def get_assigned_day(name: str) -> Optional[str]:
    """Get assigned day for driver based on name"""
    return DAY_ASSIGNMENTS.get(name)

def is_assigned_day_today(assigned_day: str) -> bool:
    """Check if today is the assigned day for the driver"""
    today = datetime.now(timezone.utc)
    current_day = today.strftime("%A")  # Returns day name like "Monday", "Tuesday", etc.
    return current_day == assigned_day

def is_special_member(employee_name: Optional[str]) -> bool:
    if not employee_name:
        return False
    return employee_name.strip().lower() == "valdiney"


def is_month_closed(month: int, year: int) -> bool:
    """Retorna True quando o mês já encerrou."""
    now = datetime.now(timezone.utc)
    return (year < now.year) or (year == now.year and month < now.month)


def parse_iso_datetime(value: str) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None

def get_tier_percentage(employee_id: str, occurrence_counts: Dict[str, int], employee_name: Optional[str] = None) -> float:
    """Calcula percentual por tier de ocorrências.

    Regras padrão:
    - Mais ocorrências: 0.8%
    - Ocorrências medianas: 0.9%
    - Menos ocorrências: 1.0%
    - Se todos tiverem 0 ocorrências: 1.0% para todos

    Regra especial Valdiney:
    - Fixo em 2.5%
    """
    is_valdiney = is_special_member(employee_name)
    if is_valdiney:
        return 2.5

    min_rate = 0.8
    mid_rate = 0.9
    max_rate = 1.0

    if not occurrence_counts:
        return max_rate

    if all(count == 0 for count in occurrence_counts.values()):
        return max_rate

    members_with_occurrence = [
        (emp_id, count) for emp_id, count in occurrence_counts.items() if count > 0
    ]
    members_with_occurrence.sort(key=lambda item: item[1], reverse=True)

    # Regra específica: apenas 1 membro com ocorrência -> só ele recebe a menor taxa
    if len(members_with_occurrence) == 1:
        return min_rate if employee_id == members_with_occurrence[0][0] else max_rate

    # Regra específica: 2 membros com ocorrência -> maior recebe menor taxa, menor recebe taxa média, restante taxa máxima
    if len(members_with_occurrence) == 2:
        first_id = members_with_occurrence[0][0]
        second_id = members_with_occurrence[1][0]
        first_count = members_with_occurrence[0][1]
        second_count = members_with_occurrence[1][1]
        if first_count == second_count and employee_id in {first_id, second_id}:
            return mid_rate
        if employee_id == first_id:
            return min_rate
        if employee_id == second_id:
            return mid_rate
        return max_rate

    sorted_employees = sorted(
        occurrence_counts.items(),
        key=lambda item: item[1],
        reverse=True
    )

    positions = {emp_id: idx for idx, (emp_id, _) in enumerate(sorted_employees)}
    position = positions.get(employee_id, len(sorted_employees) - 1)

    total = len(sorted_employees)
    tier_size = total / 3

    if position < tier_size:
        return min_rate
    if position < tier_size * 2:
        return mid_rate
    return max_rate

async def get_occurrence_count_map() -> Dict[str, int]:
    """Retorna mapa employee_id -> quantidade de ocorrências para todos os membros."""
    users = await db.users.find(
        {"role": {"$in": ["driver", "helper"]}},
        {"_id": 0, "id": 1}
    ).to_list(1000)

    occurrence_counts: Dict[str, int] = {}
    for user in users:
        employee_id = user.get("id")
        if not employee_id:
            continue
        occurrence_counts[employee_id] = await db.occurrences.count_documents({"employee_id": employee_id})

    return occurrence_counts


async def get_occurrence_count_map_for_period(month: int, year: int) -> Dict[str, int]:
    """Mapa employee_id -> ocorrências apenas do mês/ano informado."""
    users = await db.users.find(
        {"role": {"$in": ["driver", "helper"]}},
        {"_id": 0, "id": 1}
    ).to_list(1000)

    period_prefix = f"{year:04d}-{month:02d}"
    occurrence_counts: Dict[str, int] = {}

    for user in users:
        employee_id = user.get("id")
        if not employee_id:
            continue
        occurrence_counts[employee_id] = await db.occurrences.count_documents(
            {
                "employee_id": employee_id,
                "created_at": {"$regex": f"^{period_prefix}"},
            }
        )

    return occurrence_counts


def get_monthly_percentage(
    employee_id: str,
    employee_name: Optional[str],
    occurrence_counts: Dict[str, int],
    month: int,
    year: int,
) -> float:
    """
    Regra provisória para a tela Users & Commissions:
    - Todos ficam em 0.8%
    - Exceção Valdiney: regra especial já existente

    Observação:
    - O fechamento final por ranking (0.8/0.9/1.0) é aplicado apenas no relatório mensal.
    """
    if is_special_member(employee_name):
        return get_tier_percentage(employee_id, occurrence_counts, employee_name)

    return 0.8


def get_final_monthly_percentage(
    employee_id: str,
    employee_name: Optional[str],
    occurrence_counts: Dict[str, int],
) -> float:
    """
    Percentual final de fechamento mensal:
    - Mais ocorrências: 0.8%
    - Meio: 0.9%
    - Menos ocorrências: 1.0%
    - Exceção Valdiney: regra especial (2.5% fixo)
    """
    return get_tier_percentage(employee_id, occurrence_counts, employee_name)


def get_delivery_values_for_period(deliveries: List[dict], month: int, year: int) -> Tuple[float, float]:
    """Retorna total geral e total do mês/ano informado para uma lista de entregas."""
    total_all_time = sum(d.get("value", 0) for d in deliveries)
    total_period = 0.0

    for delivery in deliveries:
        dt = parse_iso_datetime(str(delivery.get("created_at", "")))
        if dt and dt.month == month and dt.year == year:
            total_period += float(delivery.get("value", 0))

    return total_all_time, total_period

# Calculate commission for a user
async def calculate_user_commission(user_id: str) -> dict:
    deliveries = await db.deliveries.find({"user_id": user_id}, {"_id": 0}).to_list(100)
    
    delivery_dict = {truck: 0 for truck in TRUCK_RATES.keys()}
    total_deliveries = 0
    total_commission = 0.0
    
    for delivery in deliveries:
        truck = delivery['truck_type']
        count = delivery['delivery_count']
        delivery_dict[truck] = count
        total_deliveries += count
        total_commission += count * TRUCK_RATES[truck]
    
    return {
        "deliveries": delivery_dict,
        "total_deliveries": total_deliveries,
        "total_commission": round(total_commission, 2)
    }

# Routes
@api_router.post("/auth/register")
async def register(user_data: UserRegister):
    # Check if username exists
    existing_user = await db.users.find_one({"username": user_data.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Validate role
    if user_data.role not in ["driver", "helper"]:
        raise HTTPException(status_code=400, detail="Role must be 'driver' or 'helper'")
    
    # Get assigned day for driver
    assigned_day = None
    if user_data.role == "driver":
        assigned_day = get_assigned_day(user_data.name)
    
    # Create user
    user = User(
        username=user_data.username,
        name=user_data.name,
        role=user_data.role,
        assigned_day=assigned_day
    )
    
    user_doc = user.model_dump()
    user_doc['password'] = hash_password(user_data.password)
    user_doc['created_at'] = user_doc['created_at'].isoformat()
    
    await db.users.insert_one(user_doc)
    
    # Initialize delivery records for all trucks
    for truck in TRUCK_RATES.keys():
        delivery = DeliveryRecord(user_id=user.id, truck_type=truck, delivery_count=0)
        delivery_doc = delivery.model_dump()
        delivery_doc['updated_at'] = delivery_doc['updated_at'].isoformat()
        await db.deliveries.insert_one(delivery_doc)
    
    token = create_access_token({"user_id": user.id, "role": user.role})
    return {"token": token, "user": user}

@api_router.post("/auth/login")
async def login(credentials: UserLogin):
    user = await db.users.find_one({"username": credentials.username}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(credentials.password, user['password']):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({"user_id": user['id'], "role": user['role']})
    user_obj = User(**user)
    return {"token": token, "user": user_obj}


@api_router.post("/notifications/token")
async def register_notification_token(
    payload: DeviceTokenRegister,
    current_user: User = Depends(get_current_user),
):
    await register_device_token(
        db=db,
        employee_id=current_user.id,
        employee_name=current_user.name,
        role=current_user.role,
        token=payload.token,
        platform=payload.platform,
    )
    return {"success": True}


@api_router.get("/notifications/me")
async def get_my_notifications(
    current_user: User = Depends(get_current_user),
    limit: int = 50,
):
    safe_limit = max(1, min(limit, 100))
    notifications = await db.notifications.find(
        {"employee_id": current_user.id},
        {"_id": 0},
    ).sort("timestamp", -1).to_list(safe_limit)
    return {"notifications": notifications, "total": len(notifications)}

@api_router.get("/user/dashboard", response_model=UserDashboard)
async def get_user_dashboard(current_user: User = Depends(get_current_user)):
    commission_data = await calculate_user_commission(current_user.id)

    return UserDashboard(
        user=current_user,
        deliveries=commission_data["deliveries"],
        total_deliveries=commission_data["total_deliveries"],
        total_commission=commission_data["total_commission"]
    )

@api_router.get("/admin/users/legacy", response_model=List[AdminUserSummary])
async def get_all_users(admin: User = Depends(get_admin_user)):
    users = await db.users.find({"role": {"$in": ["driver", "helper"]}}, {"_id": 0}).to_list(1000)
    
    result = []
    for user_data in users:
        user = User(**user_data)
        commission_data = await calculate_user_commission(user.id)
        result.append(AdminUserSummary(
            user=user,
            total_deliveries=commission_data["total_deliveries"],
            total_commission=commission_data["total_commission"]
        ))
    
    return result

# Remover endpoint antigo @api_router.post("/admin/delivery") - usar /api/deliveries em vez disso@api_router.get("/admin/user/{user_id}/deliveries")
async def get_user_deliveries(user_id: str, admin: User = Depends(get_admin_user)):
    deliveries = await db.deliveries.find({"user_id": user_id}, {"_id": 0}).to_list(100)
    return deliveries

# NOVO SISTEMA DE COMISSÃO - endpoints por valor (não por contagem)
@api_router.post("/deliveries")
async def create_delivery(payload: DeliveryCreate):
    """Registra uma entrega com valor por caminhão"""
    if payload.truck_type not in TRUCK_RATES:
        raise HTTPException(status_code=400, detail="Invalid truck type")
    
    delivery = {
        "id": str(uuid.uuid4()),
        "employee_id": payload.employee_id,
        "truck_type": payload.truck_type,
        "value": payload.value,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    delivery_doc = delivery.copy()
    result = await db.deliveries.insert_one(delivery_doc)
    logger.info(f"✅ Entrega inserida no MongoDB: {payload.employee_id} - {payload.truck_type} - R${payload.value} (ID: {result.inserted_id})")

    employee = await db.users.find_one({"id": payload.employee_id}, {"_id": 0, "name": 1})
    employee_name = employee.get("name", f"Funcionário {payload.employee_id}") if employee else f"Funcionário {payload.employee_id}"
    push_result = await notify_commission_update(
        db=db,
        employee_id=payload.employee_id,
        employee_name=employee_name,
        amount=payload.value,
        truck_type=payload.truck_type,
    )

    return {
        "success": True,
        "delivery": delivery,
        "inserted_id": str(result.inserted_id),
        "notification_sent": push_result.get("sent", 0) > 0,
        "notification_result": push_result,
    }

@api_router.post("/occurrences")
async def create_occurrence(payload: OccurrenceCreate):
    """Registra uma ocorrência"""
    occurrence = {
        "id": str(uuid.uuid4()),
        "employee_id": payload.employee_id,
        "employee_name": payload.employee_name,
        "type": payload.occurrence_type,
        "description": payload.description,
        "truck_type": payload.truck_type,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    occurrence_doc = occurrence.copy()
    result = await db.occurrences.insert_one(occurrence_doc)
    logger.info(f"✅ Ocorrência inserida no MongoDB: {payload.employee_id} - {payload.occurrence_type} (ID: {result.inserted_id})")
    return {
        "success": True,
        "occurrence": occurrence,
        "inserted_id": str(result.inserted_id)
    }

@api_router.get("/admin/users")
async def get_admin_users_new(admin: User = Depends(get_admin_user)):
    """Retorna lista de usuários com novo sistema de comissão"""
    users = await db.users.find({"role": {"$in": ["driver", "helper"]}}, {"_id": 0, "password": 0}).to_list(1000)
    logger.info(f"📋 Buscando dados de {len(users)} usuários do MongoDB")

    now = datetime.now(timezone.utc)
    month = now.month
    year = now.year
    occurrence_counts = await get_occurrence_count_map_for_period(month, year)
    
    result = []
    today_iso = datetime.now(timezone.utc).date().isoformat()
    for user_data in users:
        user_id = user_data["id"]
        
        # Busca entregas
        deliveries = await db.deliveries.find({"employee_id": user_id}, {"_id": 0}).to_list(1000)
        total_delivered, month_delivered = get_delivery_values_for_period(deliveries, month, year)
        today_delivered_value = sum(
            d.get("value", 0)
            for d in deliveries
            if str(d.get("created_at", "")).startswith(today_iso)
        )
        
        # Agrupa por caminhão
        by_truck = {}
        for d in deliveries:
            truck = d.get("truck_type", "")
            if truck:
                if truck not in by_truck:
                    by_truck[truck] = {"count": 0, "total_value": 0}
                by_truck[truck]["count"] += 1
                by_truck[truck]["total_value"] += d.get("value", 0)
        
        # Conta ocorrências e calcula percentual por tier
        occurrence_count = occurrence_counts.get(user_id, 0)
        percentage = get_monthly_percentage(user_id, user_data.get("name"), occurrence_counts, month, year)
        
        # Calcula valor a receber com base no mês atual
        value_to_receive = month_delivered * (percentage / 100)
        
        logger.info(
            f"  👤 {user_data['name']}: {len(deliveries)} entregas "
            f"(mês R${month_delivered:.2f}, total R${total_delivered:.2f}), "
            f"{occurrence_count} ocorrências no mês, {percentage:.1f}% comissão"
        )
        
        result.append({
            "user": {
                "id": user_data["id"],
                "name": user_data["name"],
                "username": user_data["username"],
                "role": user_data["role"],
                "assigned_day": user_data.get("assigned_day")
            },
            "total_deliveries": len(deliveries),
            "total_commission": round(value_to_receive, 2),
            "total_delivered_value": round(month_delivered, 2),
            "all_time_delivered_value": round(total_delivered, 2),
            "today_delivered_value": round(today_delivered_value, 2),
            "value_to_receive": round(value_to_receive, 2),
            "by_truck": by_truck,
            "statistics": {
                "occurrence_count": occurrence_count,
                "percentage": percentage,
                "month": month,
                "year": year,
                "status": "closed" if is_month_closed(month, year) else "provisional"
            }
        })
    
    return result

@api_router.get("/employees/{employee_id}")
async def get_employee_summary(employee_id: str):
    """Retorna resumo de entrega de um motorista"""
    # Busca entregas
    deliveries = await db.deliveries.find({"employee_id": employee_id}, {"_id": 0}).to_list(1000)
    now = datetime.now(timezone.utc)
    month = now.month
    year = now.year
    total_delivered, month_delivered = get_delivery_values_for_period(deliveries, month, year)
    today_iso = datetime.now(timezone.utc).date().isoformat()
    today_delivered_value = sum(
        d.get("value", 0)
        for d in deliveries
        if str(d.get("created_at", "")).startswith(today_iso)
    )
    
    # Agrupa por caminhão
    by_truck = {}
    for d in deliveries:
        truck = d.get("truck_type", "")
        if truck:
            if truck not in by_truck:
                by_truck[truck] = {"count": 0, "total_value": 0}
            by_truck[truck]["count"] += 1
            by_truck[truck]["total_value"] += d.get("value", 0)
    
    # Busca dados do usuário
    user = await db.users.find_one({"id": employee_id}, {"_id": 0, "password": 0})
    user_name = user.get("name", f"Funcionário {employee_id}") if user else f"Funcionário {employee_id}"

    # Busca ocorrências detalhadas
    occurrences = await db.occurrences.find(
        {"employee_id": employee_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(200)
    occurrence_count = 0
    for occurrence in occurrences:
        dt = parse_iso_datetime(str(occurrence.get("created_at", "")))
        if dt and dt.month == month and dt.year == year:
            occurrence_count += 1

    # Calcula percentual por tier (comparando com todos os membros)
    occurrence_counts = await get_occurrence_count_map_for_period(month, year)
    percentage = get_monthly_percentage(employee_id, user_name, occurrence_counts, month, year)
    
    # Calcula valor a receber no mês atual
    value_to_receive = month_delivered * (percentage / 100)
    
    return {
        "employee_id": employee_id,
        "name": user_name,
        "total_delivered_value": round(month_delivered, 2),
        "all_time_delivered_value": round(total_delivered, 2),
        "today_delivered_value": round(today_delivered_value, 2),
        "value_to_receive": round(value_to_receive, 2),
        "by_truck": by_truck,
        "occurrence_count": occurrence_count,
        "percentage": percentage,
        "month": month,
        "year": year,
        "status": "closed" if is_month_closed(month, year) else "provisional",
        "occurrences": occurrences
    }


@api_router.get("/reports/monthly-commission")
async def get_monthly_commission_report(
    month: int,
    year: int,
    admin: User = Depends(get_admin_user),
):
    """Gera relatório mensal de comissão por ranking de ocorrências."""
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12")

    users = await db.users.find(
        {"role": {"$in": ["driver", "helper"]}},
        {"_id": 0, "password": 0}
    ).to_list(1000)

    occurrence_counts = await get_occurrence_count_map_for_period(month, year)
    report_rows = []

    for user_data in users:
        user_id = user_data["id"]
        name = user_data.get("name")
        deliveries = await db.deliveries.find({"employee_id": user_id}, {"_id": 0}).to_list(5000)
        _, month_delivered = get_delivery_values_for_period(deliveries, month, year)

        percentage = get_monthly_percentage(user_id, name, occurrence_counts, month, year)
        commission_value = month_delivered * (percentage / 100)

        final_percentage = get_final_monthly_percentage(user_id, name, occurrence_counts)
        final_commission_value = month_delivered * (final_percentage / 100)

        report_rows.append({
            "employee_id": user_id,
            "employee_name": name,
            "role": user_data.get("role"),
            "occurrence_count": occurrence_counts.get(user_id, 0),
            "monthly_delivered_value": round(month_delivered, 2),
            "percentage": round(percentage, 2),
            "commission_value": round(commission_value, 2),
            "final_percentage": round(final_percentage, 2),
            "final_commission_value": round(final_commission_value, 2),
        })

    report_rows.sort(key=lambda row: (row["occurrence_count"], -row["monthly_delivered_value"]))

    total_delivered = round(sum(row["monthly_delivered_value"] for row in report_rows), 2)
    total_commission = round(sum(row["commission_value"] for row in report_rows), 2)
    total_final_commission = round(sum(row["final_commission_value"] for row in report_rows), 2)

    return {
        "month": month,
        "year": year,
        "status": "closed" if is_month_closed(month, year) else "provisional",
        "policy": {
            "default_rate_during_month": 0.8,
            "closing_rates": {
                "fewer_occurrences": 1.0,
                "middle": 0.9,
                "more_occurrences": 0.8,
            },
            "special_member": "Valdiney",
        },
        "summary": {
            "employees": len(report_rows),
            "total_delivered_value": total_delivered,
            "total_commission_value": total_commission,
            "total_final_commission_value": total_final_commission,
        },
        "rows": report_rows,
    }

app.include_router(api_router)

# Register commission routes (novo sistema de comissões)
commission_router = create_commission_router(db, security)
app.include_router(commission_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    # Create default admin user if doesn't exist
    admin = await db.users.find_one({"username": "admin"})
    if not admin:
        admin_user = User(
            username="admin",
            name="Administrator",
            role="admin"
        )
        admin_doc = admin_user.model_dump()
        admin_doc['password'] = hash_password("admin123")
        admin_doc['created_at'] = admin_doc['created_at'].isoformat()
        await db.users.insert_one(admin_doc)
        logger.info("Default admin user created (username: admin, password: admin123)")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
