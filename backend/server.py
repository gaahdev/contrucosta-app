from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
import jwt

# Import commission routes
from commission_routes import create_commission_router

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

# Checklist items in Portuguese by category
CHECKLIST_ITEMS = {
    "Motor": [
        "verificar óleo do motor",
        "nível do radiador",
        "se há vazamento no motor",
        "drenar o filtro racor"
    ],
    "Freio": [
        "verificar pressão do ar",
        "altura do pedal",
        "drenar o balão de ar"
    ],
    "Direção": [
        "verificar óleo da direção",
        "giro da direção",
        "se há barulho na direção",
        "barra de direção",
        "as molas"
    ],
    "Elétrico": [
        "verificar buzina",
        "setas",
        "sirene de ré",
        "faróis",
        "luz de ré",
        "luz de freio",
        "limpadores",
        "instrumentos no painel",
        "iluminação de placa"
    ],
    "Pneus": [
        "verificar pressão dos pneus",
        "desgastes dos pneus",
        "o estepe"
    ],
    "Placas": [
        "verificar condições das placas",
        "tarjetas",
        "lacre da placa"
    ],
    "Obrigatório": [
        "verificar validade do extintor",
        "verificar chave de roda",
        "macaco",
        "triângulo",
        "documentos"
    ],
    "Habitáculo": [
        "verificar bancos",
        "cintos de segurança",
        "vidro das portas",
        "para-brisa",
        "espelhos retrovisores",
        "portas-luvas",
        "fechaduras",
        "limpeza interna",
        "limpeza externa"
    ]
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

class ChecklistSubmission(BaseModel):
    items: Dict[str, Dict[str, str]]  # category -> item -> response

class ChecklistRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    user_name: str
    week_start: str  # ISO date string for the Monday of the week
    completed: bool = False
    items: Dict[str, Dict[str, str]] = {}
    submitted_at: Optional[datetime] = None

class UserDashboard(BaseModel):
    user: User
    deliveries: dict
    total_deliveries: int
    total_commission: float
    checklist_completed: bool
    current_week_start: str

class AdminUserSummary(BaseModel):
    user: User
    total_deliveries: int
    total_commission: float

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

def should_complete_checklist(user: User, week_start: str) -> bool:
    """Determine if user should complete checklist based on their assigned day and current day"""
    if user.role != "driver" or not user.assigned_day:
        return False
    
    # Driver must complete checklist once their assigned day has passed in the current week
    today = datetime.now(timezone.utc)
    current_day_index = today.weekday()  # 0=Monday, 1=Tuesday, 2=Wednesday, 3=Thursday, 4=Friday, 5=Saturday, 6=Sunday
    
    # Map assigned days to indices
    day_map = {
        "Monday": 0,
        "Tuesday": 1,
        "Wednesday": 2,
        "Thursday": 3,
        "Friday": 4,
        "Saturday": 5,
        "Sunday": 6
    }
    
    assigned_day_index = day_map.get(user.assigned_day, -1)
    if assigned_day_index == -1:
        return False
    
    # If today is on or after the assigned day in the current week, checklist is required
    return current_day_index >= assigned_day_index

def can_fill_checklist(user: User) -> bool:
    """Check if the driver can fill the checklist today.
    
    Alteração: agora permite que o motorista preencha o check-list no **dia atribuído ou em qualquer dia posterior da mesma semana**.
    Ou seja: se ele esqueceu no dia dele, pode preencher nos dias seguintes daquela semana.
    """
    if user.role != "driver" or not user.assigned_day:
        return False

    today = datetime.now(timezone.utc)
    current_day_index = today.weekday()

    day_map = {
        "Monday": 0,
        "Tuesday": 1,
        "Wednesday": 2,
        "Thursday": 3,
        "Friday": 4,
        "Saturday": 5,
        "Sunday": 6
    }

    assigned_day_index = day_map.get(user.assigned_day, -1)
    if assigned_day_index == -1:
        return False

    # Allow filling on the assigned day or any day after it within the same week
    return current_day_index >= assigned_day_index

def is_special_member(employee_name: Optional[str]) -> bool:
    if not employee_name:
        return False
    return employee_name.strip().lower() == "valdiney"

def get_tier_percentage(employee_id: str, occurrence_counts: Dict[str, int], employee_name: Optional[str] = None) -> float:
    """Calcula percentual por tier de ocorrências.

    Regras padrão:
    - Mais ocorrências: 0.8%
    - Ocorrências medianas: 0.9%
    - Menos ocorrências: 1.0%
    - Se todos tiverem 0 ocorrências: 1.0% para todos

    Regras especiais Valdiney:
    - Faixa entre 2.0% e 2.5%
    - Pior cenário: 2.0%
    - Médio: 2.25%
    - Melhor cenário: 2.5%
    """
    is_valdiney = is_special_member(employee_name)
    min_rate = 2.0 if is_valdiney else 0.8
    mid_rate = 2.25 if is_valdiney else 0.9
    max_rate = 2.5 if is_valdiney else 1.0

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

async def check_checklist_completed(user_id: str, week_start: str) -> bool:
    """Check if user has completed checklist for the current week"""
    checklist = await db.checklists.find_one({
        "user_id": user_id,
        "week_start": week_start,
        "completed": True
    })
    return checklist is not None

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

@api_router.get("/user/dashboard", response_model=UserDashboard)
async def get_user_dashboard(current_user: User = Depends(get_current_user)):
    commission_data = await calculate_user_commission(current_user.id)
    
    # Check if driver needs to complete checklist based on assigned day
    week_start = get_week_start()
    checklist_completed = True
    
    # Only require checklist if it's the driver's assigned day (or passed) in the week
    if should_complete_checklist(current_user, week_start):
        checklist_completed = await check_checklist_completed(current_user.id, week_start)
    
    return UserDashboard(
        user=current_user,
        deliveries=commission_data["deliveries"],
        total_deliveries=commission_data["total_deliveries"],
        total_commission=commission_data["total_commission"],
        checklist_completed=checklist_completed,
        current_week_start=week_start
    )

@api_router.get("/checklist/template")
async def get_checklist_template(current_user: User = Depends(get_current_user)):
    """Get the checklist template structure"""
    if current_user.role != "driver":
        raise HTTPException(status_code=403, detail="Only drivers can access checklist")
    
    if not current_user.assigned_day:
        raise HTTPException(status_code=400, detail="Driver not assigned to any day")
    
    # Check if today is the assigned day or after it to fill the checklist
    if not can_fill_checklist(current_user):
        raise HTTPException(
            status_code=403, 
            detail=f"Você pode preencher o check-list apenas no dia atribuído ou em dias posteriores desta semana: {current_user.assigned_day}"
        )
    
    return {
        "assigned_day": current_user.assigned_day,
        "categories": CHECKLIST_ITEMS,
        "can_fill": True
    }

@api_router.get("/checklist/current")
async def get_current_checklist(current_user: User = Depends(get_current_user)):
    """Get current week's checklist for the user"""
    if current_user.role != "driver":
        raise HTTPException(status_code=403, detail="Only drivers can access checklist")
    
    week_start = get_week_start()
    checklist = await db.checklists.find_one({
        "user_id": current_user.id,
        "week_start": week_start
    }, {"_id": 0})
    
    if not checklist:
        # Create new checklist for this week
        new_checklist = ChecklistRecord(
            user_id=current_user.id,
            user_name=current_user.name,
            week_start=week_start,
            completed=False,
            items={}
        )
        checklist_doc = new_checklist.model_dump()
        await db.checklists.insert_one(checklist_doc)
        return new_checklist
    
    return ChecklistRecord(**checklist)

@api_router.post("/checklist/submit")
async def submit_checklist(submission: ChecklistSubmission, current_user: User = Depends(get_current_user)):
    """Submit completed checklist"""
    if current_user.role != "driver":
        raise HTTPException(status_code=403, detail="Only drivers can submit checklist")
    
    # Check if today is the assigned day or after it
    if not can_fill_checklist(current_user):
        raise HTTPException(
            status_code=403, 
            detail=f"Você só pode submeter o check-list no dia atribuído ou em dias posteriores desta semana: {current_user.assigned_day}"
        )
    
    week_start = get_week_start()
    
    # Validate all items are filled
    for category, items in CHECKLIST_ITEMS.items():
        if category not in submission.items:
            raise HTTPException(status_code=400, detail=f"Category '{category}' is missing")
        for item in items:
            if item not in submission.items[category] or not submission.items[category][item]:
                raise HTTPException(status_code=400, detail=f"Item '{item}' in category '{category}' is not filled")
    
    # Update or create checklist
    existing = await db.checklists.find_one({
        "user_id": current_user.id,
        "week_start": week_start
    })
    
    if existing:
        await db.checklists.update_one(
            {"id": existing['id']},
            {"$set": {
                "items": submission.items,
                "completed": True,
                "submitted_at": datetime.now(timezone.utc).isoformat()
            }}
        )
    else:
        checklist = ChecklistRecord(
            user_id=current_user.id,
            user_name=current_user.name,
            week_start=week_start,
            completed=True,
            items=submission.items,
            submitted_at=datetime.now(timezone.utc)
        )
        checklist_doc = checklist.model_dump()
        checklist_doc['submitted_at'] = checklist_doc['submitted_at'].isoformat()
        await db.checklists.insert_one(checklist_doc)
    
    return {"message": "Checklist submitted successfully", "completed": True}

@api_router.get("/admin/checklists")
async def get_all_checklists(admin: User = Depends(get_admin_user)):
    """Admin endpoint to view all checklists"""
    checklists = await db.checklists.find({}, {"_id": 0}).sort("week_start", -1).to_list(1000)
    return checklists

@api_router.get("/admin/checklists/week/{week_start}")
async def get_checklists_by_week(week_start: str, admin: User = Depends(get_admin_user)):
    """Admin endpoint to view checklists for a specific week"""
    checklists = await db.checklists.find({"week_start": week_start}, {"_id": 0}).to_list(100)
    return checklists

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
    return {
        "success": True,
        "delivery": delivery,
        "inserted_id": str(result.inserted_id)
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

    occurrence_counts = await get_occurrence_count_map()
    
    result = []
    for user_data in users:
        user_id = user_data["id"]
        
        # Busca entregas
        deliveries = await db.deliveries.find({"employee_id": user_id}, {"_id": 0}).to_list(1000)
        total_delivered = sum(d.get("value", 0) for d in deliveries)
        
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
        percentage = get_tier_percentage(user_id, occurrence_counts, user_data.get("name"))
        
        # Calcula valor a receber (percentual de comissão)
        value_to_receive = total_delivered * (percentage / 100)
        
        logger.info(f"  👤 {user_data['name']}: {len(deliveries)} entregas (R${total_delivered:.2f}), {occurrence_count} ocorrências, {percentage:.1f}% comissão")
        
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
            "total_delivered_value": round(total_delivered, 2),
            "value_to_receive": round(value_to_receive, 2),
            "by_truck": by_truck,
            "statistics": {
                "occurrence_count": occurrence_count,
                "percentage": percentage
            }
        })
    
    return result

@api_router.get("/employees/{employee_id}")
async def get_employee_summary(employee_id: str):
    """Retorna resumo de entrega de um motorista"""
    # Busca entregas
    deliveries = await db.deliveries.find({"employee_id": employee_id}, {"_id": 0}).to_list(1000)
    total_delivered = sum(d.get("value", 0) for d in deliveries)
    
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
    occurrence_count = len(occurrences)

    # Calcula percentual por tier (comparando com todos os membros)
    occurrence_counts = await get_occurrence_count_map()
    percentage = get_tier_percentage(employee_id, occurrence_counts, user_name)
    
    # Calcula valor a receber (percentual de comissão)
    value_to_receive = total_delivered * (percentage / 100)
    
    return {
        "employee_id": employee_id,
        "name": user_name,
        "total_delivered_value": round(total_delivered, 2),
        "value_to_receive": round(value_to_receive, 2),
        "by_truck": by_truck,
        "occurrence_count": occurrence_count,
        "percentage": percentage,
        "occurrences": occurrences
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
