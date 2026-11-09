#!/usr/bin/env python3
"""Instalador del motor de construcciones (Windows, Linux y macOS). Funciona SIN conexión.

Uso (desde cualquier carpeta):
    python instalar.py              -> comprueba, instala lo que falte y hace una prueba
    python instalar.py --comprobar  -> solo comprueba, no instala nada
    python instalar.py --sin-prueba -> instala sin generar la casa de prueba

Qué instala:
  wheels/              nbtlib (Python puro, incluido en el repositorio)
  vendor/schematica/   base de diseño (Schematica) + catálogo de bloques 26.1
  assets/              texturas de bloques (vistas previas)

En ESTE repositorio público vendor/ y assets/ NO se incluyen (Schematica no declara licencia y las
texturas son de Mojang): la primera vez, el instalador los DESCARGA con git en tu equipo (hace falta
git e internet solo en ese momento). Si ya tienes una copia completa del paquete (vendor/ y assets/
dentro), funciona sin conexión. Solo se usa internet para numpy/Pillow si faltan y no hay wheels.
"""
from __future__ import annotations

import argparse
import importlib
import os
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
WHEELS = BASE / "wheels"
REQUISITOS = {            # módulo importable -> paquete pip
    "numpy": "numpy",
    "PIL": "pillow",
    "nbtlib": "nbtlib",
}
DATOS = {
    "Schematica": BASE / "vendor" / "schematica" / "scripts" / "schematica" / "blocks" / "registry.py",
    "Catálogo de bloques 26.1": BASE / "vendor" / "schematica" / "minecraft_data" / "data" / "pc" / "26.1" / "blocks.json",
    "Texturas de bloques": BASE / "assets" / "mca" / "data" / "1.21.11" / "blocks" / "stone.png",
}


SCHEMATICA_URL = "https://github.com/tester2024/schematica"
SCHEMATICA_COMMIT = "7385534148d04e173e03fac9f45f2573020cb0c0"       # fijado: no cambia aunque el repo se actualice
ASSETS_URL = "https://github.com/PrismarineJS/minecraft-assets"
ASSETS_RUTA = "data/1.21.11/blocks"
CATALOGO = "26.1"


def ok(msg):
    print(f"  [OK] {msg}")


def mal(msg):
    print(f"  [FALTA] {msg}")


def pip_install(paquete: str, offline: bool) -> bool:
    """Instala con pip probando las variantes que exigen algunos sistemas (venv, --user, Debian/Ubuntu)."""
    base = [sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "-q"]
    origen = ["--no-index", "--find-links", str(WHEELS)] if offline else ["--find-links", str(WHEELS)]
    for extra in ([], ["--user"], ["--break-system-packages"], ["--user", "--break-system-packages"]):
        r = subprocess.run(base + origen + extra + [paquete], capture_output=True, text=True)
        if r.returncode == 0:
            return True
        if "externally-managed" not in (r.stderr + r.stdout) and "--user" not in extra and extra:
            break
    return False


def disponible(modulo: str) -> bool:
    # si pip instaló en la carpeta de usuario y esa carpeta no existía al arrancar, añadirla a la ruta
    import site
    try:
        usuario = site.getusersitepackages()
        if usuario and os.path.isdir(usuario) and usuario not in sys.path:
            site.addsitedir(usuario)
    except Exception:
        pass
    importlib.invalidate_caches()
    try:
        importlib.import_module(modulo)
        return True
    except Exception:
        return False


def comprobar_python() -> bool:
    v = sys.version_info
    if v < (3, 10):
        mal(f"Python {v.major}.{v.minor}: hace falta 3.10 o superior")
        return False
    ok(f"Python {v.major}.{v.minor}.{v.micro} ({sys.executable})")
    return True


def dependencias(instalar: bool) -> bool:
    todo = True
    for modulo, paquete in REQUISITOS.items():
        if disponible(modulo):
            ok(f"{paquete}")
            continue
        if not instalar:
            mal(paquete)
            todo = False
            continue
        hay_wheel = any(WHEELS.glob(f"{paquete}-*.whl")) or any(WHEELS.glob(f"{paquete.capitalize()}-*.whl"))
        print(f"  ... instalando {paquete} ({'desde wheels/, sin conexión' if hay_wheel else 'desde internet'})")
        if pip_install(paquete, offline=hay_wheel) and disponible(modulo):
            ok(f"{paquete} instalado")
        else:
            mal(f"{paquete}: no se pudo instalar."
                + ("" if hay_wheel else f" Sin conexión: copia un .whl de {paquete} para tu sistema en wheels/ "
                   f"o instálalo a mano con: {Path(sys.executable).name} -m pip install {paquete}"))
            todo = False
    return todo


