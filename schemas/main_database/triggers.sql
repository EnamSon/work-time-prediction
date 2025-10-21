-- schemas/triggers.sql
-- Triggers pour maintenir l'intégrité et automatiser les tâches

-- ============================================================================
-- Trigger : Mise à jour automatique de last_accessed
-- ============================================================================
CREATE TRIGGER IF NOT EXISTS update_session_last_accessed
AFTER UPDATE ON sessions
FOR EACH ROW
WHEN NEW.last_accessed = OLD.last_accessed
BEGIN
    UPDATE sessions 
    SET last_accessed = datetime('now')
    WHERE session_id = NEW.session_id;
END;

-- ============================================================================
-- Trigger : Log de création de session
-- ============================================================================
CREATE TRIGGER IF NOT EXISTS log_session_creation
AFTER INSERT ON sessions
FOR EACH ROW
BEGIN
    INSERT INTO security_logs (session_id, ip_address, event_type, event_data, severity, created_at)
    VALUES (
        NEW.session_id,
        NEW.ip_address,
        'session_created',
        json_object('session_id', NEW.session_id, 'expires_at', NEW.expires_at),
        'INFO',
        datetime('now')
    );
END;

-- ============================================================================
-- Trigger : Log de suppression de session
-- ============================================================================
CREATE TRIGGER IF NOT EXISTS log_session_deletion
BEFORE DELETE ON sessions
FOR EACH ROW
BEGIN
    INSERT INTO security_logs (session_id, ip_address, event_type, event_data, severity, created_at)
    VALUES (
        OLD.session_id,
        OLD.ip_address,
        'session_deleted',
        json_object(
            'session_id', OLD.session_id,
            'created_at', OLD.created_at,
            'last_accessed', OLD.last_accessed
        ),
        'INFO',
        datetime('now')
    );
END;

-- ============================================================================
-- Trigger : Initialisation des quotas IP lors de la première session
-- ============================================================================
CREATE TRIGGER IF NOT EXISTS init_ip_quotas
AFTER INSERT ON sessions
FOR EACH ROW
WHEN NOT EXISTS (SELECT 1 FROM ip_quotas WHERE ip_address = NEW.ip_address)
BEGIN
    INSERT INTO ip_quotas (
        ip_address, 
        models_count, 
        storage_used_mb, 
        requests_count, 
        train_count, 
        predictions_count, 
        violations_count, 
        is_banned, 
        last_reset, 
        created_at
    )
    VALUES (
        NEW.ip_address,
        0,
        0.0,
        0,
        0,
        0,
        0,
        0,
        datetime('now'),
        datetime('now')
    );
END;

-- ============================================================================
-- Trigger : Incrémenter le compteur de modèles par IP
-- ============================================================================
CREATE TRIGGER IF NOT EXISTS increment_models_count
AFTER INSERT ON sessions
FOR EACH ROW
BEGIN
    UPDATE ip_quotas
    SET models_count = models_count + 1
    WHERE ip_address = NEW.ip_address;
END;

-- ============================================================================
-- Trigger : Décrémenter le compteur de modèles lors de suppression
-- ============================================================================
CREATE TRIGGER IF NOT EXISTS decrement_models_count
AFTER DELETE ON sessions
FOR EACH ROW
BEGIN
    UPDATE ip_quotas
    SET models_count = CASE 
        WHEN models_count > 0 THEN models_count - 1 
        ELSE 0 
    END
    WHERE ip_address = OLD.ip_address;
END;

-- ============================================================================
-- Trigger : Validation des dates d'expiration
-- ============================================================================
CREATE TRIGGER IF NOT EXISTS validate_session_expiration
BEFORE INSERT ON sessions
FOR EACH ROW
WHEN NEW.expires_at <= datetime('now')
BEGIN
    SELECT RAISE(ABORT, 'La date d''expiration doit être dans le futur');
END;

-- ============================================================================
-- Trigger : Validation des métadonnées JSON
-- ============================================================================
CREATE TRIGGER IF NOT EXISTS validate_session_metadata
BEFORE INSERT ON sessions
FOR EACH ROW
WHEN NEW.metadata IS NOT NULL AND json_valid(NEW.metadata) = 0
BEGIN
    SELECT RAISE(ABORT, 'Les métadonnées doivent être au format JSON valide');
END;

-- ============================================================================
-- Trigger : Auto-nettoyage des logs anciens (> 30 jours)
-- ============================================================================
CREATE TRIGGER IF NOT EXISTS cleanup_old_security_logs
AFTER INSERT ON security_logs
FOR EACH ROW
WHEN (SELECT COUNT(*) FROM security_logs) > 10000
BEGIN
    DELETE FROM security_logs
    WHERE created_at < datetime('now', '-30 days');
END;