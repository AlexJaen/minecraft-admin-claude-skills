"""Renderizador isométrico con texturas reales de Minecraft (PrismarineJS minecraft-assets 1.21.11).

Vistas: iso desde el sureste (fachada sur + este), iso desde el noroeste,
planta cenital y plantas cortadas por niveles (para ver interiores).
"""
from __future__ import annotations
import os as _os, sys as _sys  # noqa: E401
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import rutas  # noqa: E402,F401

import json
import math
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from schematica.blocks.block import Block

from rutas import TEX, VENDOR  # noqa: E402
COLORES = VENDOR / "scripts" / "schematica" / "data" / "block_colors.json"

GIRO180 = {"north": "south", "south": "north", "east": "west", "west": "east"}
TINTE_HIERBA = (124, 189, 107)
TINTE_HOJAS = (89, 174, 48)
TRANSPARENTES = ("glass", "leaves", "ice", "slime", "honey_block")


def _st(b: Block) -> dict:
    return {k: str(v).lower() for k, v in b.states}


# ------------------------------------------------------------------ texturas
@lru_cache(maxsize=None)
def _png(nombre: str) -> Image.Image | None:
    p = TEX / f"{nombre}.png"
    if not p.exists():
        return None
    im = Image.open(p).convert("RGBA")
    if im.height > im.width:  # texturas animadas: primer frame
        im = im.crop((0, 0, im.width, im.width))
    return im.resize((16, 16), Image.NEAREST)


def _tintar(im: Image.Image, color) -> Image.Image:
    a = np.asarray(im).astype(np.float32)
    a[..., :3] = a[..., :3] * (np.array(color) / 255.0)
    return Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGBA")


@lru_cache(maxsize=1)
def _tabla_colores():
    d = json.loads(COLORES.read_text())["colors"]
    return {k.removeprefix("minecraft:"): tuple(int(c * 255) for c in v) for k, v in d.items()}


def _color_plano(nombre: str) -> Image.Image:
    t = _tabla_colores()
    c = None
    for cand in (nombre, nombre + "s", nombre.replace("_stairs", "").replace("_slab", ""), "stone"):
        if cand in t:
            c = t[cand]
            break
    return Image.new("RGBA", (16, 16), (*c, 255))


_SUFIJOS_MATERIAL = ("_stairs", "_slab", "_wall", "_fence_gate", "_fence", "_pressure_plate", "_button")
_ESPECIALES = {
    "chest": "oak_planks", "trapped_chest": "oak_planks", "ender_chest": "obsidian",
    "campfire": "campfire_log", "soul_campfire": "campfire_log",
    "water": "water_still", "lava": "lava_still", "bell": "gold_block",
    "red_bed": "red_wool", "white_bed": "white_wool",
}


def _material_base(n: str) -> str:
    if n.endswith("_bed"):
        return n.replace("_bed", "_wool")
    if n.endswith("_carpet"):
        return "moss_block" if n == "moss_carpet" else n.replace("_carpet", "_wool")
    if n.endswith("_pane"):
        return n.replace("_pane", "")
    for suf in _SUFIJOS_MATERIAL:
        if n.endswith(suf):
            base = n[: -len(suf)]
            for cand in (base, base + "s", base + "_planks", base + "_block", base.replace("brick", "bricks"),
                         base.replace("_brick", "_bricks"), "smooth_" + base, base + "_top"):
                if _png(cand) is not None:
                    return cand
            if base.endswith("smooth_quartz") or base == "quartz":
                return "quartz_block_top"
            if base == "smooth_stone":
                return "smooth_stone"
            return base
    return n


def textura(b: Block, cara: str) -> Image.Image:
    """cara: 'top' | 'side' | 'bottom'. Nunca devuelve None."""
    t = _textura(b, cara)
    return t if t is not None else _color_plano(b.name.removeprefix("minecraft:"))


