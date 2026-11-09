# 🏗️ Motor de construcciones

Genera construcciones de Minecraft como **schematics `.schem`** (Sponge v3) listos para FAWE/WorldEdit: diseño por código con piezas de alto nivel, validación de bloques, conexiones calculadas, simetría comprobada automáticamente y vistas previas con texturas reales.

Las reglas de diseño (simetría, paridad, decoración, procedimiento) están en la skill [`constructor-minecraft`](../../skills/constructor-minecraft/SKILL.md). Este paquete es la parte de código.

## Instalación (Windows, Linux o macOS)

Necesitas **Python 3.10 o superior** y **git** (solo la primera vez). Desde la carpeta `tools/motor_construcciones`:

```
python instalar.py          # en Windows también: py instalar.py
```

Qué hace, paso a paso:

1. Comprueba la versión de Python.
2. Comprueba `numpy` y `Pillow` (casi siempre vienen instalados) e instala `nbtlib` desde `wheels/`, sin conexión.
3. Comprueba los datos del motor: **Schematica** (base de diseño), el **catálogo de bloques 26.1** y las **texturas** de bloques. Si faltan, los **descarga con git** (Schematica fijada a un commit, texturas con *sparse checkout*) en `vendor/` y `assets/`. Esos dos directorios no se incluyen en este repositorio: Schematica no declara licencia y las texturas son de Mojang.
4. Genera una casa de prueba en `salidas/casa_prueba/` y termina con `LISTO`, o marca con `[FALTA]` lo que no esté y cómo resolverlo.

Opciones: `--comprobar` (solo revisa, no instala), `--sin-prueba` (no genera la casa de prueba) y `--sin-descarga` (no descarga nada).

**Sin conexión:** si ya tienes una copia completa del paquete (con `vendor/` y `assets/` dentro), el instalador no necesita internet. Cópiala tal cual a la máquina sin red. Solo haría falta conexión si falta `numpy` o `Pillow`; en ese caso copia sus `.whl` a `wheels/`.

> La descarga de Schematica y de las texturas no está probada en todos los sistemas: si falla, el instalador te muestra el error de git. Los datos bajan solo a tu equipo; no se vuelven a subir al repositorio (`vendor/`, `assets/` y `salidas/` están en el `.gitignore`).

## Módulos

| Módulo | Para qué |
|---|---|
| `lienzo.py` | `Lienzo(ancho, alto, largo)`: lienzo rápido (numpy). `caja`, `vaciar`, `set`, `get`, `muros`, `marco`, `disco`, `octogono`, `linea`, `spawner(x,y,z,mob)`. |
| `decor.py` | `Deco(lienzo, F)`: catálogo de decoración centrado y simétrico: `farola_a`, `farola_b`, `baliza`, `banco`, `maceta`, `jardinera`, `arbusto`, `cerezo`, `parterre`, `obelisco`, `antena`, `estandarte`, `fuente`. |
| `piezas.py` | Piezas para sesiones pequeñas: `muros`, `puerta`, `ventana`, `tejado_dos_aguas`, `viga_perimetral`... |
| `simetria.py` | `centro(a0,a1)` (falla si el tramo es par), `assert_centrado`, `espejar_x(lienzo, cx)`, `diferencias_espejo`, `clave`, `rc/rs` (redondeo polar simétrico: usar SIEMPRE en círculos). |
| `conexiones.py` | Recalcula paneles, vallas, muros, barrotes y forma de escaleras (FAWE pega sin físicas). Se aplica solo al exportar. |
| `motor.py` | `exportar(s, nombre, anclaje=..., hundir=..., offset=..., con_vistas=...)`: valida bloques contra el catálogo, recalcula conexiones, escribe Sponge v3, relee y compara, lista de materiales. |
| `render.py` | `iso` (isométrica con texturas), `planta`, `planta_rapida` (mapas grandes), `lamina_completa`. |
| `pixelart.py` | Imagen -> bloques (`cuantizar`, `por_regiones`, `frontal`). |
| `rutas.py` | Rutas relativas al paquete (o a la variable `MOTOR_BASE`). |

## Ejemplo

`builds/casa_prueba.py`: casa pequeña con piezas (`python builds/casa_prueba.py`). Salida en `salidas/casa_prueba/` (`.schem`, vista previa y lista de materiales).

## Flujo resumido

1. Plano en constantes (ejes impares) + `assert_centrado` de cada zona.
2. Construir con `Lienzo` + `Deco`; lo simétrico, en una mitad y `espejar_x`.
3. Zonas asimétricas justificadas, después del espejo.
4. Comprobar (`diferencias_espejo`) y exportar con `motor.exportar`.
5. Revisar vistas (`render.planta_rapida` para el conjunto, `render.iso` por zonas).
6. Copiar el `.schem` a la carpeta `schematics` de FAWE y **verificar el hash** en destino (con nombre de origen único: una copia con el mismo nombre puede reutilizar una versión anterior).

## Notas

- `DATA_VERSION` está fijada en `motor.py` (4903, Minecraft 26.x); cámbiala si tu servidor usa otra versión.
- `Offset` = esquina mínima respecto a los pies del jugador al pegar.
- Hojas siempre `persistent=true`; spawners con `SpawnData`; estados normalizados.
- **Schematica** (descargada por `instalar.py`, no incluida aquí) no declara licencia: uso personal. El instalador la clona en tu máquina; este repositorio no la redistribuye.
