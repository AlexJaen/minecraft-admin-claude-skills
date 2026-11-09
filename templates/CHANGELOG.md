# CHANGELOG

Formato: `fecha — componente — cambio — [R] recompilar · [C] solo config · [G] comando en juego · [X] reinicio`.
Mantener al día tras cada cambio (la skill `servidor-minecraft` lo exige).

## AAAA-MM-DD (componente)
- Qué se cambió, dónde, y si requiere recompilar/desplegar. **[R]** `mvn clean package` en `<plugin>`; jar de `target\` → `<servidor>\plugins\` (mismo nombre) + reinicio.
