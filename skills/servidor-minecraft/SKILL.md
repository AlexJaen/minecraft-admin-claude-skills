---
name: "servidor-minecraft"
description: "Úsala en cualquier petición sobre los servidores Minecraft del proyecto (carpetas de servidor, plugins propios, configs, bugs, logs, despliegues): define el flujo orientar → cambiar → avisar de recompilar/desplegar → registrar en docs/CHANGELOG.md."
---

# Flujo estándar para administrar servidores Minecraft (Paper)

Requisito: el proyecto tiene un `CLAUDE.md` en la raíz con el mapa de servidores (ver `templates/CLAUDE.md` del repositorio de esta skill). Si no existe, créalo la primera vez a partir de la plantilla y rellénalo con lo que averigües.

Idioma: el del usuario; respuestas concisas; modo auto (decidir razonablemente, preguntar solo ante bloqueo real).

## 1. Orientarse (siempre, antes de tocar nada)
1. Leer `CLAUDE.md` de la raíz (servidores, versiones, puertos, reglas) y, si el tema lo requiere, `docs/PENDIENTE.md` y `docs/servers/<servidor>.md`.
2. Identificar el servidor afectado (carpeta, versión de Paper/Velocity, puerto). Si hay varias versiones del mismo plugin (p. ej. una copia por versión de Minecraft), **no mezclarlas** y editar todas las que correspondan.
3. Listar/leer lo que hay antes de escribir en una carpeta; nunca sobrescribir un fichero sin leerlo.

## 2. Diagnosticar y cambiar
- Config vs código: decidir cuál es la causa real. Para config, editar el yml/json desplegado en `<servidor>/plugins/<Plugin>/`; si el plugin copia su yml del jar solo cuando no existe, editar también `src/main/resources` del plugin propio.
- Grep con `output_mode: content` cuando se necesiten líneas; no deducir ausencia de un "Found N files".
- Antes de crear un plugin propio: buscar uno existente y preguntar al usuario.
- No abrir flags de WorldGuard como atajo para una excepción concreta; resolver en el plugin. Los `/rg flag` se dan al usuario como comandos (WorldGuard sobrescribe `regions.yml` con el servidor encendido).
- Comentar los cambios con fecha y motivo (`Sesion AAAA-MM-DD (a peticion del usuario: "...")` o el estilo del repo).
- Verificar firmas de API con los jars de `libraries/` (paper-api) en vez de adivinar.
- Hacer copia en `_backup/` antes de editar configs sensibles.
- **Antes de tocar código que mueva items, llaves o dinero**: leer `docs/EXPLOITS.md` (checklist de código seguro) y añadir una entrada tras cada incidente.

## 3. Avisar siempre del despliegue
Si el entorno no puede compilar Java, decirlo: tras editar código, indicar explícitamente qué plugin recompilar (`mvn clean package` o gradle), qué jar sale, dónde dejarlo (mismo nombre de fichero; **un único jar por plugin**, o Paper carga uno al azar), que hace falta reinicio completo (no `/reload`) y que no se ha probado. Distinguir en la respuesta: solo config / recompilar / reinicio / comando en juego.
Si el servidor real está en un hosting externo, la copia local puede diferir: para verificar, pedir al usuario `/plugins`, `/version <plugin>` o el log.

## 4. Registrar (obligatorio al terminar)
- Entrada fechada en `docs/CHANGELOG.md` (qué, dónde, etiquetas: [R] recompilar, [C] config, [G] comando en juego, [X] reinicio).
- Actualizar `docs/PENDIENTE.md` (cerrar lo hecho, abrir lo nuevo u ofrecido sin confirmar).
- Si cambia la estructura del proyecto, actualizar el mapa de `CLAUDE.md`.
- Hechos durables del usuario (preferencias, decisiones de diseño) → memoria del proyecto.

## 5. Buenas prácticas al escribir/revisar código de plugins
- **Eventos**: `@EventHandler(ignoreCancelled = true)` salvo que se necesite ver cancelados; prioridad NORMAL por defecto, HIGH/HIGHEST solo para sobreescribir decisiones de otros plugins; MONITOR solo lectura. Antes de tocar un listener, preguntarse qué pasa con eventos ya cancelados por otro handler.
- **Eventos async** (chat async, etc.): jamás tocar mundo/entidades/inventarios ahí; volver al hilo principal con `Bukkit.getScheduler().runTask(plugin, ...)`. Es seguro en async: leer datos propios, BD, HTTP, enviar mensajes.
- **Tareas**: lambdas con `runTask/runTaskLater/runTaskTimer`; E/S pesada fuera del hilo principal, nunca `Thread.sleep`; cancelar las tareas en `onDisable`.
- **Datos en ítems/entidades/bloques/chunks**: `PersistentDataContainer` con `NamespacedKey` creado una vez como campo; tipos nativos, objetos complejos como JSON en STRING. Para grandes volúmenes de jugadores, una BD y no PDC.
- **Versiones nuevas de Paper**: comprobar el Adventure que trae; las librerías que incluyan otra versión deben relocalizarse.
- Cuidado con `%` de PlaceholderAPI en formatos que pasan por `String.format`, y con llamar a la API del mundo desde hilos async.
- **Items/dinero**: comprobar siempre el resultado de `addItem` (sobrante), `dispatchCommand` y las transacciones de economía; no consumir el item antes de saber que la recompensa se entregó.

## 6. Respuesta final
Una o dos frases útiles: qué se hizo, si requiere recompilar/reiniciar y qué probar. Sin recapitular cada paso.
