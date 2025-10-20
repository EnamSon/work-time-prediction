# src/work_time_prediction/core/session_manager.py
# Gestion des sessions utilisateur et persistance des modèles

import sqlite3
import pickle
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import secrets
import hashlib

from work_time_prediction.core.constants import (
    SESSIONS_DIR, SESSIONS_DB_PATH, MODELS_DIR,
    MODEL_METADATA_FILE, MODEL_ARRIVAL_FILE, MODEL_DEPARTURE_FILE,
    MODEL_ENCODER_FILE, MODEL_DATA_DB_FILE, JWT_ALGORITHM,
    JWT_EXPIRATION_DAYS, MIN_JWT_SECRET_LENGTH
)
from work_time_prediction.core.ml_state import MLState
from work_time_prediction.core.database import get_all_data
from work_time_prediction.core.constants import SCHEDULE_TABLE_NAME
from work_time_prediction.core.utils.folder_manager import get_model_file_path

class SessionManager:
    """Gère les sessions utilisateur et la persistance des modèles."""
    
    def __init__(self):
        """Initialise le gestionnaire de sessions."""
        self._ensure_directories()
        self._init_database()
        self._ml_state: dict[str, MLState] = {}

    def _ensure_directories(self):
        """Crée les répertoires nécessaires s'ils n'existent pas."""
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
    
    def _init_database(self):
        """Initialise la base de données des sessions."""
        conn = sqlite3.connect(SESSIONS_DB_PATH)
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    model_id TEXT UNIQUE NOT NULL,
                    ip_address TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_accessed TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    metadata TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_ip_address 
                ON sessions(ip_address)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_expires_at 
                ON sessions(expires_at)
            """)
            conn.commit()
        finally:
            conn.close()
    
    def create_session(self, ip_address: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Crée une nouvelle session pour un utilisateur.
        
        Args:
            ip_address: Adresse IP du client
            metadata: Métadonnées additionnelles (optionnel)
        
        Returns:
            str: ID de session (token JWT-like)
        """
        # Générer un ID de session sécurisé
        session_id = self._generate_session_id()
        model_id = self._generate_model_id()
        
        now = datetime.now()
        expires_at = now + timedelta(days=JWT_EXPIRATION_DAYS)
        
        conn = sqlite3.connect(SESSIONS_DB_PATH)
        try:
            conn.execute("""
                INSERT INTO sessions 
                (session_id, model_id, ip_address, created_at, last_accessed, expires_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                model_id,
                ip_address,
                now.isoformat(),
                now.isoformat(),
                expires_at.isoformat(),
                json.dumps(metadata or {})
            ))
            conn.commit()
        finally:
            conn.close()
        
        # Créer le répertoire du modèle
        model_dir = MODELS_DIR / model_id
        model_dir.mkdir(parents=True, exist_ok=True)
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les informations d'une session.
        
        Args:
            session_id: ID de la session
        
        Returns:
            Dict contenant les infos de session ou None si invalide/expirée
        """
        conn = sqlite3.connect(SESSIONS_DB_PATH)
        try:
            cursor = conn.execute("""
                SELECT session_id, model_id, ip_address, created_at, 
                       last_accessed, expires_at, metadata
                FROM sessions
                WHERE session_id = ?
            """, (session_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            session_data = {
                "session_id": row[0],
                "model_id": row[1],
                "ip_address": row[2],
                "created_at": row[3],
                "last_accessed": row[4],
                "expires_at": row[5],
                "metadata": json.loads(row[6])
            }
            
            # Vérifier l'expiration
            expires_at = datetime.fromisoformat(session_data["expires_at"])
            if datetime.now() > expires_at:
                self.delete_session(session_id)
                return None
            
            # Mettre à jour le dernier accès
            conn.execute("""
                UPDATE sessions 
                SET last_accessed = ?
                WHERE session_id = ?
            """, (datetime.now().isoformat(), session_id))
            conn.commit()
            
            return session_data
            
        finally:
            conn.close()
    
    def delete_session(self, session_id: str):
        """Supprime une session et ses données associées."""
        session = self.get_session(session_id)
        if not session:
            return
        
        model_id = session["model_id"]
        
        # Supprimer les fichiers du modèle
        model_dir = MODELS_DIR / model_id
        if model_dir.exists():
            import shutil
            shutil.rmtree(model_dir)
        
        # Supprimer l'entrée de la base de données
        conn = sqlite3.connect(SESSIONS_DB_PATH)
        try:
            conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            conn.commit()
        finally:
            conn.close()
    
    def save_model(self, ml_state: MLState, session_id: str, data_row_count: int):
        """
        Sauvegarde le modèle ML actuel dans la session.
        
        Args:
            session_id: ID de la session
            data_row_count: Nombre de lignes de données utilisées pour l'entraînement
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError("Session invalide ou expirée")
        
        model_id = session["model_id"]
        
        # Sauvegarder les modèles
        with open(get_model_file_path(model_id, MODEL_ARRIVAL_FILE), 'wb') as f:
            pickle.dump(ml_state.model_start_time, f)
        
        with open(get_model_file_path(model_id, MODEL_DEPARTURE_FILE), 'wb') as f:
            pickle.dump(ml_state.model_end_time, f)
        
        with open(get_model_file_path(model_id, MODEL_ENCODER_FILE), 'wb') as f:
            pickle.dump({
                'encoder': ml_state.id_encoder,
                'id_map': ml_state.id_map
            }, f)
        
        # Sauvegarder les données
        model_data_db_path = get_model_file_path(model_id, MODEL_DATA_DB_FILE)
        df = get_all_data(model_data_db_path)
        import sqlite3
        conn = sqlite3.connect(model_data_db_path)
        try:
            df.to_sql(SCHEDULE_TABLE_NAME, conn, if_exists='replace', index=False)
        finally:
            conn.close()
        
        # Sauvegarder les métadonnées
        metadata = {
            'trained_at': datetime.now().isoformat(),
            'data_row_count': data_row_count,
            'employee_count': len(ml_state.id_map),
            'is_trained': ml_state.is_trained
        }
        
        with open(get_model_file_path(model_id, MODEL_METADATA_FILE), 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def load_model(self, session_id: str) -> MLState | None:
        """
        Charge un modèle depuis la session dans ml_state.
        
        Args:
            session_id: ID de la session
        
        Returns:
            bool: True si le chargement a réussi, False sinon
        """
        if session_id in self._ml_state:
            return self._ml_state[session_id]
        session = self.get_session(session_id)
        if not session:
            return None
        
        model_id = session["model_id"]
        
        # Vérifier que le modèle existe
        metadata_file = get_model_file_path(model_id, MODEL_METADATA_FILE)
        if not metadata_file.exists():
            return None

        ml_state = MLState()
        try:
            # Charger les modèles
            with open(get_model_file_path(model_id, MODEL_ARRIVAL_FILE), 'rb') as f:
                ml_state.model_start_time = pickle.load(f)
            
            with open(get_model_file_path(model_id, MODEL_DEPARTURE_FILE), 'rb') as f:
                ml_state.model_end_time = pickle.load(f)
            
            with open(get_model_file_path(model_id, MODEL_ENCODER_FILE), 'rb') as f:
                encoder_data = pickle.load(f)
                ml_state.id_encoder = encoder_data['encoder']
                ml_state.id_map = encoder_data['id_map']
            
            ml_state.is_trained = True

            self._ml_state[session_id] = ml_state
            return ml_state
            
        except Exception as e:
            print(f"Erreur lors du chargement du modèle: {e}")
            return None
    
    def cleanup_expired_sessions(self):
        """Nettoie les sessions expirées."""
        conn = sqlite3.connect(SESSIONS_DB_PATH)
        try:
            cursor = conn.execute("""
                SELECT session_id FROM sessions
                WHERE expires_at < ?
            """, (datetime.now().isoformat(),))
            
            expired_sessions = [row[0] for row in cursor.fetchall()]
            
            for session_id in expired_sessions:
                self.delete_session(session_id)
                
        finally:
            conn.close()
    
    def get_user_sessions(self, ip_address: str) -> list:
        """Récupère toutes les sessions actives d'une IP."""
        conn = sqlite3.connect(SESSIONS_DB_PATH)
        try:
            cursor = conn.execute("""
                SELECT session_id, model_id, created_at, last_accessed, expires_at
                FROM sessions
                WHERE ip_address = ? AND expires_at > ?
                ORDER BY last_accessed DESC
            """, (ip_address, datetime.now().isoformat()))
            
            sessions = []
            for row in cursor.fetchall():
                sessions.append({
                    "session_id": row[0],
                    "model_id": row[1],
                    "created_at": row[2],
                    "last_accessed": row[3],
                    "expires_at": row[4]
                })
            
            return sessions
            
        finally:
            conn.close()
    
    def _generate_session_id(self) -> str:
        """Génère un ID de session sécurisé."""
        # Utiliser secrets pour la cryptographie
        random_bytes = secrets.token_bytes(32)
        timestamp = str(datetime.now().timestamp()).encode()
        
        # Créer un hash SHA256
        hash_obj = hashlib.sha256(random_bytes + timestamp)
        return hash_obj.hexdigest()
    
    def _generate_model_id(self) -> str:
        """Génère un ID unique pour un modèle."""
        return secrets.token_hex(16)


# Instance globale
session_manager = SessionManager()