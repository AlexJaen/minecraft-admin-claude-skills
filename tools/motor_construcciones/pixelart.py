"""Imagen -> pixel art de bloques (pared vertical en el plano XY, mirando al sur)."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parent))
import rutas  # noqa: E402,F401
import render

# Bloques de color uniforme, buenos para pixel art (sin caras distintas ni transparencias)
COLORES = ["white", "light_gray", "gray", "black", "brown", "red", "orange", "yellow", "lime", "green",
           "cyan", "light_blue", "blue", "purple", "magenta", "pink"]
PALETA = ([f"{c}_concrete" for c in COLORES] + [f"{c}_wool" for c in COLORES] +
          [f"{c}_terracotta" for c in COLORES] +
          ["terracotta", "quartz_block", "smooth_stone", "stone", "dirt", "coarse_dirt", "moss_block",
           "purpur_block", "amethyst_block", "obsidian", "crying_obsidian", "snow_block", "oak_planks",
           "spruce_planks", "dark_oak_planks", "birch_planks", "mud", "packed_mud", "deepslate_tiles",
           "polished_blackstone", "nether_bricks", "calcite", "dripstone_block",
           "white_glazed_terracotta"][:-1])


def _lab(rgb):
    c = np.asarray(rgb, dtype=np.float64) / 255.0
    c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    m = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = c @ m.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def colores_paleta(nombres=PALETA):
    from schematica.blocks.block import Block
    out = {}
    for n in nombres:
        t = render.textura(Block.parse("minecraft:" + n), "side")
        if t is None:
            continue
        a = np.asarray(t.convert("RGBA")).reshape(-1, 4)
        a = a[a[:, 3] > 0][:, :3]
        out[n] = a.mean(0)
    return out


def cuantizar(img: Image.Image, ancho: int, nombres=PALETA, umbral_alfa=110):
    """Devuelve matriz [fila][col] de nombres de bloque (None = transparente)."""
    alto = round(img.height * ancho / img.width)
    peq = img.convert("RGBA").resize((ancho, alto), Image.BOX)
    a = np.asarray(peq).astype(np.float64)
    pal = colores_paleta(nombres)
    claves = list(pal)
    plab = _lab(np.array([pal[k] for k in claves]))
    lab = _lab(a[..., :3])
    d = ((lab[:, :, None, :] - plab[None, None, :, :]) ** 2).sum(-1)
    idx = d.argmin(-1)
    res = [[claves[idx[y, x]] if a[y, x, 3] >= umbral_alfa else None for x in range(ancho)] for y in range(alto)]
    return res


def frontal(matriz, escala=16) -> Image.Image:
    """Vista frontal con texturas reales."""
    from schematica.blocks.block import Block
    h, w = len(matriz), len(matriz[0])
    im = Image.new("RGBA", (w * escala, h * escala), (0, 0, 0, 0))
    cache = {}
    for y, fila in enumerate(matriz):
        for x, n in enumerate(fila):
            if n:
                if n not in cache:
                    cache[n] = render.textura(Block.parse("minecraft:" + n), "side").resize((escala, escala), Image.NEAREST)
                im.alpha_composite(cache[n], (x * escala, y * escala))
    return im


def por_regiones(img: Image.Image, ancho: int, reglas=None, umbral_alfa=128):
    """Cuantización por regiones semánticas (tono/saturación/brillo): da zonas limpias,
    sin el moteado de buscar el bloque más parecido píxel a píxel."""
    import colorsys
    alto = round(img.height * ancho / img.width)
    a = np.asarray(img.convert("RGBA").resize((ancho, alto), Image.BOX)).astype(np.float64)
    res = []
    for y in range(alto):
        fila = []
        for x in range(ancho):
            r, g, b, al = a[y, x]
            if al < umbral_alfa:
                fila.append(None); continue
            h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            fila.append(reglas(h * 360, s, v))
        res.append(fila)
    return res
