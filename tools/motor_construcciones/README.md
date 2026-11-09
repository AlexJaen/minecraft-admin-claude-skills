# 🏗️ Motor de construcciones

Genera construcciones de Minecraft como **schematics `.schem`** (Sponge v3) listos para FAWE/WorldEdit: diseño por código con piezas de alto nivel, validación de bloques, conexiones calculadas, simetría comprobada automáticamente y vistas previas con texturas reales.

Las reglas de diseño (simetría, paridad, decoración, procedimiento) están en la skill [`constructor-minecraft`](../../skills/constructor-minecraft/SKILL.md). Este paquete es la parte de código.

## Instalación (Linux / espacio de trabajo de Claude)

```bash
bash setup.sh
```

Instala dependencias de Python, descarga **Schematica** (fijada a un commit), el catálogo de bloques 26.1 y las texturas 1.21.11 de PrismarineJS, y hace una prueba (casa de ejemplo en `salidas/casa_prueba/`). Necesita `git`, `python3` (>= 3.10) y acceso a GitHub. `vendor/`, `assets/` y `salidas/` se generan y no se suben al repositorio.

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

`builds/casa_prueba.py`: casa pequeña con piezas (`python3 builds/casa_prueba.py`). Salida en `salidas/casa_prueba/` (`.schem`, vista previa y lista de materiales).

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
- **Schematica** (descargada por `setup.sh`, no incluida aquí) no declara licencia: uso personal. El texto de `setup.sh` la clona en tu máquina, este repositorio no la redistribuye.
