"""Lienzo rápido para construcciones grandes: escribe directamente en un array numpy.

Compatible con motor.exportar (expone .grid y .entidades).
X = este(+), Y = arriba, Z = sur(+). Coordenadas inclusivas en cajas.
"""
from __future__ import annotations

import math
import sys

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
import rutas  # noqa: E402,F401
import numpy as np  # noqa: E402

from schematica.blocks.block import Block  # noqa: E402
from schematica.core.palette import Palette  # noqa: E402
from schematica.core.voxel import VoxelGrid  # noqa: E402


class Lienzo:
    def __init__(self, ancho: int, alto: int, largo: int):
        self.grid = VoxelGrid(shape=(ancho, alto, largo), palette=Palette())
        self.d = self.grid.data
        self.sx, self.sy, self.sz = ancho, alto, largo
        self._cache: dict[str, int] = {"minecraft:air": 0, "air": 0}
        self.entidades: dict = {}

    # ------------------------------------------------------------ básicos
    def i(self, b: str) -> int:
        k = self._cache.get(b)
        if k is None:
            nombre = b if b.startswith("minecraft:") else "minecraft:" + b
            k = self.grid.palette.add(Block.parse(nombre))
            self._cache[b] = k
        return k

    def _clip(self, x0, y0, z0, x1, y1, z1):
        x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1)); z0, z1 = sorted((z0, z1))
        return (max(0, x0), max(0, y0), max(0, z0),
                min(self.sx - 1, x1), min(self.sy - 1, y1), min(self.sz - 1, z1))

    def caja(self, x0, y0, z0, x1, y1, z1, b):
        x0, y0, z0, x1, y1, z1 = self._clip(x0, y0, z0, x1, y1, z1)
        if x0 <= x1 and y0 <= y1 and z0 <= z1:
            self.d[x0:x1 + 1, y0:y1 + 1, z0:z1 + 1] = self.i(b)

    def vaciar(self, x0, y0, z0, x1, y1, z1):
        self.caja(x0, y0, z0, x1, y1, z1, "air")

    def set(self, x, y, z, b):
        if 0 <= x < self.sx and 0 <= y < self.sy and 0 <= z < self.sz:
            self.d[x, y, z] = self.i(b)

    def get(self, x, y, z) -> str:
        return self.grid.palette[int(self.d[x, y, z])].to_blockstate_str()

    def es_aire(self, x, y, z) -> bool:
        return 0 <= x < self.sx and 0 <= y < self.sy and 0 <= z < self.sz and self.d[x, y, z] == 0

    def muros(self, x0, y0, z0, x1, y1, z1, b):
        self.caja(x0, y0, z0, x1, y1, z0, b); self.caja(x0, y0, z1, x1, y1, z1, b)
        self.caja(x0, y0, z0, x0, y1, z1, b); self.caja(x1, y0, z0, x1, y1, z1, b)

    def marco(self, x0, y, z0, x1, z1, b):
        """Anillo horizontal de 1 de ancho."""
        self.muros(x0, y, z0, x1, y, z1, b)

    def reemplazar_en(self, x0, y0, z0, x1, y1, z1, origen: str, destino: str):
        x0, y0, z0, x1, y1, z1 = self._clip(x0, y0, z0, x1, y1, z1)
        sub = self.d[x0:x1 + 1, y0:y1 + 1, z0:z1 + 1]
        sub[sub == self.i(origen)] = self.i(destino)

    # ------------------------------------------------------------ formas
    def disco(self, cx, cz, r, y0, y1, b, hueco=0.0):
        """Cilindro vertical (macizo, o anillo si hueco>0 = radio interior)."""
        x0, x1 = int(math.floor(cx - r)), int(math.ceil(cx + r))
        z0, z1 = int(math.floor(cz - r)), int(math.ceil(cz + r))
        X, Z = np.meshgrid(np.arange(x0, x1 + 1), np.arange(z0, z1 + 1), indexing="ij")
        d2 = (X - cx) ** 2 + (Z - cz) ** 2
        m = d2 <= r * r + r * 0.8
        if hueco > 0:
            m &= d2 > hueco * hueco + hueco * 0.8
        k = self.i(b)
        for x, z in zip(X[m], Z[m]):
            if 0 <= x < self.sx and 0 <= z < self.sz:
                self.d[x, max(0, y0):min(self.sy, y1 + 1), z] = k

    def octogono(self, cx, cz, r, chaflan, y0, y1, b, hueco=None):
        """Octógono relleno (cuadrado de semilado r con esquinas cortadas `chaflan`)."""
        X, Z = np.meshgrid(np.arange(cx - r, cx + r + 1), np.arange(cz - r, cz + r + 1), indexing="ij")
        dx, dz = np.abs(X - cx), np.abs(Z - cz)
        m = (dx <= r) & (dz <= r) & (dx + dz <= 2 * r - chaflan)
        if hueco is not None:
            r2, ch2 = hueco
            m &= ~((dx <= r2) & (dz <= r2) & (dx + dz <= 2 * r2 - ch2))
        k = self.i(b)
        for x, z in zip(X[m], Z[m]):
            if 0 <= x < self.sx and 0 <= z < self.sz:
                self.d[x, max(0, y0):min(self.sy, y1 + 1), z] = k

    def linea(self, x0, z0, x1, z1, y, b, ancho=1):
        n = max(abs(x1 - x0), abs(z1 - z0)) + 1
        for t in np.linspace(0, 1, n * 2):
            x, z = round(x0 + (x1 - x0) * t), round(z0 + (z1 - z0) * t)
            h = ancho // 2
            self.caja(x - h, y, z - h, x - h + ancho - 1, y, z - h + ancho - 1, b)

    # ------------------------------------------------------------ entidades
    def spawner(self, x, y, z, mob: str):
        self.set(x, y, z, "minecraft:spawner")
        from nbtlib.tag import Compound, Short, String
        self.entidades[(x, y, z)] = ("minecraft:mob_spawner", {
            "SpawnData": Compound({"entity": Compound({"id": String(f"minecraft:{mob}")})}),
            "Delay": Short(20), "MinSpawnDelay": Short(200), "MaxSpawnDelay": Short(800),
            "SpawnCount": Short(4), "MaxNearbyEntities": Short(6), "RequiredPlayerRange": Short(16),
            "SpawnRange": Short(4),
        })
