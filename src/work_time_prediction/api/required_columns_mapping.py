# src/work_time_prediction/api/column_config.py
# Endpoint de configuration des colonnes du csv

from fastapi import APIRouter
from work_time_prediction.models.required_columns_mapping_request import RequiredColumnsMappingRequest
from work_time_prediction.core.required_columns import required_columns

router = APIRouter()

@router.post("/required_columns_mapping/")
async def required_columns_mapping(request: RequiredColumnsMappingRequest):
    required_columns.id = request.id
    required_columns.date = request.date
    required_columns.start = request.start
    required_columns.end = request.end

    return {
        "detail": "success"
    }
