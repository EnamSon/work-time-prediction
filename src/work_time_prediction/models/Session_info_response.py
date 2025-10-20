from pydantic import BaseModel

class SessionInfoResponse(BaseModel):
    """Informations sur une session."""
    session_id: str
    model_id: str
    created_at: str
    last_accessed: str
    expires_at: str
    is_model_trained: bool
    employee_count: int
