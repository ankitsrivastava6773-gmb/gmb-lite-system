# database/client_loader.py
from database.supabase import supabase

def load_client_data(client_id: str):
    client = (
        supabase
        .table("clients")
        .select("* , client_types(*)")
        .eq("id", client_id)
        .single()
        .execute()
        .data
    )

    if not client:
        return None

    ctype = client.get("client_types") or {}

    return {
        "product": client.get("products_services"),
        "area": client.get("area"),
        "contexts": (
            client.get("context")
            or ctype.get("context")
            or []
        ),
        "trust_signals": (
            client.get("trust_signals")
            or ctype.get("trust_signals")
            or []
        ),
        "seo_keywords": (
            client.get("seo_keywords")
            or ctype.get("seo_keywords")
            or []
        ),
        "industry": ctype.get("type_name")
    }