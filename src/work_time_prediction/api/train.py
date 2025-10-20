# Route d'entraînement du modèle avec gestion de session

from fastapi import APIRouter, UploadFile, File, HTTPException, Header
from typing import Optional
import io

from work_time_prediction.core.database import load_data_from_csv, save_data_to_db
from work_time_prediction.core.train_models import train_models
from work_time_prediction.core.exceptions import InvalidCsvFormatError, NoDataFoundError
from work_time_prediction.core.session_manager import session_manager


router = APIRouter()


@router.post("/train/")
async def train_model(
    file: UploadFile = File(...),
    session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    """
    Upload un CSV, entraîne le modèle et sauvegarde dans la session.
    
    Args:
        file: Fichier CSV contenant les données d'entraînement
        session_id: ID de session (optionnel, en créera un si absent)
    
    Returns:
        dict: Résultat de l'entraînement avec session_id
    """
    # Vérifier/créer la session
    if not session_id:
        raise HTTPException(
            status_code=400, 
            detail="Session ID manquant. Créez d'abord une session via POST /api/session/create"
        )
    
    # Valider la session
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session invalide ou expirée")

    try:
        # Lire le contenu du fichier
        contents = await file.read()
        csv_data = io.StringIO(contents.decode('utf-8'))
        
        # Charger et traiter les données
        df = load_data_from_csv(csv_data)
        
        if df.empty:
            raise InvalidCsvFormatError("Le fichier CSV ne contient aucune donnée valide après nettoyage")
        
        # Sauvegarder dans la DB de la session (pas la DB globale)
        save_data_to_db(df)
        
        # Entraîner les modèles
        data_row_count = train_models()
        
        # Sauvegarder le modèle dans la session
        session_manager.save_model(session_id, data_row_count)
        
        return {
            "message": "Modèle entraîné et sauvegardé avec succès",
            "session_id": session_id,
            "data_points": data_row_count,
            "employees": len(df['Employee_ID'].unique())
        }
    
    except InvalidCsvFormatError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    except NoDataFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'entraînement: {str(e)}")