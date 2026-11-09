"""Post-proceso de estados dependientes de vecinos.

FAWE/WorldEdit pegan sin físicas: paneles, vallas, muros, barrotes y escaleras
en esquina se quedan con el estado que lleve el fichero. Aquí se calculan
como lo haría el juego al colocarlos a mano.
"""
from __future__ import annotations
import os as _os, sys as _sys  # noqa: E401
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import rutas  # noqa: E402,F401

import numpy as np

from schematica.blocks.block import Block

DIRS = {"north": (0, 0, -1), "south": (0, 0, 1), "east": (1, 0, 0), "west": (-1, 0, 0)}
OPUESTO = {"north": "south", "south": "north", "east": "west", "west": "east"}
IZQ = {"north": "west", "west": "south", "south": "east", "east": "north"}  # girar 90º a la izquierda
DER = {v: k for k, v in IZQ.items()}

NO_SOLIDOS = ("air", "glass_pane", "leaves", "poppy", "dandelion", "tulip", "orchid", "allium",
              "bluet", "daisy", "cornflower", "lily", "rose_bush", "peony", "lilac", "sunflower", "torchflower",
              "pitcher", "eyeblossom", "petals", "wildflowers", "wither_rose", "dead_bush", "roots", "sprouts", "slab", "stairs", "fence", "wall", "pane", "bars",
              "door", "trapdoor", "carpet", "lantern", "torch", "sign", "button", "pressure_plate",
              "flower", "sapling", "grass", "fern", "bed", "chest", "campfire", "rail", "ladder",
              "vine", "chain", "candle", "pot", "banner", "head", "skull", "lever", "rod", "cake",
              "snow", "water", "lava", "scaffolding", "anvil", "bell", "lectern", "cauldron",
              "hopper", "brewing", "enchanting", "_gate", "dripleaf", "azalea", "moss_carpet",
              "mushroom", "bush", "seagrass", "kelp", "coral", "cactus", "bamboo", "sugar_cane",
              "shelf", "decorated_pot", "copper_grate")


def _corto(b: Block) -> str:
    return b.name.removeprefix("minecraft:")


def familia(nombre: str) -> str | None:
    if nombre.endswith("_fence"):
        return "fence"
    if nombre.endswith("_pane") or nombre == "glass_pane":
        return "pane"
    if nombre.endswith("_bars"):  # iron_bars y copper_bars
        return "pane"
    if nombre.endswith("_wall") and "sign" not in nombre and "banner" not in nombre and "torch" not in nombre \
            and "head" not in nombre and "skull" not in nombre and "fan" not in nombre:
        return "wall"
    return None


def solido_completo(nombre: str) -> bool:
    return not any(t in nombre for t in NO_SOLIDOS)


def _estados(b: Block) -> dict:
    return {k: str(v).lower() for k, v in b.states}


def _con(b: Block, **cambios) -> Block:
    st = _estados(b)
    st.update({k: str(v).lower() for k, v in cambios.items()})
    return Block.from_mapping(b.name, st)


def aplicar(grid) -> int:
    """Recalcula conexiones in situ. Devuelve el número de bloques modificados."""
    data = grid.data
    pal = grid.palette
    sx, sy, sz = data.shape
    bloques = pal.blocks()
    nombres = [_corto(b) for b in bloques]
    fam = [familia(n) for n in nombres]
    solido = [solido_completo(n) for n in nombres]
    es_escalera = [n.endswith("_stairs") for n in nombres]

    def en(x, y, z):
        if 0 <= x < sx and 0 <= y < sy and 0 <= z < sz:
            return int(data[x, y, z])
        return 0

    cambios = 0
    nuevos: list[tuple[int, int, int, Block]] = []
    objetivos = np.isin(data, [i for i in range(len(bloques)) if fam[i] or es_escalera[i]])
    for x, y, z in zip(*np.nonzero(objetivos)):
        i = int(data[x, y, z])
        b = bloques[i]
        f = fam[i]
        if f:
            st = {}
            for d, (dx, dy, dz) in DIRS.items():
                j = en(x + dx, y + dy, z + dz)
                nj = nombres[j]
                conecta = j != 0 and (solido[j] or fam[j] == f
                                      or (f == "fence" and nj.endswith("_fence_gate"))
                                      or (f == "wall" and fam[j] in ("pane", "fence") and False)
                                      or (f in ("pane", "wall") and fam[j] in ("pane", "wall")))
                # las vallas de madera no conectan con las del nether y viceversa
                if f == "fence" and fam[j] == "fence":
                    conecta = (nombres[i] == "nether_brick_fence") == (nj == "nether_brick_fence")
                if f == "wall":
                    arriba = en(x + dx, y + 1, z + dz)
                    alto = conecta and en(x, y + 1, z) != 0 and solido[en(x, y + 1, z)]
                    st[d] = ("tall" if alto else "low") if conecta else "none"
                else:
                    st[d] = "true" if conecta else "false"
            if f == "wall":
                rect_ns = st["north"] != "none" and st["south"] != "none" and st["east"] == "none" and st["west"] == "none"
                rect_ew = st["east"] != "none" and st["west"] != "none" and st["north"] == "none" and st["south"] == "none"
                encima = en(x, y + 1, z)
                st["up"] = "false" if (rect_ns or rect_ew) and not (encima and fam[encima] == "wall") else "true"
            nb = _con(b, **st)
        else:
            nb = _forma_escalera(b, x, y, z, en, bloques, es_escalera)
        if nb != b:
            nuevos.append((x, y, z, nb))
    for x, y, z, nb in nuevos:
        data[x, y, z] = pal.add(nb)
        cambios += 1
    return cambios


def _forma_escalera(b, x, y, z, en, bloques, es_escalera) -> Block:
    """Algoritmo del juego (StairBlock#getStairsShape)."""
    st = _estados(b)
    facing = st.get("facing", "north")
    half = st.get("half", "bottom")

    def vecina(d):
        dx, _, dz = DIRS[d]
        j = en(x + dx, y, z + dz)
        if j and es_escalera[j]:
            s2 = _estados(bloques[j])
            if s2.get("half", "bottom") == half:
                return s2.get("facing", "north")
        return None

    def mismo(d, f_esperada):
        """¿La escalera en dirección d tiene el mismo facing y half? (bloquea la forma)."""
        dx, _, dz = DIRS[d]
        j = en(x + dx, y, z + dz)
        if j and es_escalera[j]:
            s2 = _estados(bloques[j])
            return s2.get("facing") == f_esperada and s2.get("half", "bottom") == half
        return False

    forma = "straight"
    delante = vecina(facing)  # escalera hacia donde sube
    if delante and delante in (IZQ[facing], DER[facing]) and not mismo(OPUESTO[delante], facing):
        forma = "outer_left" if delante == IZQ[facing] else "outer_right"
    else:
        detras = vecina(OPUESTO[facing])
        if detras and detras in (IZQ[facing], DER[facing]) and not mismo(detras, facing):
            forma = "inner_left" if detras == IZQ[facing] else "inner_right"
    if st.get("shape") == forma:
        return b
    return _con(b, shape=forma)
