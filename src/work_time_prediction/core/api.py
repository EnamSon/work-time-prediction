# Définition des endpoints API (Router FastAPI)

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
import io
import pandas as pd
from typing import List

from work_time_prediction.models.predict_request import PredictionRequest
from work_time_prediction.models.predict_response import PredictionResponse, PredictedDay
from work_time_prediction.core.database import load_data_from_csv, save_data_to_db
from work_time_prediction.core.predictions import train_models, generate_predictions, ml_state
from work_time_prediction.core.exceptions import (
    ModelNotTrainedError, EmployeeNotFoundError, InvalidCsvFormatError, NoDataFoundError
)

# Création du routeur FastAPI
router = APIRouter()

@router.get("/")
async def status_check():
    """Endpoint de statut pour vérifier si le service est en ligne et entraîné."""
    return {
        "message": "Service de Prédiction d'Horaires - API en ligne", 
        "is_trained": ml_state.is_trained
    }

@router.post("/train/")
async def train_model_endpoint(file: UploadFile = File(...)):
    """
    Uploade le CSV, stocke les données dans la DB et entraîne les modèles ML.
    """
    
    # 1. Lecture et prétraitement du fichier
    try:
        contents = await file.read()
        csv_data = io.StringIO(contents.decode('utf-8'))
        
        df_processed = load_data_from_csv(csv_data)
        
    except InvalidCsvFormatError as e:
        raise HTTPException(status_code=400, detail=f"Erreur de format de fichier: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne lors de la lecture du fichier: {e}")


    # 2. Sauvegarde dans la base de données
    try:
        save_data_to_db(df_processed)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la sauvegarde dans la base de données: {e}")


    # 3. Entraînement des modèles
    try:
        data_points = train_models()
        
        return JSONResponse({
            "status": "success", 
            "message": "Modèles d'arrivée et de départ entraînés et prêts.", 
            "data_points": data_points
        })
        
    except NoDataFoundError as e:
        # Erreur si la DB est vide (ce qui ne devrait pas arriver après save_data)
        raise HTTPException(status_code=500, detail=f"Erreur d'entraînement : {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne lors de l'entraînement ML: {e}")


@router.post("/predict/", response_model=PredictionResponse)
async def get_predictions(request: PredictionRequest):
    """
    Prédit les horaires pour une fenêtre de dates autour de la date cible.
    """
    try:
        # Conversion et détermination de la fenêtre de prédiction
        target_date = datetime.strptime(request.target_date, '%d/%m/%Y')
        
        start_date = target_date - timedelta(days=request.window_size // 2)
        end_date = target_date + timedelta(days=request.window_size // 2)

        # Correction mypy: conversion explicite des Timestamp de pandas en datetime
        all_dates: List[datetime] = [
            d.to_pydatetime() 
            for d in pd.date_range(start=start_date, end=end_date, freq='D')
        ]

        # Génération des résultats (Historique + Prédictions) - retourne List[Dict]
        raw_results = generate_predictions(request.employee_id, all_dates)

        # Correction mypy/Pydantic: construction des objets PredictedDay
        predictions = [PredictedDay(**data) for data in raw_results]

        return PredictionResponse(predictions=predictions)

    except ModelNotTrainedError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except EmployeeNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ValueError:
        raise HTTPException(status_code=400, detail="Format de date cible invalide. Utilisez jj/mm/aaaa.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne lors de la prédiction: {e}")
