"""Motor de construcciones para Minecraft (Paper 26.x + FAWE).

Capa fina sobre Schematica (diseño por primitivas) que añade:
  * Exportación Sponge v3 con DataVersion 4903, compatible con el que guarda FAWE.
  * Validación de cada bloque y estado contra el catálogo 26.1 (lo más cercano
    a 26.2 en minecraft-data) y relleno de estados por defecto.
  * Anclaje de pegado: dónde queda el jugador al hacer //paste.
  * Lista de materiales, vistas previas y comprobación de ida y vuelta.

Uso típico:
    from motor import nueva, exportar
    s = nueva(21, 16, 15)
    s.add(Box(...), "minecraft:stone_bricks")
    exportar(s, "mi_build", anclaje="centro")
"""
from __future__ import annotations

import json
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rutas import SALIDAS, VENDOR  # noqa: E402,F401

import nbtlib  # noqa: E402
import numpy as np  # noqa: E402
from nbtlib.tag import ByteArray, Compound, Int, IntArray, List, Long, Short, String  # noqa: E402

from schematica.blocks.block import Block  # noqa: E402
from schematica.blocks.registry import BlockRegistry  # noqa: E402
from schematica.session.session import Session  # noqa: E402

DATA_VERSION = 4903        # leída de schematics guardados por FAWE en un servidor Paper 26.x
CATALOGO = "26.1"          # catálogo de bloques más reciente disponible

# Bloques que necesitan block entity para no quedar "vacíos" al pegar.
_CON_ENTIDAD = ("chest", "barrel", "furnace", "smoker", "blast_furnace", "hopper",
                "dispenser", "dropper", "_sign", "_hanging_sign", "lectern",
                "brewing_stand", "campfire", "bell", "beacon", "enchanting_table",
                "shulker_box", "decorated_pot", "chiseled_bookshelf", "crafter", "banner")


def nueva(ancho: int, alto: int, largo: int) -> Session:
    """Sesión vacía: X=ancho (este-oeste), Y=alto, Z=largo (norte-sur). Z=0 es el norte."""
    return Session.new((ancho, alto, largo), version=CATALOGO)


# ---------------------------------------------------------------- validación
def _validar(grid) -> tuple[dict[int, str], list[str]]:
    """Resuelve cada entrada de la paleta contra el catálogo. Devuelve mapa idx->estado y errores."""
    reg = BlockRegistry.for_version(CATALOGO)
    mapa, errores = {}, []
    for i, b in enumerate(grid.palette.blocks()):
        try:
            mapa[i] = reg.resolve(b).to_blockstate_str()
        except Exception as e:  # noqa: BLE001
            errores.append(f"{b.to_blockstate_str()}: {e}")
    return mapa, errores


# ---------------------------------------------------------------- exportador v3
def _varint(v: int, out: bytearray) -> None:
    while True:
        b = v & 0x7F
        v >>= 7
        if v:
            out.append(b | 0x80)
        else:
            out.append(b)
            return


