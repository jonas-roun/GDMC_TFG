# config.py
import os
from pathlib import Path

# Directorio raíz del proyecto
PROJECT_ROOT = Path(__file__).resolve().parent

# Ruta a la base de datos
BLOCKS_DB_PATH = PROJECT_ROOT / 'data/blocks.db'