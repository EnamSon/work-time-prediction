-- schemas/tables.sql
-- Schéma des tables de l'application

-- ============================================================================
-- Table des sessions utilisateur
-- ============================================================================
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    ip_address TEXT NOT NULL,
    created_at TEXT NOT NULL,
    last_accessed TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    metadata TEXT DEFAULT '{}'
);

-- ============================================================================
-- Table des quotas par IP
-- ============================================================================
CREATE TABLE IF NOT EXISTS ip_quotas (
    ip_address TEXT PRIMARY KEY,
    models_count INTEGER DEFAULT 0,
    storage_used_mb REAL DEFAULT 0.0,
    requests_count INTEGER DEFAULT 0,
    train_count INTEGER DEFAULT 0,
    predictions_count INTEGER DEFAULT 0,
    violations_count INTEGER DEFAULT 0,
    is_banned INTEGER DEFAULT 0,
    banned_until TEXT,
    last_reset TEXT NOT NULL,
    created_at TEXT NOT NULL
);

-- ============================================================================
-- Table des logs de sécurité
-- ============================================================================
CREATE TABLE IF NOT EXISTS security_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    ip_address TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_data TEXT,
    severity TEXT DEFAULT 'INFO',
    created_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
);