def _offset(anclaje: str, sx: int, sy: int, sz: int, hundir: int) -> tuple[int, int, int]:
    """Offset = esquina mínima respecto a los pies del jugador al pegar."""
    y = -hundir
    if anclaje == "centro":
        return (-(sx // 2), y, -(sz // 2))
    if anclaje == "entrada_sur":  # jugador delante de la fachada sur, mirando al norte
        return (-(sx // 2), y, -sz)
    if anclaje == "esquina":
        return (0, y, 0)
    raise ValueError("anclaje: centro | entrada_sur | esquina")


def _varints_np(vals: np.ndarray) -> bytes:
    """Codifica en varint (hasta 3 bytes por valor) de forma vectorizada."""
    v = vals.astype(np.int64)
    n = np.where(v < 128, 1, np.where(v < 16384, 2, 3))
    out = np.zeros(int(n.sum()), dtype=np.uint8)
    pos = np.concatenate([[0], np.cumsum(n)[:-1]])
    b0 = np.where(n > 1, (v & 0x7F) | 0x80, v & 0x7F)
    out[pos] = b0
    m2 = n >= 2
    out[pos[m2] + 1] = np.where(n[m2] > 2, ((v[m2] >> 7) & 0x7F) | 0x80, (v[m2] >> 7) & 0x7F)
    m3 = n == 3
    out[pos[m3] + 2] = (v[m3] >> 14) & 0x7F
    return out.tobytes()


def _desvarints_np(raw: bytes) -> np.ndarray:
    b = np.frombuffer(raw, dtype=np.uint8).astype(np.int64)
    fin = (b & 0x80) == 0
    ends = np.nonzero(fin)[0]
    starts = np.concatenate([[0], ends[:-1] + 1])
    largo = ends - starts + 1
    out = b[starts] & 0x7F
    m = largo >= 2
    out[m] |= (b[starts[m] + 1] & 0x7F) << 7
    m = largo >= 3
    out[m] |= (b[starts[m] + 2] & 0x7F) << 14
    return out


def escribir_v3(grid, ruta: Path, *, nombre: str, anclaje: str, hundir: int, extra_entidades=None,
                offset=None) -> dict:
    mapa, errores = _validar(grid)
    if errores:
        raise ValueError("Bloques no válidos para " + CATALOGO + ":\n  " + "\n  ".join(errores))
    data = grid.to_dense().data if hasattr(grid, "to_dense") else grid.data
    sx, sy, sz = data.shape

    # Paleta compacta: solo los índices realmente usados (y fusiona duplicados tras resolver).
    usados = np.unique(data)
    nueva_idx, paleta = {}, {}
    for i in usados:
        est = mapa[int(i)]
        if est not in paleta:
            paleta[est] = len(paleta)
        nueva_idx[int(i)] = paleta[est]
    lut = np.zeros(int(data.max()) + 1, dtype=np.int64)
    for k, v in nueva_idx.items():
        lut[k] = v
    remap = lut[data]

    # Orden Sponge: índice = x + z*W + y*W*L  -> recorrer y, z, x
    buf = _varints_np(remap.transpose(1, 2, 0).reshape(-1))

    entidades = []
    extra = dict(extra_entidades or {})
    inv = {v: k for k, v in paleta.items()}
    con_ent = [v for v, k in inv.items()
               if any(t in k.split("[")[0].removeprefix("minecraft:") for t in _CON_ENTIDAD)]
    for x, y, z in zip(*np.nonzero(np.isin(remap, con_ent))):
        x, y, z = int(x), int(y), int(z)
        if (x, y, z) in extra:
            continue
        nombre_b = inv[int(remap[x, y, z])].split("[")[0].removeprefix("minecraft:")
        bid = "minecraft:" + ("sign" if nombre_b.endswith("_sign") and "hanging" not in nombre_b
                              else "hanging_sign" if "hanging_sign" in nombre_b
                              else "shulker_box" if "shulker_box" in nombre_b
                              else "banner" if "banner" in nombre_b else nombre_b)
        entidades.append(Compound({"Id": String(bid), "Pos": IntArray([Int(x), Int(y), Int(z)]),
                                   "Data": Compound({"id": String(bid)})}))
    for (x, y, z), (bid, datos) in extra.items():
        d = Compound(datos); d["id"] = String(bid)
        entidades.append(Compound({"Id": String(bid), "Pos": IntArray([Int(x), Int(y), Int(z)]), "Data": d}))

    off = offset if offset is not None else _offset(anclaje, sx, sy, sz, hundir)
    bloques = Compound({
        "Palette": Compound({k: Int(v) for k, v in paleta.items()}),
        "Data": ByteArray(np.frombuffer(bytes(buf), dtype=np.int8)),
    })
    if entidades:
        bloques["BlockEntities"] = List[Compound](entidades)
    raiz = Compound({
        "Version": Int(3),
        "DataVersion": Int(DATA_VERSION),
        "Width": Short(sx), "Height": Short(sy), "Length": Short(sz),
        "Offset": IntArray([Int(c) for c in off]),
        "Metadata": Compound({"Name": String(nombre), "Author": String("motor_construcciones"),
                              "Date": Long(int(time.time() * 1000))}),
        "Blocks": bloques,
    })
    nbtlib.File({"Schematic": raiz}, gzipped=True).save(ruta)
    return {"paleta": paleta, "remap": remap, "offset": off}


def _comprobar(ruta: Path, remap: np.ndarray, paleta: dict) -> None:
    """Relee el fichero y compara bloque a bloque."""
    r = nbtlib.load(ruta)["Schematic"]
    assert int(r["Version"]) == 3 and int(r["DataVersion"]) == DATA_VERSION
    w, h, l = int(r["Width"]), int(r["Height"]), int(r["Length"])
    raw = bytes(np.array(r["Blocks"]["Data"], dtype=np.int8).tobytes())
    arr = _desvarints_np(raw).reshape(h, l, w).transpose(2, 0, 1)
    assert arr.shape == remap.shape and (arr == remap).all(), "la relectura no coincide"
    pal = {k: int(v) for k, v in r["Blocks"]["Palette"].items()}
    assert pal == paleta


# ---------------------------------------------------------------- materiales
def materiales(remap: np.ndarray, paleta: dict) -> list[tuple[str, int]]:
    inv = {v: k for k, v in paleta.items()}
    c = Counter()
    for idx, n in zip(*np.unique(remap, return_counts=True)):
        nombre = inv[int(idx)].split("[")[0].removeprefix("minecraft:")
        if nombre in ("air", "cave_air", "void_air"):
            continue
        # Puertas y camas ocupan 2 bloques pero son 1 ítem
        if inv[int(idx)].find("half=upper") >= 0 or "part=head" in inv[int(idx)]:
            continue
        c[nombre] += int(n)
    return c.most_common()


def _fmt_stacks(n: int) -> str:
    s, r = divmod(n, 64)
    return f"{n}" + (f" ({s}×64{' + ' + str(r) if r else ''})" if s else "")


# ---------------------------------------------------------------- vistas previas
def vistas(grid, carpeta: Path, titulo: str, niveles: list[int] | None = None) -> Path:
    """Lámina con iso SE/NO, planta y cortes por nivel, con texturas reales."""
    import render
    carpeta.mkdir(parents=True, exist_ok=True)
    data = grid.to_dense().data if hasattr(grid, "to_dense") else grid.data
    return render.lamina_completa(data, grid.palette.blocks(), titulo, carpeta / "preview.png", niveles)


# ---------------------------------------------------------------- todo junto
def exportar(s: Session, nombre: str, *, anclaje: str = "centro", hundir: int = 0,
             con_vistas: bool = True, niveles: list[int] | None = None, offset=None) -> dict:
    """Exporta <nombre>.schem + preview.png + materiales.txt en salidas/<nombre>/."""
    carpeta = SALIDAS / nombre
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / f"{nombre}.schem"
    import conexiones
    conectados = conexiones.aplicar(s.grid)
    info = escribir_v3(s.grid, ruta, nombre=nombre, anclaje=anclaje, hundir=hundir,
                       extra_entidades=getattr(s, "entidades", None), offset=offset)
    _comprobar(ruta, info["remap"], info["paleta"])
    mats = materiales(info["remap"], info["paleta"])
    sx, sy, sz = info["remap"].shape
    total = sum(n for _, n in mats)
    lineas = [f"{nombre}  —  {sx}×{sy}×{sz} (ancho×alto×largo), {total} bloques",
              f"Pegar: //schem load {nombre}  y  //paste -a   (anclaje={anclaje}, offset={info['offset']})", ""]
    lineas += [f"{n:<34} {_fmt_stacks(c)}" for n, c in mats]
    (carpeta / "materiales.txt").write_text("\n".join(lineas), encoding="utf-8")
    res = {"schem": ruta, "materiales": carpeta / "materiales.txt", "total": total,
           "dimensiones": (sx, sy, sz), "tipos": len(mats)}
    if con_vistas:
        res["preview"] = vistas(s.grid, carpeta, f"{nombre}  ·  {sx}×{sy}×{sz}  ·  {total} bloques", niveles)
    res["conexiones_recalculadas"] = conectados
    (carpeta / "info.json").write_text(json.dumps({k: str(v) for k, v in res.items()}, indent=1))
    return res
