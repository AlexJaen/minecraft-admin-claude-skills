"""Comprueba que el motor funciona: genera una casa de prueba, exporta, relee y renderiza."""
import os, subprocess, sys
base = os.path.dirname(os.path.abspath(__file__))
r = subprocess.run([sys.executable, os.path.join(base, "builds", "casa_prueba.py")], capture_output=True, text=True)
if r.returncode != 0:
    print(r.stdout[-2000:], r.stderr[-3000:]); sys.exit("FALLO en la prueba de instalación")
ruta = os.path.join(base, "salidas", "casa_prueba")
assert os.path.exists(os.path.join(ruta, "casa_prueba.schem")) and os.path.exists(os.path.join(ruta, "preview.png"))
print("OK: motor instalado. Prueba en", ruta)
