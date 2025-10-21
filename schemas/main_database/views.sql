-- schemas/views.sql
-- Vues pour simplifier les requêtes courantes

-- ============================================================================
-- Vue des sessions actives
-- ============================================================================
CREATE VIEW IF NOT EXISTS active_sessions AS
SELECT 
    session_id,
    ip_address,
    created_at,
    last_accessed,
    expires_at,
    metadata,
    CAST((julianday(expires_at) - julianday('now')) AS INTEGER) as days_until_expiry,
    CAST((julianday('now') - julianday(last_accessed)) * 24 AS INTEGER) as hours_since_last_access
FROM sessions
WHERE expires_at > datetime('now')
ORDER BY last_accessed DESC;

-- ============================================================================
-- Vue des sessions expirées
-- ============================================================================
CREATE VIEW IF NOT EXISTS expired_sessions AS
SELECT 
    session_id,
    ip_address,
    created_at,
    last_accessed,
    expires_at,
    CAST((julianday('now') - julianday(expires_at)) AS INTEGER) as days_expired
FROM sessions
WHERE expires_at <= datetime('now')
ORDER BY expires_at DESC;

-- ============================================================================
-- Vue des statistiques par IP
-- ============================================================================
CREATE VIEW IF NOT EXISTS ip_statistics AS
SELECT 
    s.ip_address,
    COUNT(s.session_id) as total_sessions,
    COUNT(CASE WHEN s.expires_at > datetime('now') THEN 1 END) as active_sessions,
    COUNT(CASE WHEN s.expires_at <= datetime('now') THEN 1 END) as expired_sessions,
    MIN(s.created_at) as first_session_date,
    MAX(s.last_accessed) as last_activity_date,
    COALESCE(q.storage_used_mb, 0) as storage_used_mb,
    COALESCE(q.is_banned, 0) as is_banned
FROM sessions s
LEFT JOIN ip_quotas q ON s.ip_address = q.ip_address
GROUP BY s.ip_address;

-- ============================================================================
-- Vue des événements de sécurité récents (dernières 24h)
-- ============================================================================
CREATE VIEW IF NOT EXISTS recent_security_events AS
SELECT 
    id,
    session_id,
    ip_address,
    event_type,
    event_data,
    severity,
    created_at,
    CAST((julianday('now') - julianday(created_at)) * 24 * 60 AS INTEGER) as minutes_ago
FROM security_logs
WHERE created_at > datetime('now', '-24 hours')
ORDER BY created_at DESC;

-- ============================================================================
-- Vue des IPs suspectes (violations récentes)
-- ============================================================================
CREATE VIEW IF NOT EXISTS suspicious_ips AS
SELECT 
    ip_address,
    violations_count,
    is_banned,
    banned_until,
    requests_count,
    train_count,
    predictions_count,
    last_reset,
    CASE 
        WHEN is_banned = 1 AND banned_until > datetime('now') THEN 'BANNED'
        WHEN violations_count >= 5 THEN 'WARNING'
        ELSE 'NORMAL'
    END as status
FROM ip_quotas
WHERE violations_count > 0 OR is_banned = 1
ORDER BY violations_count DESC;

-- ============================================================================
-- Vue globale des statistiques du système
-- ============================================================================
CREATE VIEW IF NOT EXISTS system_statistics AS
SELECT 
    (SELECT COUNT(*) FROM sessions) as total_sessions,
    (SELECT COUNT(*) FROM active_sessions) as active_sessions,
    (SELECT COUNT(*) FROM expired_sessions) as expired_sessions,
    (SELECT COUNT(DISTINCT ip_address) FROM sessions) as unique_ips,
    (SELECT COUNT(*) FROM ip_quotas WHERE is_banned = 1) as banned_ips,
    (SELECT COALESCE(SUM(storage_used_mb), 0) FROM ip_quotas) as total_storage_mb,
    (SELECT COUNT(*) FROM security_logs WHERE created_at > datetime('now', '-24 hours')) as security_events_24h;