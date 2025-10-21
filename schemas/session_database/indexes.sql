-- ============================================================================
-- Index sur la table schedule_data
-- ============================================================================

-- Index pour rechercher par employé
CREATE INDEX IF NOT EXISTS idx_schedule_data_id 
ON schedule_data(id);

-- Index pour rechercher par date
CREATE INDEX IF NOT EXISTS idx_schedule_data_date 
ON schedule_data(date);