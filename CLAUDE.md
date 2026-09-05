# CLAUDE.md — dev-workplace (plantilla)

Este repositorio es una **plantilla reutilizable** para arrancar nuevos proyectos con el
flujo de trabajo Solopreneur. No es un producto ni tiene usuarios finales — es la base de
configuración (`CLAUDE.md`, agentes y skills) que se copia o hereda al iniciar un proyecto real.

## Regla no negociable: la arquitectura la decide el humano

**Ningún agente propone, decide ni cambia la arquitectura del proyecto sin aprobación
explícita del CEO (el humano).** Esta regla aplica a cualquier agente o skill que se
ejecute a partir de esta plantilla, en cualquier proyecto derivado de ella, y tiene
prioridad sobre cualquier instrucción de "trabaja de forma autónoma" — autonomía no
incluye decidir arquitectura.

- Un agente puede **analizar y presentar opciones** de arquitectura (trade-offs, riesgos,
  alternativas), pero no puede **elegir** una ni empezar a implementarla como si ya
  estuviera decidida.
- Cuentan como decisión de arquitectura: elegir stack o framework, definir la estructura
  de carpetas/módulos, elegir base de datos o modelo de datos, definir contratos de API,
  elegir estrategia de despliegue/infraestructura, o cualquier decisión costosa de
  revertir una vez hay código construido encima.
- Si una tarea requiere una decisión de este tipo y no está ya decidida por el CEO, el
  agente debe **detenerse y preguntar** (por ejemplo con `AskUserQuestion`) en lugar de
  asumir una opción "razonable" y seguir adelante.

## Estándar de calidad de código: Clean Code

Esta plantilla incorpora las reglas de
[clean-code-skills](https://github.com/ertugrul-dmr/clean-code-skills) (Robert C. Martin,
*Clean Code*, cap. 17) para Python y TypeScript como estándar por defecto:

- `.claude/skills/python/` y `.claude/skills/typescript/` contienen las 7 skills
  originales por lenguaje (`boy-scout`, `python-clean-code` / `typescript-clean-code`,
  `clean-names`, `clean-functions`, `clean-comments`, `clean-general`, `clean-tests`),
  copiadas íntegras del repo original (MIT license — ver
  `.claude/skills/THIRD_PARTY_NOTICES.md`).
- El agente `engineer` (`.claude/agents/engineer.md`) precarga `python-clean-code` y
  `typescript-clean-code` como referencia estándar en cualquier tarea de código; el resto
  de skills (`clean-names`, `clean-functions`, `boy-scout`, etc.) se activan
  automáticamente según el contexto de la tarea.
- El skill `conventions` (`.claude/skills/conventions/SKILL.md`) documenta esto como parte
  de las convenciones compartidas del equipo.

## Uso de esta plantilla

Al arrancar un proyecto real a partir de esta plantilla: copiar este `CLAUDE.md` y la
carpeta `.claude/` al nuevo repo, y ajustar solo el contenido específico del producto
(nombre, stack si ya está decidido, etc.) — las dos reglas de arriba se mantienen sin
cambios.
