from pydantic import BaseModel

class ClientType(BaseModel):
    type_name: str
    prefilled_context: str
    trust_signals: str
    seo_keywords: str