from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
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

class UserDashboard(BaseModel):
    user: User
    deliveries: dict
    total_deliveries: int
    total_commission: float

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
    
    # Create user
    user = User(
        username=user_data.username,
        name=user_data.name,
        role=user_data.role
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
    return UserDashboard(
        user=current_user,
        deliveries=commission_data["deliveries"],
        total_deliveries=commission_data["total_deliveries"],
        total_commission=commission_data["total_commission"]
    )

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