def _textura(b: Block, cara: str) -> Image.Image:
    """cara: 'top' | 'side' | 'bottom'."""
    n = b.name.removeprefix("minecraft:")
    st = _st(b)
    n = _ESPECIALES.get(n, n)
    if n == "grass_block":
        if cara == "top":
            return _tintar(_png("grass_block_top"), TINTE_HIERBA)
        if cara == "side":
            base = _png("grass_block_side").copy()
            base.alpha_composite(_tintar(_png("grass_block_side_overlay"), TINTE_HIERBA))
            return base
        return _png("dirt")
    if n.endswith("_door"):
        return _png(f"{n}_{'top' if st.get('half') == 'upper' else 'bottom'}") or _color_plano(n)
    if n in ("water", "water_still"):
        return _tintar(_png("water_still") or _color_plano("water"), (63, 118, 228))
    if n.endswith("_leaves"):
        im = _png(n) or _color_plano(n)
        return im if n in ("cherry_leaves", "pale_oak_leaves", "azalea_leaves", "flowering_azalea_leaves") \
            else _tintar(im, TINTE_HOJAS)
    base = _material_base(n)
    eje = st.get("axis", "y")
    if base.endswith(("_log", "_stem", "_wood", "basalt", "pillar", "hay_block", "bone_block")) \
            or base in ("campfire_log",):
        tope = _png(base + "_top") or _png(base.replace("_wood", "_log")) or _png(base)
        lado = _png(base) or _png(base.replace("_wood", "_log"))
        if base.endswith("_wood"):
            tope = lado = _png(base.replace("_wood", "_log")) or lado
        if eje == "y":
            return tope if cara in ("top", "bottom") else lado
        return lado if cara in ("top", "bottom") else (tope if cara == "side_" + eje else lado)
    cands = {"top": [base + "_top", base], "bottom": [base + "_bottom", base + "_top", base],
             "side": [base + "_side", base + "_front", base]}[cara if cara in ("top", "bottom") else "side"]
    for c in cands:
        im = _png(c)
        if im is not None:
            return im
    return _color_plano(base)


