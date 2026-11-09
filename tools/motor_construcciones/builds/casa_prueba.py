"""Casa medieval de prueba: planta 11x9, zócalo de piedra, entramado de abeto, tejado de roble oscuro."""
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import rutas  # noqa: E402,F401
import sys
from motor import nueva, exportar
from piezas import bloque, caja, muros, postes, puerta, tejado_dos_aguas, ventana, viga_perimetral

s = nueva(15, 13, 13)
x0, x1, z0, z1 = 2, 12, 2, 10       # muros exteriores 11 x 9
cx = 7                               # eje de la puerta

# Cimiento + suelo
caja(s, x0, 0, z0, x1, 0, z1, "minecraft:cobblestone")
caja(s, x0 + 1, 0, z0 + 1, x1 - 1, 0, z1 - 1, "minecraft:spruce_planks")
# Muros: zócalo de piedra + entramado
muros(s, x0, 1, z0, x1, 1, z1, "minecraft:stone_bricks")
muros(s, x0, 2, z0, x1, 4, z1, "minecraft:white_terracotta")
postes(s, [(x0, z0), (x1, z0), (x0, z1), (x1, z1), (cx, z0), (cx, z1)], 1, 4, "minecraft:spruce_log[axis=y]")
viga_perimetral(s, x0, 5, z0, x1, z1, "minecraft:spruce_log")
# Tejado (cumbrera E-O) con hastiales de tablones
cumbre = tejado_dos_aguas(s, x0, z0, x1, z1, 5, "dark_oak", cumbrera="x", hastial="minecraft:spruce_planks")

# Chimenea (oeste)
caja(s, x0 - 1, 0, 5, x0 - 1, cumbre + 1, 6, "minecraft:cobblestone")
caja(s, x0 - 1, cumbre + 2, 5, x0 - 1, cumbre + 2, 6, "minecraft:cobblestone_wall")

# Puerta sur + escalón + farolillos
puerta(s, cx, 2, z1, "spruce", mira="south")
bloque(s, cx, 1, z1, "minecraft:spruce_planks")
bloque(s, cx, 0, z1 + 1, "minecraft:cobblestone_stairs[facing=north]")
for x in (cx - 1, cx + 1):
    bloque(s, x, 3, z1 + 1, "minecraft:spruce_fence")
    bloque(s, x, 4, z1 + 1, "minecraft:lantern[hanging=false]")

# Ventanas con contraventanas y jardinera
for x in (4, 10):
    for z, cara in ((z0, "north"), (z1, "south")):
        ventana(s, x, 3, z)
        zf = z - 1 if cara == "north" else z + 1
        for dx in (-1, 1):
            bloque(s, x + dx, 3, zf, f"minecraft:spruce_trapdoor[facing={cara},half=bottom,open=true]")
        bloque(s, x, 2, zf, f"minecraft:spruce_trapdoor[facing={cara},half=top,open=false]")
for z in (5, 7):
    ventana(s, x1, 3, z)
bloque(s, 4, 3, z1 + 1, "minecraft:poppy")
bloque(s, 10, 3, z1 + 1, "minecraft:dandelion")

# Interior
caja(s, x0 + 1, 5, 6, x1 - 1, 5, 6, "minecraft:spruce_log[axis=x]")      # viga central
bloque(s, cx, 4, 6, "minecraft:lantern[hanging=true]")
bloque(s, x0 + 1, 1, z0 + 1, "minecraft:crafting_table")
bloque(s, x0 + 2, 1, z0 + 1, "minecraft:furnace[facing=south]")
caja(s, x0 + 1, 1, 5, x0 + 1, 1, 6, "minecraft:campfire[lit=false,facing=east]")
caja(s, x1 - 2, 1, z0 + 1, x1 - 1, 1, z0 + 1, "minecraft:barrel[facing=up]")
bloque(s, x1 - 1, 1, z0 + 2, "minecraft:chest[facing=west]")
bloque(s, x1 - 1, 1, z1 - 2, "minecraft:red_bed[facing=north,part=foot]")
bloque(s, x1 - 1, 1, z1 - 3, "minecraft:red_bed[facing=north,part=head]")
caja(s, x0 + 3, 1, 5, x0 + 5, 1, 7, "minecraft:brown_carpet")

print(exportar(s, "casa_prueba", anclaje="entrada_sur", hundir=1, niveles=[1]))
