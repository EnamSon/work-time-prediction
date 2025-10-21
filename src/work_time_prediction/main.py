from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from work_time_prediction.api import router
from work_time_prediction.core.utils.folder_manager import ensure_directories_exist

# Initialisation du répertoire de travail
ensure_directories_exist()

# Initialisation de l'application FastAPI
app = FastAPI(
    title="Work Time Prediction API",
    description="API de prédiction des intervalles horaires de travail avec système de sessions."
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
    allow_origins=["*"], # A restreindre en prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion du routeur principal contenant les endpoints
app.include_router(router, prefix="/api")

@app.get("/api/")
@app.get("/api")
async def root():
    """Endpoint de vérification de l'état de l'API."""
    return {
        "status": "operational",
        "version": "0.1.0",
        "message": "Work Time Prediction API with Session Management",
        "endpoints": {
            "session": {
                "create": "POST /api/session/create",
                "info": "GET /api/session/info",
                "list": "GET /api/session/list",
                "delete": "DELETE /api/session/delete"
            },
            "training": {
                "train": "POST /api/train_models/"
            },
            "prediction": {
                "predict": "POST /api/predict/"
            }
        }
    }


def run():
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)

    args = parser.parse_args()

    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    run()

# Note: Pour lancer l'application avec Poetry, utilisez:
# uvicorn work_time_prediction.main:app --reload --app-dir src
