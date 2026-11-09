# CLAUDE.md — mapa rápido del proyecto (leer primero)

Idioma de trabajo: **<tu idioma>**. Respuestas concisas. Modo "auto": tomar decisiones razonables, preguntar solo ante un bloqueo real.
**Al terminar cada cambio relevante, actualizar `docs/CHANGELOG.md`** (y este mapa si cambia la estructura).

## 1. Servidores (cada carpeta = un servidor/proceso)

| Carpeta | Qué es | Versión | Puerto | Notas |
|---|---|---|---|---|
| `proxy/` | Velocity/BungeeCord (entrada pública) | | 25565 | |
| `lobby/` | Lobby + login | Paper x.y.z | | |
| `survival/` | … | Paper x.y.z | | |

Para saber qué hay realmente en un servidor: `ls <carpeta>/plugins/*.jar` y `<carpeta>/logs/latest.log`.

## 2. Código propio (plugins)

- Dónde está el código fuente de cada plugin, cómo se compila (Maven/Gradle, JDK) y a qué carpeta se despliega el jar.
- Si hay una copia del mismo plugin por versión de Minecraft, indicar cuál es la fuente de verdad y cómo sincronizarlas.

## 3. Reglas de trabajo (aprendidas)

1. Si el entorno no puede compilar Java: editar con cuidado, avisar **siempre** de recompilar (comando, dónde queda el jar, dónde copiarlo). No dar por "vivo" un cambio sin que el usuario haya compilado.
2. Distinguir config vs código al responder ("solo config" / "hay que recompilar") y si requiere reinicio.
3. Plugins que sobrescriben su config al guardar (WorldGuard, LuckPerms…): dar los comandos al usuario en lugar de editar el fichero con el servidor encendido.
4. Antes de escribir en una carpeta, listar/leer lo que hay.
5. Antes de crear un plugin propio nuevo: buscar uno existente y **preguntar**.
6. Un único jar por plugin (si hay dos, Paper carga uno aleatorio).
7. Si el servidor real está en un hosting externo, la copia local puede diferir: pedir comprobaciones (`/plugins`, `/version`).

## 3b. Skills instaladas (usarlas por iniciativa propia)
- `servidor-minecraft` → cualquier cambio/diagnóstico/despliegue. `analisis-logs-minecraft` → logs. `constructor-minecraft` → schematics/construcciones.

## 4. Documentación

- `docs/CHANGELOG.md` — historial de cambios.
- `docs/PENDIENTE.md` — tareas abiertas.
- `docs/EXPLOITS.md` — registro de exploits/dupes y checklist de código seguro. **Leerlo antes de tocar código que mueva items/llaves/dinero.**
