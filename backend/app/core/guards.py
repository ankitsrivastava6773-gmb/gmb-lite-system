from datetime import date
from fastapi import HTTPException

def check_client_status(client: dict):
    # 1️⃣ inactive check
    if not client.get("is_active"):
        raise HTTPException(
            status_code=403,
            detail="This review link is inactive"
        )

    # 2️⃣ expiry check
    end_date = client.get("end_date")
    if end_date and date.today() > date.fromisoformat(end_date):
        raise HTTPException(
            status_code=403,
            detail="This service has expired"
        )
