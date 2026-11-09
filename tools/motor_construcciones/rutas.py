"""Rutas del motor: todo relativo a la carpeta del paquete (o a MOTOR_BASE si se define)."""
import os
import sys
from pathlib import Path

BASE = Path(os.environ.get("MOTOR_BASE", Path(__file__).resolve().parent))
VENDOR = BASE / "vendor" / "schematica"
TEX = BASE / "assets" / "mca" / "data" / "1.21.11" / "blocks"
SALIDAS = BASE / "salidas"

for p in (str(VENDOR / "scripts"), str(BASE)):
    if p not in sys.path:
        sys.path.insert(0, p)
