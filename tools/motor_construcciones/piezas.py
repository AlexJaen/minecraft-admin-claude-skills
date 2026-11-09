"""Piezas de construcción de alto nivel (evitan errores típicos de orientación y huecos).

Convenciones: X = este(+)/oeste(-), Y = arriba, Z = sur(+)/norte(-). Coordenadas inclusivas.
"""
from __future__ import annotations
import os as _os, sys as _sys  # noqa: E401
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import rutas  # noqa: E402,F401

from schematica.shapes.primitives import Box


def caja(s, x0, y0, z0, x1, y1, z1, bloque):
    s.add(Box(min(x0, x1), min(y0, y1), min(z0, z1), max(x0, x1), max(y0, y1), max(z0, z1)), bloque)


def vaciar(s, x0, y0, z0, x1, y1, z1):
    s.subtract(Box(min(x0, x1), min(y0, y1), min(z0, z1), max(x0, x1), max(y0, y1), max(z0, z1)))


def bloque(s, x, y, z, b):
    s.set_box((x, y, z), (x, y, z), b)


def muros(s, x0, y0, z0, x1, y1, z1, b):
    """Anillo de muros (sin suelo ni techo)."""
    caja(s, x0, y0, z0, x1, y1, z0, b)
    caja(s, x0, y0, z1, x1, y1, z1, b)
    caja(s, x0, y0, z0, x0, y1, z1, b)
    caja(s, x1, y0, z0, x1, y1, z1, b)


def postes(s, puntos, y0, y1, b):
    for x, z in puntos:
        caja(s, x, y0, z, x, y1, z, b)


def viga_perimetral(s, x0, y, z0, x1, z1, tronco):
    """Vigas de tronco con el eje bien orientado."""
    caja(s, x0, y, z0, x1, y, z0, f"{tronco}[axis=x]")
    caja(s, x0, y, z1, x1, y, z1, f"{tronco}[axis=x]")
    caja(s, x0, y, z0 + 1, x0, y, z1 - 1, f"{tronco}[axis=z]")
    caja(s, x1, y, z0 + 1, x1, y, z1 - 1, f"{tronco}[axis=z]")


def puerta(s, x, y, z, madera, mira, bisagra="left"):
    """Puerta de 2 de alto. `mira` = hacia dónde mira quien sale (fachada sur -> 'south')."""
    vaciar(s, x, y, z, x, y + 1, z)
    f = {"south": "north", "north": "south", "east": "west", "west": "east"}[mira]  # facing = hacia dentro
    bloque(s, x, y, z, f"minecraft:{madera}_door[facing={f},half=lower,hinge={bisagra}]")
    bloque(s, x, y + 1, z, f"minecraft:{madera}_door[facing={f},half=upper,hinge={bisagra}]")


def ventana(s, x, y, z, ancho=1, alto=1, eje="x", cristal="minecraft:glass_pane"):
    if eje == "x":
        caja(s, x, y, z, x + ancho - 1, y + alto - 1, z, cristal)
    else:
        caja(s, x, y, z, x, y + alto - 1, z + ancho - 1, cristal)


def tejado_dos_aguas(s, x0, z0, x1, z1, y, material, *, cumbrera="x", alero=1, relleno=None,
                     hastial=None):
    """Tejado de escaleras sobre la caja de muros [x0..x1]×[z0..z1], empezando en la altura y.

    cumbrera='x' -> la cumbrera va de oeste a este y las aguas caen al norte y al sur.
    material: familia de escaleras/losas, p.ej. 'dark_oak' -> dark_oak_stairs / dark_oak_slab.
    hastial: bloque para cerrar los triángulos de los extremos (None = no cerrar).
    Devuelve la altura de la cumbrera.
    """
    est = f"minecraft:{material}_stairs"
    losa = f"minecraft:{material}_slab[type=bottom]"
    if relleno is None:
        relleno = f"minecraft:{material}_planks" if _es_madera(material) else f"minecraft:{material}s"
    if cumbrera == "x":
        a0, a1 = x0 - alero, x1 + alero          # a lo largo de la cumbrera
        lo, hi = z0 - alero, z1 + alero          # caída
        sube_lo, sube_hi = "south", "north"
    else:
        a0, a1 = z0 - alero, z1 + alero
        lo, hi = x0 - alero, x1 + alero
        sube_lo, sube_hi = "east", "west"

    def fila(c, yy, b):
        if cumbrera == "x":
            caja(s, a0, yy, c, a1, yy, c, b)
        else:
            caja(s, c, yy, a0, c, yy, a1, b)

    i = 0
    while True:
        yy = y + i
        cl, ch = lo + i, hi - i
        if cl > ch:
            return yy - 1
        if cl == ch:
            fila(cl, yy, losa)
            return yy
        fila(cl, yy, f"{est}[facing={sube_lo},half=bottom]")
        fila(ch, yy, f"{est}[facing={sube_hi},half=bottom]")
        if i >= 1:  # escalera invertida bajo el alero para cerrar el hueco
            for ext in (a0, a1):
                for c, f in ((cl, sube_hi), (ch, sube_lo)):
                    if cumbrera == "x":
                        bloque(s, ext, yy - 1, c, f"{est}[facing={f},half=top]")
                    else:
                        bloque(s, c, yy - 1, ext, f"{est}[facing={f},half=top]")
        if hastial and i >= 1:  # triángulo del extremo, por debajo de esta hilera
            ini, fin = cl + 1 - 0, ch - 1 + 0
            for ext in ((x0, x1) if cumbrera == "x" else (z0, z1)):
                if ini <= fin:
                    if cumbrera == "x":
                        caja(s, ext, yy, ini, ext, yy, fin, hastial)
                    else:
                        caja(s, ini, yy, ext, fin, yy, ext, hastial)
        i += 1


def _es_madera(m: str) -> bool:
    return m in ("oak", "spruce", "birch", "jungle", "acacia", "dark_oak", "mangrove", "cherry",
                 "bamboo", "crimson", "warped", "pale_oak")
