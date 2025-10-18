# Base de données
DB_NAME = "work_time_data.db"
TABLE_NAME = "schedule_data"

# Caractéristiques utilisées pour l'entraînement (en plus de l'ID encodé)
FEATURES = ['Employee_ID_Encoded', 'Day_of_Week', 'Day_of_Year']

# Colonnes requises pour l'entraînement
REQUIRED_COLUMNS_RAW = ['Employee ID', 'Date', 'First Punch', 'Last Punch']

# Colonnes du DataFrame après prétraitement
DF_COLS = ['Employee_ID', 'Date', 'first_punch_min', 'last_punch_min']
