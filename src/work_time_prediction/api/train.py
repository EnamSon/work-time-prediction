# Route d'entraînement du modèle avec gestion de session

from fastapi import APIRouter, UploadFile, File, HTTPException, Header, Form
import io

from work_time_prediction.core.database import load_data_from_csv, save_data_to_db
from work_time_prediction.core.train_models import train_models
from work_time_prediction.core.exceptions import InvalidCsvFormatError, NoDataFoundError
from work_time_prediction.core.session_manager import session_manager
from work_time_prediction.core.required_columns import RequiredColumnsMapping
from work_time_prediction.core.utils.folder_manager import get_model_file_path
from work_time_prediction.core.constants import MODEL_DATA_DB_FILE
router = APIRouter()


@router.post("/train/")
@router.post("/train")
async def train_model(
    file: UploadFile = File(...),
    id_column: str = Form(...),
    date_column: str = Form(...),
    start_time_column: str = Form(...),
    end_time_column: str = Form(),
    session_id: str | None = Header(None, alias="X-Session-ID"),
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
        required_columns_mapping = RequiredColumnsMapping(
            id_column, date_column, start_time_column, end_time_column
        )
        df = load_data_from_csv(csv_data, required_columns_mapping)
        
        if df.empty:
            raise InvalidCsvFormatError("Le fichier CSV ne contient aucune donnée valide après nettoyage")

        model_id = session["model_id"]
        model_data_db_path = get_model_file_path(model_id, MODEL_DATA_DB_FILE)
        # Sauvegarder dans la DB de la session (pas la DB globale)
        save_data_to_db(df, model_data_db_path)
        
        # Entraîner les modèles
        ml_state = train_models(df, model_data_db_path)
        data_row_count = len(df)
    
        # Sauvegarder le modèle dans la session
        session_manager.save_model(ml_state, session_id, data_row_count)
        
        return {
            "message": "Modèle entraîné et sauvegardé avec succès",
            "session_id": session_id,
            "data_points": data_row_count,
            "employees": len(ml_state.id_map)
        }
    
    except InvalidCsvFormatError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    except NoDataFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'entraînement: {str(e)}")