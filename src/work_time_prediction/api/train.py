# src/work_time_prediction/api/train.py
# Endpoint d'entraînement des modèles ML

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import io

from work_time_prediction.core.database import load_data_from_csv, save_data_to_db
from work_time_prediction.core.train_models import train_models
from work_time_prediction.core.exceptions import (
    InvalidCsvFormatError, 
    NoDataFoundError
)

router = APIRouter()


@router.post("/train/")
async def train_model_endpoint(file: UploadFile = File(...)):
    """
    Upload un fichier CSV, stocke les données dans la base de données 
    et entraîne les modèles ML.
    
    Args:
        file: Fichier CSV contenant les données d'entraînement
        
    Returns:
        Réponse JSON avec le statut, message et nombre de points de données
        
    Raises:
        HTTPException: En cas d'erreur de format, de base de données ou d'entraînement
    """
    
    # 1. Lecture et prétraitement du fichier
    try:
        contents = await file.read()
        csv_data = io.StringIO(contents.decode('utf-8'))
        df_processed = load_data_from_csv(csv_data)
        
    except InvalidCsvFormatError as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Erreur de format de fichier: {e}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur interne lors de la lecture du fichier: {e}"
        )

    # 2. Sauvegarde dans la base de données
    try:
        save_data_to_db(df_processed)
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur lors de la sauvegarde dans la base de données: {e}"
        )

    # 3. Entraînement des modèles
    try:
        data_points = train_models()
        
        return JSONResponse({
            "status": "success", 
            "message": "Modèles d'arrivée et de départ entraînés et prêts.", 
            "data_points": data_points
        })
        
    except NoDataFoundError as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur d'entraînement : {e}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur interne lors de l'entraînement ML: {e}"
        )
