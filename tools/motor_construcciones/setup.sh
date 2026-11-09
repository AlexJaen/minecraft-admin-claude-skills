#!/usr/bin/env bash
# Instala el motor de construcciones: dependencias, Schematica (fijada a un commit), catálogo de bloques y texturas.
# Uso: bash setup.sh            (desde la carpeta motor_construcciones)
set -e
cd "$(dirname "$0")"
PIP="pip install -q"
$PIP numpy nbtlib shapely trimesh matplotlib pillow scipy prompt_toolkit 2>/dev/null \
  || $PIP --break-system-packages numpy nbtlib shapely trimesh matplotlib pillow scipy prompt_toolkit
# noise es opcional (solo lo usa el generador de terreno de Schematica)
$PIP noise 2>/dev/null || $PIP --break-system-packages noise 2>/dev/null || echo "(aviso) 'noise' no instalado: opcional, solo para terreno"

mkdir -p vendor assets salidas
if [ ! -d vendor/schematica ]; then
  git clone -q https://github.com/tester2024/schematica vendor/schematica
  git -C vendor/schematica checkout -q 7385534148d04e173e03fac9f45f2573020cb0c0
fi
if [ ! -d assets/mca ]; then
  git clone -q --depth 1 --filter=blob:none --sparse https://github.com/PrismarineJS/minecraft-assets assets/mca
  git -C assets/mca sparse-checkout set data/1.21.11/blocks
fi
( cd vendor/schematica/scripts && python3 -m schematica.blocks.download 26.1 >/dev/null )
python3 prueba_instalacion.py
