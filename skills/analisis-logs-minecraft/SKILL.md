---
name: "analisis-logs-minecraft"
description: "Úsala cuando el usuario suba o mencione un log de un servidor Minecraft (latest*.log, crash, consola) o pregunte qué pasó: muertes, items perdidos, bosses, errores de plugins, arranque, lag, jugadores concretos."
---

# Análisis de logs de servidores Minecraft

Idioma: el del usuario, conciso. Los logs llegan como `latest*.log` subidos por el usuario o están en `<servidor>/logs/latest.log`. Los nombres de usuario reales aparecen en ellos: úsalos tal cual, sin inventar.

## Método
1. **Localizar y acotar.** Mirar primero la cabecera (hora de inicio, versión de Paper, plugins cargados) y la última línea (si el servidor cayó). Trabajar con `grep -n`/python por rango horario; no volcar el log entero.
2. **Preguntar lo que importa antes de buscar**: jugador, rango horario, qué plugin/evento. Si el usuario ya lo dio, responder a eso exacto con evidencia (líneas y horas).
3. **Resumen primero, evidencia después**: veredicto en una frase, luego 3-6 líneas citadas con hora (`[03:50:15] ...`) y qué significan. Decir qué NO se puede saber del log (el log solo registra lo que loguea Paper/plugins; un item perdido no sale sin CoreProtect).
4. **Distinguir ruido de problema**: WARN de plugins viejos, un "Can't keep up" aislado y mensajes de ViaVersion no son bugs; sí lo son stacktraces repetidos, `Could not pass event`, `Ambiguous plugin name`, `Error occurred while enabling`, `UnknownFormatConversionException`, `NoSuchMethodError/ClassNotFoundException` (plugin incompatible con la versión), `Server thread dumped`.

## Búsquedas útiles (grep -E)
- Arranque/plugins: `Enabling|Disabling|Error occurred while enabling|Could not load|Ambiguous|Unsupported API version`
- Errores: `ERROR|Exception|Caused by|Could not pass event|at com\.|at dev\.|at net\.`
- Muertes/combate: `was slain by|fell out of the world|fell from a high|burned|drowned|blew up|was killed|combat|logged out`
- Jugadores: `joined the game|left the game|lost connection|issued server command|UUID of player`
- Rendimiento: `Can't keep up|Running \d+ms behind|tick|watchdog|spark`
- Chat/comandos: `<Nombre>` y `issued server command: /`
- Caídas al vacío: `fell out of the world` (comprobar hora y mundo; las muertes por combat-log salen como muerte inmediata tras `lost connection`).

## Casos típicos
- **Item perdido / duplicado**: el log da muerte, hora y comandos; para el item usar CoreProtect (`/co lookup user:X t:3d r:N a:drop|pickup|container|item`; el radio es un cubo, ojo con la altura). Dar el comando exacto al usuario. Para dupes masivos, ver `tools/exploit_hunt` (consulta la BD de CoreProtect).
- **Plugin que no carga tras actualizar Paper**: buscar la primera `Caused by`; suele ser una librería de Adventure distinta, API antigua o falta de dependencia (PlaceholderAPI/Vault/LuckPerms).
- **Chat/placeholders raros**: `UnknownFormatConversionException`, `%` sin resolver, hooks de plugins de chat/tags.
- **Bosses/eventos de plugins propios**: buscar el prefijo del plugin en el log y seguir la secuencia (spawn → daño → muerte).
- **Cierre/reinicio inesperado**: última línea antes del corte, `Stopping server`, OOM, watchdog.

## Entrega
- Respuesta corta: veredicto + evidencia + siguiente comprobación (comando concreto).
- Si se encuentra un bug de código/config, aplicar el flujo de la skill `servidor-minecraft` (corregir, avisar de recompilar, registrar en `docs/CHANGELOG.md`).
- Si un patrón se repite, proponer una regla nueva para esta skill.
