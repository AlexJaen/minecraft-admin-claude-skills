"""Catálogo de decoración (estética espacial morada/rosa). Todas las piezas se centran en (x, z)
y son simétricas respecto a su centro salvo que se indique orientación."""
from __future__ import annotations
import os as _os, sys as _sys  # noqa: E401
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import rutas  # noqa: E402,F401

import math
import random

from simetria import rc, rs

LUZ = "pearlescent_froglight"
HOJAS_CEREZO = "cherry_leaves[persistent=true,distance=1,waterlogged=false]"
HOJAS_AZALEA = "flowering_azalea_leaves[persistent=true,distance=1,waterlogged=false]"
HOJAS_AZALEA2 = "azalea_leaves[persistent=true,distance=1,waterlogged=false]"
CESPED = "grass_block[snowy=false]"
OPUESTO = {"north": "south", "south": "north", "east": "west", "west": "east"}


class Deco:
    def __init__(self, c, F, semilla=7):
        self.c, self.F = c, F
        self.rnd = random.Random(semilla)

    # ------------------------------------------------------------ iluminación
    def farola_a(self, x, z, alto=3):
        """Columna de purpur con ranaluz y end rod."""
        c, F = self.c, self.F
        c.set(x, F + 1, z, "purpur_block")
        c.caja(x, F + 2, z, x, F + alto, z, "purpur_pillar[axis=y]")
        c.set(x, F + alto + 1, z, LUZ)
        c.set(x, F + alto + 2, z, "end_rod[facing=up]")

    def farola_b(self, x, z, eje="x"):
        """Farola doble de brazos: poste de cuarzo, brazos de losa y luces colgando de cadenas."""
        c, F = self.c, self.F
        c.set(x, F + 1, z, "smooth_quartz")
        c.caja(x, F + 2, z, x, F + 6, z, "quartz_pillar[axis=y]")
        c.set(x, F + 7, z, "amethyst_block")
        c.set(x, F + 8, z, "end_rod[facing=up]")
        dx, dz = (1, 0) if eje == "x" else (0, 1)
        for s in (-1, 1):
            for k in (1, 2):
                c.set(x + dx * s * k, F + 7, z + dz * s * k, "purpur_slab[type=top]")
            c.set(x + dx * s * 2, F + 6, z + dz * s * 2, "iron_chain[axis=y]")
            c.set(x + dx * s * 2, F + 5, z + dz * s * 2, LUZ)

    def baliza(self, x, z):
        """Baliza baja de suelo (bolardo luminoso)."""
        c, F = self.c, self.F
        c.set(x, F + 1, z, "purpur_slab[type=bottom]")
        c.set(x, F, z, LUZ)

    # ------------------------------------------------------------ mobiliario
    def banco(self, x, z, mira):
        """Banco de 5 (3 asientos + reposabrazos) centrado en (x,z). `mira` = hacia dónde mira quien se sienta."""
        c, F = self.c, self.F
        facing = OPUESTO[mira]                       # el respaldo queda detrás
        dx, dz = (1, 0) if mira in ("north", "south") else (0, 1)
        for k in (-1, 0, 1):
            c.set(x + dx * k, F + 1, z + dz * k, f"quartz_stairs[facing={facing},half=bottom]")
        a1, a2 = ("west", "east") if dx else ("north", "south")
        # reposabrazos: trampillas abiertas con el panel en el lado exterior
        c.set(x - 2 * dx, F + 1, z - 2 * dz, f"pale_oak_trapdoor[facing={a2},half=bottom,open=true]")
        c.set(x + 2 * dx, F + 1, z + 2 * dz, f"pale_oak_trapdoor[facing={a1},half=bottom,open=true]")

    def maceta(self, x, z, planta=None):
        c, F = self.c, self.F
        c.set(x, F + 1, z, f"potted_{planta or self.rnd.choice(['allium', 'pink_tulip', 'azalea_bush', 'flowering_azalea_bush', 'cherry_sapling'])}")

    # ------------------------------------------------------------ vegetación
    def jardinera(self, x, z, r=1, planta="azalea"):
        """Jardinera elevada (2r+1)² con borde de cuarzo y planta central."""
        c, F = self.c, self.F
        c.caja(x - r - 1, F + 1, z - r - 1, x + r + 1, F + 1, z + r + 1, "smooth_quartz")
        c.caja(x - r, F + 1, z - r, x + r, F + 1, z + r, CESPED)
        c.caja(x - r, F, z - r, x + r, F, z + r, "dirt")
        if planta == "azalea":
            c.set(x, F + 2, z, "flowering_azalea")
        elif planta == "cerezo":
            self.cerezo(x, z, base=F + 1, alto=4, r=2)
        if r >= 1:
            for dx, dz in ((-r, -r), (r, -r), (-r, r), (r, r)):
                c.set(x + dx, F + 2, z + dz, "allium")

    def arbusto(self, x, z, r=1):
        c, F = self.c, self.F
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                for dy in (1, 2):
                    if abs(dx) + abs(dz) + (dy - 1) <= r + 1 and c.es_aire(x + dx, F + dy, z + dz):
                        c.set(x + dx, F + dy, z + dz, HOJAS_AZALEA if (dx + dz + dy) % 2 else HOJAS_AZALEA2)

    def cerezo(self, x, z, base=None, alto=None, r=None):
        """Cerezo con copa simétrica respecto al tronco (radio impar alrededor del centro)."""
        c = self.c
        base = self.F if base is None else base
        alto = alto or self.rnd.choice((4, 5, 5, 6))
        r = r or self.rnd.choice((2, 3, 3))
        c.caja(x, base + 1, z, x, base + alto, z, "cherry_log[axis=y]")
        top = base + alto
        for dy in range(-1, 3):
            rr = r - (1 if dy in (-1, 2) else 0)
            for dx in range(-rr, rr + 1):
                for dz in range(-rr, rr + 1):
                    if dx * dx + dz * dz <= rr * rr + rr and c.es_aire(x + dx, top + dy, z + dz):
                        c.set(x + dx, top + dy, z + dz, HOJAS_CEREZO)
        # ramas colgantes en los 4 lados (simétricas)
        for dx, dz in ((r, 0), (-r, 0), (0, r), (0, -r)):   # ramas colgantes pegadas a la copa
            if c.es_aire(x + dx, top - 1, z + dz) and not c.es_aire(x + dx, top, z + dz):
                c.set(x + dx, top - 1, z + dz, HOJAS_CEREZO)
        for dx, dz in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
            if c.es_aire(x + dx * 2, base + 1, z + dz * 2) and c.get(x + dx * 2, base, z + dz * 2).startswith("minecraft:grass"):
                c.set(x + dx * 2, base + 1, z + dz * 2, "pink_petals[flower_amount=3,facing=north]")

    def parterre(self, x0, z0, x1, z1):
        """Lecho de flores con patrón simétrico respecto a su centro."""
        c, F = self.c, self.F
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                c.set(x, F, z, CESPED)
                k = int(abs(x - cx) + abs(z - cz))
                flor = ("allium", "pink_tulip", "short_grass", "allium", "lily_of_the_valley")[k % 5]
                if c.es_aire(x, F + 1, z):
                    c.set(x, F + 1, z, flor)

    # ------------------------------------------------------------ elementos verticales
    def obelisco(self, x, z, alto=8):
        c, F = self.c, self.F
        c.caja(x - 1, F + 1, z - 1, x + 1, F + 1, z + 1, "purpur_block")
        c.caja(x - 1, F + 2, z - 1, x + 1, F + 2, z + 1, "purpur_slab[type=bottom]")
        c.caja(x, F + 2, z, x, F + alto, z, "amethyst_block")
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            c.caja(x + dx, F + 3, z + dz, x + dx, F + 2 + alto // 2, z + dz, "magenta_stained_glass")
        c.set(x, F + alto + 1, z, LUZ)
        c.set(x, F + alto + 2, z, "end_rod[facing=up]")

    def antena(self, x, z, alto=10):
        c, F = self.c, self.F
        c.caja(x - 1, F + 1, z - 1, x + 1, F + 1, z + 1, "polished_blackstone")
        c.set(x, F + 1, z, "purpur_block")
        c.caja(x, F + 2, z, x, F + alto, z, "iron_bars")
        for y in range(F + 4, F + alto, 3):
            c.set(x, y, z, LUZ)
        c.set(x, F + alto + 1, z, "lightning_rod[facing=up]")

    def estandarte(self, x, z, color="magenta", alto=6):
        """Mástil con dos estandartes (a ambos lados, simétrico en X)."""
        c, F = self.c, self.F
        c.caja(x, F + 1, z, x, F + alto, z, "purpur_pillar[axis=y]")
        c.set(x, F + alto + 1, z, "end_rod[facing=up]")
        c.set(x + 1, F + alto - 1, z, f"{color}_wall_banner[facing=east]")
        c.set(x - 1, F + alto - 1, z, f"{color}_wall_banner[facing=west]")

    # ------------------------------------------------------------ agua
    def fuente(self, x, z, r=4, niveles=2):
        """Fuente de varios niveles: vaso exterior (radio r) + pedestal con cuenco superior."""
        c, F = self.c, self.F
        c.disco(x, z, r + 1, F, F, "smooth_quartz")
        c.disco(x, z, r + 1, F + 1, F + 1, "purpur_slab[type=bottom]")
        c.disco(x, z, r, F + 1, F + 1, "air")
        c.disco(x, z, r, F, F, "water[level=0]")
        c.disco(x, z, r, F - 1, F - 1, "amethyst_block")
        c.caja(x, F, z, x, F + 2, z, "purpur_pillar[axis=y]")
        if niveles >= 2:
            c.caja(x - 1, F + 3, z - 1, x + 1, F + 3, z + 1, "smooth_quartz_slab[type=top]")
            c.set(x, F + 3, z, "purpur_block")
            c.set(x, F + 4, z, "water[level=0]")
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                c.set(x + dx, F + 4, z + dz, "purpur_slab[type=bottom]")
            for dx, dz in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
                c.set(x + dx, F + 4, z + dz, "end_rod[facing=up]")
        for ang in range(0, 360, 45):
            xx = x + rc(r + 1, ang)
            zz = z + rs(r + 1, ang)
            c.set(xx, F, zz, LUZ)