# ------------------------------------------------------------------ geometría
def cajas(b: Block) -> list[tuple[float, float, float, float, float, float]]:
    """Subcajas (x0,y0,z0,x1,y1,z1) en [0,1] para dibujar el bloque."""
    n = b.name.removeprefix("minecraft:")
    st = _st(b)
    f = st.get("facing", "north")
    t = 1 / 16
    if n.endswith("_slab"):
        tipo = st.get("type", "bottom")
        return [(0, 0, 0, 1, 1, 1)] if tipo == "double" else [(0, 0.5 if tipo == "top" else 0, 0, 1, 1 if tipo == "top" else 0.5, 1)]
    if n.endswith("_stairs"):
        top = st.get("half") == "top"
        base = (0, 0.5, 0, 1, 1, 1) if top else (0, 0, 0, 1, 0.5, 1)
        y0, y1 = (0, 0.5) if top else (0.5, 1)
        paso = {"north": (0, y0, 0, 1, y1, 0.5), "south": (0, y0, 0.5, 1, y1, 1),
                "east": (0.5, y0, 0, 1, y1, 1), "west": (0, y0, 0, 0.5, y1, 1)}[f]
        forma = st.get("shape", "straight")
        if forma.startswith("outer"):
            izq = {"north": "west", "west": "south", "south": "east", "east": "north"}[f]
            lado = izq if forma == "outer_left" else {"north": "east", "east": "south", "south": "west", "west": "north"}[f]
            q = list(paso)
            if lado in ("east", "west"):
                q[0], q[3] = (0.5, 1) if lado == "east" else (0, 0.5)
            else:
                q[2], q[5] = (0.5, 1) if lado == "south" else (0, 0.5)
            return [base, tuple(q)]
        out = [base, paso]
        if forma.startswith("inner"):
            izq = {"north": "west", "west": "south", "south": "east", "east": "north"}[f]
            lado = izq if forma == "inner_left" else {"north": "east", "east": "south", "south": "west", "west": "north"}[f]
            extra = {"north": (0, y0, 0, 1, y1, 0.5), "south": (0, y0, 0.5, 1, y1, 1),
                     "east": (0.5, y0, 0, 1, y1, 1), "west": (0, y0, 0, 0.5, y1, 1)}[lado]
            out.append(extra)
        return out
    if n.endswith(("_pane", "_bars")):
        c = [(7 * t, 0, 7 * t, 9 * t, 1, 9 * t)]
        return c + _brazos(st, 7 * t, 9 * t, 0, 1)
    if n.endswith("_fence"):
        return [(6 * t, 0, 6 * t, 10 * t, 1, 10 * t)] + _brazos(st, 7 * t, 9 * t, 6 * t, 15 * t)
    if n.endswith("_wall") and "sign" not in n and "torch" not in n:
        return [(4 * t, 0, 4 * t, 12 * t, 1, 12 * t)] + _brazos(st, 5 * t, 11 * t, 0, 14 * t, wall=True)
    if n.endswith("_door"):
        o = GIRO180[f]  # el panel está en el lado opuesto al facing
        return [_lamina(o, 3 * t)]
    if n.endswith("_trapdoor"):
        if st.get("open") == "true":
            return [_lamina(GIRO180[f], 3 * t)]
        return [(0, 13 * t, 0, 1, 1, 1)] if st.get("half") == "top" else [(0, 0, 0, 1, 3 * t, 1)]
    if n.endswith("_fence_gate"):
        if f in ("north", "south"):
            return [(0, 5 * t, 7 * t, 1, 1, 9 * t)]
        return [(7 * t, 5 * t, 0, 9 * t, 1, 1)]
    if n.endswith("_carpet"):
        return [(0, 0, 0, 1, t, 1)]
    if n.endswith("_bed"):
        return [(0, 3 * t, 0, 1, 9 * t, 1)]
    if n.endswith("lantern"):
        return [(5 * t, (1 if st.get("hanging") == "true" else 0) * t, 5 * t, 11 * t, 8 * t, 11 * t)]
    if n.endswith("torch"):
        return [(7 * t, 0, 7 * t, 9 * t, 10 * t, 9 * t)]
    if n.endswith(("chest",)):
        return [(t, 0, t, 15 * t, 14 * t, 15 * t)]
    if n.endswith("campfire"):
        return [(0, 0, 0, 1, 7 * t, 1)]
    if n.endswith(("_pressure_plate",)):
        return [(t, 0, t, 15 * t, t, 15 * t)]
    if n in ("chain", "iron_chain") or n.endswith("_chain"):
        return [(7 * t, 0, 7 * t, 9 * t, 1, 9 * t)]
    if n.endswith(("_flower", "_sapling", "_tulip", "poppy", "dandelion", "fern", "short_grass", "tall_grass", "_orchid",
                   "allium", "azure_bluet", "oxeye_daisy", "cornflower", "lily_of_the_valley")):
        return [(4 * t, 0, 4 * t, 12 * t, 12 * t, 12 * t)]
    if n == "ladder" or n.endswith(("_sign", "_banner", "_button", "lever", "vine")):
        return [_lamina(GIRO180.get(f, "north"), 2 * t)]
    return [(0, 0, 0, 1, 1, 1)]


def _lamina(lado: str, g: float):
    return {"north": (0, 0, 0, 1, 1, g), "south": (0, 0, 1 - g, 1, 1, 1),
            "west": (0, 0, 0, g, 1, 1), "east": (1 - g, 0, 0, 1, 1, 1)}[lado]


def _brazos(st, a, b, y0, y1, wall=False):
    out = []
    for d, caja in (("north", (a, y0, 0, b, y1, a)), ("south", (a, y0, b, b, y1, 1)),
                    ("west", (0, y0, a, a, y1, b)), ("east", (b, y0, a, 1, y1, b))):
        v = st.get(d, "false")
        if v in ("true", "low", "tall"):
            c = list(caja)
            if wall and v == "low":
                c[4] = 14 / 16
            if wall and v == "tall":
                c[4] = 1
            out.append(tuple(c))
    return out


def es_cubo_opaco(b: Block) -> bool:
    n = b.name.removeprefix("minecraft:")
    if n == "air" or any(k in n for k in TRANSPARENTES):
        return False
    return cajas(b) == [(0, 0, 0, 1, 1, 1)]


