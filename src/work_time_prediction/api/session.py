# Routes API pour la gestion des sessions

from fastapi import APIRouter, HTTPException, Request, Header

from work_time_prediction.core.session_manager import session_manager
from work_time_prediction.models.Session_create_response import SessionCreateResponse
from work_time_prediction.models.Session_info_response import SessionInfoResponse

router = APIRouter(prefix="/session")

@router.post("/create/", response_model=SessionCreateResponse)
@router.post("/create", response_model=SessionCreateResponse)
async def create_session(request: Request):
    """
    Crée une nouvelle session pour l'utilisateur.
    
    Returns:
        SessionCreateResponse: ID de session et message de confirmation
    """
    # Récupérer l'IP du client
    client_ip = request.client.host if request.client else "unknown"
    
    try:
        session_id = session_manager.create_session(
            ip_address=client_ip,
            metadata={"user_agent": request.headers.get("user-agent", "unknown")}
        )
        
        return SessionCreateResponse(
            session_id=session_id,
            message="Session créée avec succès. Utilisez ce session_id pour vos requêtes."
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la création de la session: {str(e)}")


@router.get("/info/", response_model=SessionInfoResponse)
@router.get("/info", response_model=SessionInfoResponse)
async def get_session_info(session_id: str = Header(..., alias="X-Session-ID")):
    """
    Récupère les informations d'une session.
    
    Args:
        session_id: ID de session (passé dans le header X-Session-ID)
    
    Returns:
        SessionInfoResponse: Informations détaillées sur la session
    """
    session = session_manager.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session non trouvée ou expirée")
    
    # Vérifier si un modèle est entraîné
    model_trained = session_manager.load_model(session_id)

    return SessionInfoResponse(
        session_id=session["session_id"],
        model_id=session["model_id"],
        created_at=session["created_at"],
        last_accessed=session["last_accessed"],
        expires_at=session["expires_at"],
        is_model_trained=model_trained.is_trained if model_trained else False,
        ids_count=len(model_trained.id_map) if model_trained else 0
    )


@router.delete("/delete/")
@router.delete("/delete")
async def delete_session(session_id: str = Header(..., alias="X-Session-ID")):
    """
    Supprime une session et toutes ses données associées.
    
    Args:
        session_id: ID de session (passé dans le header X-Session-ID)
    
    Returns:
        dict: Message de confirmation
    """
    session = session_manager.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session non trouvée")
    
    try:
        session_manager.delete_session(session_id)
        return {"message": "Session supprimée avec succès"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression: {str(e)}")

@router.get("/list/")
@router.get("/list")
async def list_user_sessions(request: Request):
    """
    Liste toutes les sessions actives de l'utilisateur actuel.
    
    Returns:
        dict: Liste des sessions
    """
    client_ip = request.client.host if request.client else "unknown"
    
    sessions = session_manager.get_user_sessions(client_ip)
    
    return {
        "count": len(sessions),
        "sessions": sessions
    }


@router.post("/cleanup/")
@router.post("/cleanup")
async def cleanup_expired():
    """
    Nettoie toutes les sessions expirées (endpoint admin).
    
    Returns:
        dict: Message de confirmation
    """
    try:
        session_manager.cleanup_expired_sessions()
        return {"message": "Nettoyage des sessions expirées effectué"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du nettoyage: {str(e)}")