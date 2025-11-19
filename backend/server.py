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

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

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
        "diro da direção",
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
    user_id: str
    truck_type: str
    delivery_count: int = 0
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DeliveryUpdate(BaseModel):
    user_id: str
    truck_type: str
    delivery_count: int

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

@api_router.get("/admin/users", response_model=List[AdminUserSummary])
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

@api_router.post("/admin/delivery")
async def update_delivery(delivery_update: DeliveryUpdate, admin: User = Depends(get_admin_user)):
    # Validate truck type
    if delivery_update.truck_type not in TRUCK_RATES:
        raise HTTPException(status_code=400, detail="Invalid truck type")
    
    # Check if user exists
    user = await db.users.find_one({"id": delivery_update.user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update or create delivery record
    existing = await db.deliveries.find_one({
        "user_id": delivery_update.user_id,
        "truck_type": delivery_update.truck_type
    })
    
    if existing:
        await db.deliveries.update_one(
            {"id": existing['id']},
            {"$set": {
                "delivery_count": delivery_update.delivery_count,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
    else:
        delivery = DeliveryRecord(
            user_id=delivery_update.user_id,
            truck_type=delivery_update.truck_type,
            delivery_count=delivery_update.delivery_count
        )
        delivery_doc = delivery.model_dump()
        delivery_doc['updated_at'] = delivery_doc['updated_at'].isoformat()
        await db.deliveries.insert_one(delivery_doc)
    
    return {"message": "Delivery updated successfully"}

@api_router.get("/admin/user/{user_id}/deliveries")
async def get_user_deliveries(user_id: str, admin: User = Depends(get_admin_user)):
    deliveries = await db.deliveries.find({"user_id": user_id}, {"_id": 0}).to_list(100)
    return deliveries

app.include_router(api_router)

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
