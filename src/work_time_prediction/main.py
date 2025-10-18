from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from work_time_prediction.core.api import router
import uvicorn

# Initialisation de l'application FastAPI
app = FastAPI(
    title="Work Time Prediction API",
    description="API de prédiction d'horaires des employés basée sur le Machine Learning et stockée dans SQLite."
)

# Configuration CORS pour le développement
origins = [
    "http://localhost:5173",  # Frontend React (Vite)
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "*" # À restreindre en production
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion du routeur principal contenant les endpoints
app.include_router(router, prefix="/api")

# Note: Pour lancer l'application avec Poetry, utilisez:
# uvicorn work_time_prediction.main:app --reload --app-dir src
