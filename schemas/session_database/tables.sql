-- ============================================================================
-- Table des données d'entraînement (par session)
-- ============================================================================
-- Note: Cette table est créée dynamiquement dans chaque fichier data.db
-- de session avec le nom SCHEDULE_TABLE_NAME
CREATE TABLE IF NOT EXISTS schedule_data (
    id TEXT NOT NULL,
    date TEXT NOT NULL,
    start_time_by_minutes INTEGER NOT NULL,
    end_time_by_minutes INTEGER NOT NULL,
    PRIMARY KEY (id, date)
);