def girar180(b: Block) -> Block:
    st = _st(b)
    if not st:
        return b
    nuevo = {}
    for k, v in st.items():
        if k == "facing":
            v = GIRO180.get(v, v)
        if k == "shape" and v.endswith(("_left", "_right")):
            pass  # izquierda/derecha son relativas al facing: no cambian al girar
        nuevo[GIRO180.get(k, k) if k in GIRO180 else k] = v
    return Block.from_mapping(b.name, nuevo)


# ------------------------------------------------------------------ dibujo
def _cara(lienzo, tex, p0, pu, pv, uv, brillo):
    """Proyecta tex (recortada a uv=(u0,v0,u1,v1) en píxeles 0..16) al paralelogramo p0 + s*pu + t*pv."""
    u0, v0, u1, v1 = uv
    w = max(1, int(round(u1 - u0))); h = max(1, int(round(v1 - v0)))
    sub = tex.crop((int(u0), int(v0), int(u0) + w, int(v0) + h))
    if brillo != 1:
        a = np.asarray(sub).astype(np.float32); a[..., :3] *= brillo
        sub = Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGBA")
    xs = [p0[0], p0[0] + pu[0], p0[0] + pv[0], p0[0] + pu[0] + pv[0]]
    ys = [p0[1], p0[1] + pu[1], p0[1] + pv[1], p0[1] + pu[1] + pv[1]]
    bx0, by0 = int(math.floor(min(xs))), int(math.floor(min(ys)))
    bx1, by1 = int(math.ceil(max(xs))) + 1, int(math.ceil(max(ys))) + 1
    if bx1 - bx0 < 1 or by1 - by0 < 1:
        return
    # matriz de pantalla->textura: [x-ox, y-oy] = s*pu + t*pv
    det = pu[0] * pv[1] - pu[1] * pv[0]
    if abs(det) < 1e-6:
        return
    ox, oy = p0[0] - bx0, p0[1] - by0
    ia, ib = pv[1] / det, -pv[0] / det
    ic, id_ = -pu[1] / det, pu[0] / det
    # s = ia*(x-ox) + ib*(y-oy) ; t = ic*(x-ox) + id*(y-oy)  -> en píxeles de sub: *w, *h
    coef = (ia * w, ib * w, -(ia * ox + ib * oy) * w, ic * h, id_ * h, -(ic * ox + id_ * oy) * h)
    parche = sub.transform((bx1 - bx0, by1 - by0), Image.AFFINE, coef, resample=Image.NEAREST)
    # máscara exacta del paralelogramo para no "sangrar" texturas por los bordes
    m = Image.new("L", parche.size, 0)
    ImageDraw.Draw(m).polygon([(p0[0] - bx0, p0[1] - by0), (p0[0] + pu[0] - bx0, p0[1] + pu[1] - by0),
                               (p0[0] + pu[0] + pv[0] - bx0, p0[1] + pu[1] + pv[1] - by0),
                               (p0[0] + pv[0] - bx0, p0[1] + pv[1] - by0)], fill=255)
    alfa = Image.fromarray(np.minimum(np.asarray(parche)[..., 3], np.asarray(m)))
    parche.putalpha(alfa)
    lienzo.alpha_composite(parche, (bx0, by0))