def datos(silencioso: bool = False) -> bool:
    todo = True
    for nombre, ruta in DATOS.items():
        if ruta.exists():
            if not silencioso:
                ok(nombre)
        else:
            if not silencioso:
                mal(f"{nombre} (no está {ruta.relative_to(BASE)}): ejecuta de nuevo con internet y git "
                    "(se descarga solo) o usa un paquete completo")
            todo = False
    return todo


def _git(*args, cwd=None) -> bool:
    r = subprocess.run(["git", *args], capture_output=True, text=True, cwd=cwd)
    if r.returncode != 0:
        print("    git", " ".join(args[:2]), "->", (r.stderr or r.stdout).strip()[-300:])
    return r.returncode == 0


def descargar_datos() -> None:
    """Descarga lo que falte (solo si git está disponible). Pensado para el repositorio público."""
    schem = BASE / "vendor" / "schematica"
    scripts = schem / "scripts"
    if not (scripts / "schematica" / "blocks" / "registry.py").exists():
        print("  ... descargando Schematica (git clone, commit fijado)")
        if _git("clone", "-q", SCHEMATICA_URL, str(schem)):
            _git("checkout", "-q", SCHEMATICA_COMMIT, cwd=str(schem))
    if (scripts / "schematica").exists() and not DATOS["Catálogo de bloques 26.1"].exists():
        print(f"  ... descargando el catálogo de bloques {CATALOGO}")
        env = dict(os.environ, PYTHONPATH=str(scripts), PYTHONIOENCODING="utf-8")
        r = subprocess.run([sys.executable, "-m", "schematica.blocks.download", CATALOGO],
                           capture_output=True, text=True, cwd=str(scripts), env=env)
        if r.returncode != 0:
            print("    ", (r.stderr or r.stdout).strip()[-300:])
    mca = BASE / "assets" / "mca"
    if not DATOS["Texturas de bloques"].exists():
        print("  ... descargando las texturas (git sparse checkout)")
        if _git("clone", "-q", "--depth", "1", "--filter=blob:none", "--sparse", ASSETS_URL, str(mca)):
            _git("sparse-checkout", "set", ASSETS_RUTA, cwd=str(mca))


def prueba() -> bool:
    print("  ... generando la casa de prueba")
    env = dict(os.environ, PYTHONIOENCODING="utf-8", MOTOR_BASE=str(BASE))
    r = subprocess.run([sys.executable, str(BASE / "builds" / "casa_prueba.py")], capture_output=True, text=True,
                       env=env, cwd=str(BASE))
    salida = BASE / "salidas" / "casa_prueba"
    if r.returncode != 0 or not (salida / "casa_prueba.schem").exists():
        mal("la prueba falló:")
        print((r.stdout or "")[-1500:], (r.stderr or "")[-3000:])
        return False
    ok(f"casa de prueba generada en {salida}")
    return True


def main():
    ap = argparse.ArgumentParser(description="Instalador del motor de construcciones (offline)")
    ap.add_argument("--comprobar", action="store_true", help="solo comprobar, no instalar")
    ap.add_argument("--sin-prueba", action="store_true", help="no generar la casa de prueba")
    ap.add_argument("--sin-descarga", action="store_true", help="no descargar Schematica/texturas si faltan")
    a = ap.parse_args()

    print(f"Motor de construcciones en: {BASE}\n")
    print("1) Python")
    if not comprobar_python():
        sys.exit(1)
    print("2) Dependencias (numpy, Pillow, nbtlib)")
    dep_ok = dependencias(instalar=not a.comprobar)
    print("3) Datos (Schematica, catálogo de bloques, texturas)")
    dat_ok = datos(silencioso=True)
    if not dat_ok and not a.comprobar and not a.sin_descarga:
        descargar_datos()
    dat_ok = datos()
    (BASE / "salidas").mkdir(exist_ok=True)
    pr_ok = True
    if dep_ok and dat_ok and not a.sin_prueba:
        print("4) Prueba")
        pr_ok = prueba()
    print()
    if dep_ok and dat_ok and pr_ok:
        print("LISTO. Uso: python builds/casa_prueba.py  (o importa motor, lienzo, decor... desde esta carpeta).")
        print("Los .schem se generan en salidas/.")
    else:
        print("Hay pasos pendientes (mira los [FALTA] de arriba).")
        sys.exit(1)


if __name__ == "__main__":
    main()
