<h1 align="center">🧰 Minecraft Admin — Claude Skills</h1>
<p align="center"><b>Skills y herramientas para administrar un servidor Minecraft (Paper) con Claude.</b><br>Flujo de trabajo con changelog, análisis de logs, caza de dupes con CoreProtect y constructor de schematics.</p>

<p align="center">
  <img alt="Version" src="https://img.shields.io/badge/version-1.0.0-blue">
  <img alt="Paper" src="https://img.shields.io/badge/Paper-1.21.x%20%7C%2026.x-success">
  <img alt="Skills" src="https://img.shields.io/badge/skills-3-purple">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-lightgrey">
</p>

> 🇬🇧 *English summary at the bottom.* Las skills están escritas en **español** (responden en el idioma del usuario); son texto plano y fáciles de traducir.

## ¿Qué incluye?

| Pieza | Para qué sirve |
|---|---|
| 🛠️ **`servidor-minecraft`** | Flujo estándar para cualquier cambio en tus servidores: **orientarse → cambiar → avisar de recompilar/desplegar → registrar en `docs/CHANGELOG.md`**. Incluye buenas prácticas para plugins Paper (eventos, async, PDC, items y dinero). |
| 📜 **`analisis-logs-minecraft`** | Cómo leer un `latest.log`: acotar por hora y jugador, distinguir ruido de problemas, búsquedas `grep` útiles y casos típicos (items perdidos, plugins que no cargan, caídas). |
| 🏗️ **`constructor-minecraft`** | Principios de simetría, paridad, proporción y detalle para generar **schematics** y construcciones, con comprobaciones automáticas antes de entregar. |
| 🧱 **`tools/motor_construcciones`** | Motor Python que genera **schematics `.schem`** (Sponge v3) con lienzo, decoración simétrica, validación de bloques, vistas previas y comprobación de ida y vuelta. Es la parte de código de `constructor-minecraft`. |
| 🔎 **`tools/exploit_hunt`** | Script Python (solo lectura) que caza **dupes** y repartos de items en la base de datos de CoreProtect. |
| 📄 **`templates/`** | Plantillas listas para tu proyecto: `CLAUDE.md` (mapa del servidor), `EXPLOITS.md` (checklist de código seguro + cómo cazar + caso real) y `CHANGELOG.md`. |

## Instalación

### Opción A — copiar las skills (la más sencilla)
Copia las carpetas de `skills/` a la carpeta de skills de tu cliente de Claude (por ejemplo `~/.claude/skills/` en Claude Code, o impórtalas desde la sección de Skills de la app de escritorio):

```bash
git clone https://github.com/AlexJaen/minecraft-admin-claude-skills.git
cp -r minecraft-admin-claude-skills/skills/* ~/.claude/skills/
```

### Opción B — como plugin (Claude Code)
```
/plugin marketplace add AlexJaen/minecraft-admin-claude-skills
/plugin install minecraft-server-admin@minecraft-admin-claude-skills
```
*(Opción B sin probar en todas las versiones del cliente; si falla, usa la A.)*

### Instalar el motor de construcciones (opcional)

Necesita Python 3.10+ y git (solo la primera vez, para bajar Schematica y las texturas):

```bash
cd tools/motor_construcciones
python instalar.py          # Windows: py instalar.py
```

Comprueba las dependencias, instala `nbtlib` desde el propio repositorio, descarga los datos que falten y genera una casa de prueba (`LISTO` si todo va bien). Detalles, opciones y uso sin conexión en [`tools/motor_construcciones/README.md`](tools/motor_construcciones/README.md).

## Puesta en marcha en tu proyecto

1. Copia `templates/CLAUDE.md` a la raíz de tu proyecto y rellena la tabla de servidores y las reglas.
2. Copia `templates/EXPLOITS.md` y `templates/CHANGELOG.md` a `docs/`.
3. Pídele a Claude cualquier cosa sobre tus servidores: la skill `servidor-minecraft` se activa sola, lee el `CLAUDE.md` y registra cada cambio en el changelog.

## `exploit_hunt` en 30 segundos

```bash
export COREPROTECT_DB=/ruta/a/plugins/CoreProtect/database.db   # trabaja sobre una copia si el servidor está encendido
python tools/exploit_hunt/hunt.py doubling 09-20     # cadenas de pickups que se doblan (1,2,4,8…)
python tools/exploit_hunt/hunt.py shulker 09-25      # rotura de shulker + bloque adyacente en <1 s
python tools/exploit_hunt/hunt.py dist <usuario>     # a quién reparte un jugador
```
Detalles y cómo interpretar los resultados en [`tools/exploit_hunt/README.md`](tools/exploit_hunt/README.md) y [`templates/EXPLOITS.md`](templates/EXPLOITS.md).

## Filosofía

- **Registrar siempre**: cada cambio queda en el changelog con su etiqueta (`[R]` recompilar, `[C]` config, `[G]` comando, `[X]` reinicio).
- **Honestidad sobre el despliegue**: nunca dar por "vivo" un cambio de código sin compilar y probar; la copia local puede diferir de la del hosting.
- **Seguridad primero con items y dinero**: antes de tocar código que mueva items, llaves o monedas, leer el checklist de `EXPLOITS.md`.

## Contribuir
Issues y PRs bienvenidos: nuevas búsquedas de logs, firmas de exploits, reglas de la skill de construcción, traducciones.

## Licencia
MIT — ver [LICENSE](LICENSE).

---

### 🇬🇧 English summary

Three Claude skills + tools for Minecraft (Paper) server admins: a **workflow** skill (orient → change → warn about rebuild/deploy → log in a changelog), a **log-analysis** skill, a **builder** skill (symmetry/parity rules and automated checks for schematics), a read-only **CoreProtect dupe hunter** (Python) and ready-to-use project templates. Skills are written in Spanish and reply in the user's language. Install by copying `skills/*` into your Claude skills folder, or as a plugin from this repo.