def iso(data: np.ndarray, bloques: list[Block], escala: int = 12, girar: bool = False,
        recorte_y: int | None = None) -> Image.Image:
    """Vista isométrica desde el sureste (o noroeste si girar=True)."""
    if girar:
        data = data[::-1, :, ::-1]
        bloques = [girar180(b) for b in bloques]
    if recorte_y is not None:
        data = data[:, :recorte_y, :]
    sx, sy, sz = data.shape
    opaco = np.array([es_cubo_opaco(b) for b in bloques])
    S = escala
    cx, cy = S * math.cos(math.radians(30)), S * 0.5
    ancho = int((sx + sz) * cx) + 4 * S
    alto = int((sx + sz) * cy + sy * S) + 4 * S
    lienzo = Image.new("RGBA", (ancho, alto), (0, 0, 0, 0))
    org = (sz * cx + 2 * S, sy * S + 2 * S)

    def P(x, y, z):
        return (org[0] + (x - z) * cx, org[1] + (x + z) * cy - y * S)

    op = opaco[data]
    vacio = data == 0
    pad = np.pad(op, 1, constant_values=False)
    tapa_arriba = pad[1:-1, 2:, 1:-1]
    tapa_este = pad[2:, 1:-1, 1:-1]
    tapa_sur = pad[1:-1, 1:-1, 2:]
    visibles = ~vacio & ~(op & tapa_arriba & tapa_este & tapa_sur)
    xs, ys, zs = np.nonzero(visibles)
    orden = np.lexsort((ys, xs + zs + ys))  # pintor: de atrás hacia delante
    cache = {}
    for k in orden:
        x, y, z = int(xs[k]), int(ys[k]), int(zs[k])
        i = int(data[x, y, z])
        if i not in cache:
            b = bloques[i]
            cache[i] = (b, cajas(b), textura(b, "top"), textura(b, "side"),
                        textura(b, "side_x") if _st(b).get("axis") in ("x", "z") else None,
                        textura(b, "side_z") if _st(b).get("axis") in ("x", "z") else None)
        b, cs, ttop, tside, tsx, tsz = cache[i]
        for (a0, b0, c0, a1, b1, c1) in sorted(cs, key=lambda c: c[0] + c[1] + c[2] + c[3] + c[4] + c[5]):
            X0, Y0, Z0, X1, Y1, Z1 = x + a0, y + b0, z + c0, x + a1, y + b1, z + c1
            px = 16
            # cara sur (+z): u a lo largo de x, v hacia abajo
            if not (tapa_sur[x, y, z] and c1 == 1):
                _cara(lienzo, tsz or tside, P(X0, Y1, Z1), _v(P, X1 - X0, 0, 0), _v(P, 0, -(Y1 - Y0), 0),
                      (a0 * px, (1 - b1) * px, a1 * px, (1 - b0) * px), 0.62)
            # cara este (+x): u a lo largo de -z
            if not (tapa_este[x, y, z] and a1 == 1):
                _cara(lienzo, tsx or tside, P(X1, Y1, Z1), _v(P, 0, 0, -(Z1 - Z0)), _v(P, 0, -(Y1 - Y0), 0),
                      ((1 - c1) * px, (1 - b1) * px, (1 - c0) * px, (1 - b0) * px), 0.8)
            # cara superior
            if not (tapa_arriba[x, y, z] and b1 == 1):
                _cara(lienzo, ttop, P(X0, Y1, Z0), _v(P, X1 - X0, 0, 0), _v(P, 0, 0, Z1 - Z0),
                      (a0 * px, c0 * px, a1 * px, c1 * px), 1.0)
    return _recortar(lienzo)


def _v(P, dx, dy, dz):
    a = P(0, 0, 0); b = P(dx, dy, dz)
    return (b[0] - a[0], b[1] - a[1])


def _recortar(im: Image.Image) -> Image.Image:
    bb = im.getbbox()
    return im.crop(bb) if bb else im


