# src/work_time_prediction/api/__init__.py
# Router principal de l'API

from fastapi import APIRouter

from work_time_prediction.api.status import router as status_router
from work_time_prediction.api.train import router as train_router
from work_time_prediction.api.predict import router as predict_router

# Création du routeur principal
router = APIRouter()

# Inclusion des sous-routeurs
router.include_router(status_router, tags=["Status"])
router.include_router(train_router, tags=["Training"])
router.include_router(predict_router, tags=["Predictions"])

__all__ = ["router"]
