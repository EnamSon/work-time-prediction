# src/work_time_prediction/api/__init__.py
# Router principal de l'API

from fastapi import APIRouter

from work_time_prediction.api.status import router as status_router
from work_time_prediction.api.train import router as train_router
from work_time_prediction.api.predict import router as predict_router
from work_time_prediction.api.required_columns_mapping import router as router_required_cols_mapping
# Création du routeur principal
router = APIRouter()

# Inclusion des sous-routeurs
router.include_router(status_router, tags=["Status"])
router.include_router(train_router, tags=["Training"])
router.include_router(predict_router, tags=["Predictions"])
router.include_router(router_required_cols_mapping, tags=["Required Columns Mapping"])

__all__ = ["router"]
