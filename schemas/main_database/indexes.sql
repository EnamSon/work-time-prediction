-- schemas/indexes.sql
-- Index pour optimiser les performances

-- ============================================================================
-- Index sur la table sessions
-- ============================================================================

-- Index pour rechercher par IP (utilisé dans list sessions)
CREATE INDEX IF NOT EXISTS idx_sessions_ip_address 
ON sessions(ip_address);

-- Index pour le nettoyage des sessions expirées
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at 
ON sessions(expires_at);

-- Index composite pour les requêtes filtrées par IP et expiration
CREATE INDEX IF NOT EXISTS idx_sessions_ip_expires 
ON sessions(ip_address, expires_at);

-- Index pour trier par date d'accès
CREATE INDEX IF NOT EXISTS idx_sessions_last_accessed 
ON sessions(last_accessed DESC);

-- ============================================================================
-- Index sur la table ip_quotas
-- ============================================================================

-- Index pour les IPs bannies
CREATE INDEX IF NOT EXISTS idx_ip_quotas_is_banned 
ON ip_quotas(is_banned);

-- Index pour nettoyer les bannissements expirés
CREATE INDEX IF NOT EXISTS idx_ip_quotas_banned_until 
ON ip_quotas(banned_until);

-- ============================================================================
-- Index sur la table security_logs
-- ============================================================================

-- Index pour rechercher par session
CREATE INDEX IF NOT EXISTS idx_security_logs_session_id 
ON security_logs(session_id);

-- Index pour rechercher par IP
CREATE INDEX IF NOT EXISTS idx_security_logs_ip_address 
ON security_logs(ip_address);

-- Index pour rechercher par type d'événement
CREATE INDEX IF NOT EXISTS idx_security_logs_event_type 
ON security_logs(event_type);

-- Index pour rechercher par sévérité
CREATE INDEX IF NOT EXISTS idx_security_logs_severity 
ON security_logs(severity);

-- Index pour trier par date
CREATE INDEX IF NOT EXISTS idx_security_logs_created_at 
ON security_logs(created_at DESC);

-- Index composite pour les requêtes de logs récents par IP
CREATE INDEX IF NOT EXISTS idx_security_logs_ip_date 
ON security_logs(ip_address, created_at DESC);