def planta(data: np.ndarray, bloques: list[Block], escala: int = 16, corte_y: int | None = None) -> Image.Image:
    """Vista cenital: el bloque visible más alto en cada columna (por debajo de corte_y)."""
    if corte_y is not None:
        data = data[:, :corte_y, :]
    sx, sy, sz = data.shape
    im = Image.new("RGBA", (sx * escala, sz * escala), (0, 0, 0, 0))
    for x in range(sx):
        for z in range(sz):
            col = data[x, :, z]
            nz = np.nonzero(col)[0]
            if not len(nz):
                continue
            y = int(nz[-1])
            b = bloques[int(col[y])]
            t = textura(b, "top").resize((escala, escala), Image.NEAREST)
            sombra = 0.55 + 0.45 * (y + 1) / sy
            a = np.asarray(t).astype(np.float32); a[..., :3] *= sombra
            im.alpha_composite(Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGBA"), (x * escala, z * escala))
    return im


def _fuente(t=16):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",):
        if Path(p).exists():
            return ImageFont.truetype(p, t)
    return ImageFont.load_default()


def lamina_completa(data: np.ndarray, bloques: list[Block], titulo: str, out: Path,
                    niveles: list[int] | None = None) -> Path:
    """Compone una lámina: iso SE + iso NO arriba; planta + cortes por nivel abajo."""
    sx, sy, sz = data.shape
    esc = max(4, min(16, int(900 / max(sx + sz, 1))))
    a = iso(data, bloques, esc)
    b = iso(data, bloques, esc, girar=True)
    escp = max(4, min(16, int(420 / max(sx, sz))))
    paneles = [("Cenital", planta(data, bloques, escp))]
    for y in (niveles or []):
        paneles.append((f"Interior y={y}", planta(data, bloques, escp, corte_y=y + 1)))
    f = _fuente(18); fs = _fuente(14)
    fila1_h = max(a.height, b.height) + 30
    fila2_h = max(p.height for _, p in paneles) + 30
    ancho = max(a.width + b.width + 60, sum(p.width for _, p in paneles) + 30 * (len(paneles) + 1))
    lam = Image.new("RGBA", (ancho, fila1_h + fila2_h + 50), (236, 238, 242, 255))
    d = ImageDraw.Draw(lam)
    d.text((20, 12), titulo, fill=(30, 30, 30), font=f)
    lam.alpha_composite(a, (20, 50)); d.text((20, 40 + a.height + 12), "Sureste (fachada sur = Z max)", fill=(60, 60, 60), font=fs)
    lam.alpha_composite(b, (40 + a.width, 50)); d.text((40 + a.width, 40 + b.height + 12), "Noroeste", fill=(60, 60, 60), font=fs)
    x = 20
    for nombre, p in paneles:
        y0 = fila1_h + 40
        lam.alpha_composite(p, (x, y0)); d.text((x, y0 + p.height + 4), nombre + "  (arriba = norte)", fill=(60, 60, 60), font=fs)
        x += p.width + 30
    lam.convert("RGB").save(out)
    return out


# ------------------------------------------------------------------ vistas rápidas (construcciones grandes)
_COLOR_CACHE: dict = {}


def color_medio(b: Block, cara="top"):
    k = (b, cara)
    if k not in _COLOR_CACHE:
        n = b.name.removeprefix("minecraft:")
        if n in ("air", "cave_air", "void_air"):
            _COLOR_CACHE[k] = (0, 0, 0, 0)
        else:
            a = np.asarray(textura(b, cara).convert("RGBA")).reshape(-1, 4).astype(float)
            a = a[a[:, 3] > 0]
            c = a[:, :3].mean(0) if len(a) else np.array([128, 128, 128])
            _COLOR_CACHE[k] = (*c.astype(int), 255)
    return _COLOR_CACHE[k]


def planta_rapida(data: np.ndarray, bloques: list[Block], escala: int = 2, corte_y: int | None = None,
                  aire: int = 0) -> Image.Image:
    """Vista cenital, 1 color por columna, sombreado por altura y por bordes (rápida para mapas grandes)."""
    if corte_y is not None:
        data = data[:, :corte_y, :]
    sx, sy, sz = data.shape
    nz = data != aire
    tiene = nz.any(1)
    ytop = np.where(tiene, sy - 1 - np.argmax(nz[:, ::-1, :], axis=1), -1)
    idx = np.take_along_axis(data, np.clip(ytop, 0, None)[:, None, :], 1)[:, 0, :]
    lut = np.array([color_medio(b) for b in bloques], dtype=np.float64)
    img = lut[idx]
    img[~tiene] = (0, 0, 0, 0)
    # sombreado tipo mapa: más claro si está más alto que el vecino del noroeste
    h = ytop.astype(float)
    dif = h - np.pad(h, ((1, 0), (1, 0)), mode="edge")[:-1, :-1]
    f = np.clip(1 + 0.06 * dif, 0.7, 1.25)
    base = 0.8 + 0.2 * (h + 1) / max(sy, 1)
    img[..., :3] *= (f * base)[..., None]
    im = Image.fromarray(img.clip(0, 255).astype(np.uint8).transpose(1, 0, 2), "RGBA")
    return im.resize((sx * escala, sz * escala), Image.NEAREST)
