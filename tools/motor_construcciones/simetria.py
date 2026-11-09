"""Simetría: espejo de bloques/zonas y comprobaciones automáticas (paridad, espejo, centrado)."""
from __future__ import annotations
import os as _os, sys as _sys  # noqa: E401
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import rutas  # noqa: E402,F401

import math

import numpy as np

from schematica.blocks.block import Block

_EO = {"east": "west", "west": "east"}
_NS = {"north": "south", "south": "north"}
_LR = {"left": "right", "right": "left"}


def espejo_bloque(b: Block, eje: str) -> Block:
    """Refleja un bloque. eje='x' -> espejo este<->oeste; eje='z' -> norte<->sur.
    Conserva el tipo original de cada valor (bool/int/str) para no duplicar entradas de paleta."""
    if not b.states:
        return b
    swap = _EO if eje == "x" else _NS
    nuevo = {}
    for k, v in b.states:
        k2 = swap.get(k, k)                       # propiedades de conexión east/west o north/south
        sv = str(v).lower()
        if k == "facing" and sv in swap:
            v = swap[sv]
        elif k == "hinge" and sv in _LR:
            v = _LR[sv]
        elif k == "shape" and sv.endswith(("_left", "_right")):
            base, lado = sv.rsplit("_", 1)
            v = f"{base}_{_LR[lado]}"
        elif k == "rotation":
            r = int(sv)
            r2 = (16 - r) % 16 if eje == "x" else (8 - r) % 16
            v = r2 if isinstance(v, int) else str(r2)
        nuevo[k2] = v
    return Block.from_mapping(b.name, nuevo)


def clave(b: Block) -> str:
    """Estado canónico (texto en minúsculas) para comparar bloques sin depender del tipo de los valores."""
    return b.name + "[" + ",".join(f"{k}={str(v).lower()}" for k, v in sorted(b.states)) + "]"


def lut_espejo(grid, eje: str) -> np.ndarray:
    pal = grid.palette
    n = len(pal)
    lut = np.zeros(n, dtype=np.uint16)
    for i in range(n):
        lut[i] = pal.add(espejo_bloque(pal[i], eje))
    if len(pal) > n:  # se añadieron bloques nuevos: recalcular para cubrirlos
        return lut_espejo(grid, eje)
    return lut


def espejar_x(lienzo, cx: int) -> None:
    """Copia la mitad oeste (x < cx) sobre la mitad este, reflejada. El eje x=cx se queda."""
    d = lienzo.d
    lut = lut_espejo(lienzo.grid, "x")
    w = d.shape[0]
    for x in range(cx + 1, min(w, 2 * cx + 1)):
        d[x] = lut[d[2 * cx - x]]


def diferencias_espejo(d: np.ndarray, grid, caja, eje: str, excluir=()) -> list:
    """Compara una caja (x0,z0,x1,z1) con su reflejo. Devuelve posiciones distintas (x,y,z)."""
    x0, z0, x1, z1 = caja
    lut = lut_espejo(grid, eje)
    sub = d[x0:x1 + 1, :, z0:z1 + 1]
    ref = lut[sub[::-1, :, :]] if eje == "x" else lut[sub[:, :, ::-1]]
    m = sub != ref
    for (a0, b0, a1, b1) in excluir:   # zonas excluidas (coordenadas globales)
        m[max(0, a0 - x0):max(0, a1 - x0 + 1), :, max(0, b0 - z0):max(0, b1 - z0 + 1)] = False
    xs, ys, zs = np.nonzero(m)
    return [(int(x) + x0, int(y), int(z) + z0) for x, y, z in zip(xs, ys, zs)]


def centro(a0: int, a1: int) -> int:
    """Centro entero de un tramo inclusivo; error si el tramo es par (sin bloque central)."""
    assert (a0 + a1) % 2 == 0, f"tramo {a0}..{a1} de ancho {a1 - a0 + 1} es PAR: no tiene bloque central"
    return (a0 + a1) // 2


def assert_centrado(nombre: str, a0: int, a1: int, eje: int) -> None:
    c = centro(a0, a1)
    assert c == eje, f"{nombre}: centro {c} != eje {eje}"


def rc(r, ang):
    """r·cos(ang) redondeado de forma simétrica (mismo valor absoluto en los 4 cuadrantes)."""
    v = r * math.cos(math.radians(ang))
    return int(math.copysign(math.floor(abs(v) + 0.5 + 1e-9), v)) if abs(v) > 1e-9 else 0


def rs(r, ang):
    """r·sin(ang) redondeado de forma simétrica."""
    v = r * math.sin(math.radians(ang))
    return int(math.copysign(math.floor(abs(v) + 0.5 + 1e-9), v)) if abs(v) > 1e-9 else 0
