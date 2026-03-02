import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

try:
    import firebase_admin
    from firebase_admin import credentials, messaging
except Exception:
    firebase_admin = None
    credentials = None
    messaging = None


logger = logging.getLogger(__name__)


def _load_firebase_credentials() -> Optional[Dict[str, Any]]:
    json_payload = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
    if json_payload:
        try:
            return json.loads(json_payload)
        except json.JSONDecodeError:
            logger.error("FIREBASE_SERVICE_ACCOUNT_JSON inválido")

    file_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_FILE")
    if file_path and os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception as exc:
            logger.error("Falha ao ler FIREBASE_SERVICE_ACCOUNT_FILE: %s", exc)

    return None


def _ensure_firebase_initialized() -> bool:
    if firebase_admin is None or credentials is None:
        logger.warning("firebase-admin não instalado; push notification desabilitado")
        return False

    creds = _load_firebase_credentials()
    if not creds:
        logger.warning("Credenciais Firebase não configuradas; push notification desabilitado")
        return False

    if not firebase_admin._apps:
        cert = credentials.Certificate(creds)
        firebase_admin.initialize_app(cert)

    return True


async def register_device_token(
    db: AsyncIOMotorDatabase,
    employee_id: str,
    employee_name: str,
    role: str,
    token: str,
    platform: str,
) -> None:
    now_iso = datetime.now(timezone.utc).isoformat()
    await db.device_tokens.update_one(
        {"token": token},
        {
            "$set": {
                "employee_id": employee_id,
                "employee_name": employee_name,
                "role": role,
                "platform": platform,
                "is_active": True,
                "updated_at": now_iso,
            },
            "$setOnInsert": {
                "id": str(uuid.uuid4()),
                "created_at": now_iso,
            },
        },
        upsert=True,
    )


async def create_in_app_notification(
    db: AsyncIOMotorDatabase,
    employee_id: str,
    employee_name: str,
    title: str,
    message: str,
    notification_type: str,
    data: Optional[Dict[str, Any]] = None,
) -> None:
    await db.notifications.insert_one(
        {
            "id": str(uuid.uuid4()),
            "employee_id": employee_id,
            "employee_name": employee_name,
            "type": notification_type,
            "title": title,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "read": False,
            "data": data or {},
        }
    )


async def send_push_to_employee(
    db: AsyncIOMotorDatabase,
    employee_id: str,
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
) -> Dict[str, int]:
    token_docs = await db.device_tokens.find(
        {"employee_id": employee_id, "is_active": True},
        {"_id": 0, "token": 1},
    ).to_list(100)

    tokens: List[str] = [doc["token"] for doc in token_docs if doc.get("token")]
    if not tokens:
        return {"sent": 0, "failed": 0}

    if not _ensure_firebase_initialized():
        return {"sent": 0, "failed": len(tokens)}

    normalized_data = {k: str(v) for k, v in (data or {}).items()}

    message = messaging.MulticastMessage(
        notification=messaging.Notification(title=title, body=body),
        data=normalized_data,
        tokens=tokens,
    )

    response = messaging.send_each_for_multicast(message)

    invalid_tokens: List[str] = []
    for idx, send_response in enumerate(response.responses):
        if send_response.success:
            continue
        exc = send_response.exception
        code = getattr(exc, "code", "") if exc else ""
        if code in {
            "registration-token-not-registered",
            "invalid-argument",
            "invalid-registration-token",
        }:
            invalid_tokens.append(tokens[idx])

    if invalid_tokens:
        await db.device_tokens.update_many(
            {"token": {"$in": invalid_tokens}},
            {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc).isoformat()}},
        )

    return {
        "sent": response.success_count,
        "failed": response.failure_count,
    }


async def notify_commission_update(
    db: AsyncIOMotorDatabase,
    employee_id: str,
    employee_name: str,
    amount: float,
    percentage: Optional[float] = None,
    truck_type: Optional[str] = None,
) -> Dict[str, int]:
    details = []
    if percentage is not None:
        details.append(f"{percentage}%")
    if truck_type:
        details.append(f"caminhão {truck_type}")

    detail_text = f" ({', '.join(details)})" if details else ""
    title = "💰 Nova comissão lançada"
    body = f"Foi lançada uma comissão de R$ {amount:.2f}{detail_text}."

    await create_in_app_notification(
        db=db,
        employee_id=employee_id,
        employee_name=employee_name,
        title=title,
        message=body,
        notification_type="commission_posted",
        data={
            "amount": amount,
            "percentage": percentage if percentage is not None else "",
            "truck_type": truck_type or "",
        },
    )

    return await send_push_to_employee(
        db=db,
        employee_id=employee_id,
        title=title,
        body=body,
        data={
            "type": "commission_posted",
            "amount": amount,
            "percentage": percentage if percentage is not None else "",
            "truck_type": truck_type or "",
        },
    )