# Backup Memory — Estado actual completo del proyecto

## Identidad del proyecto

- Nombre de carpeta actual: `Project I`
- Ruta actual: `/Users/rendoaltar/Unap/VIII Semester/Simulation/Project I`
- Identidad detectada por Engram: `project i`
- Fuente de detección: `dir_basename`

## Problema que motivó este respaldo

La carpeta del proyecto fue movida a iCloud y luego restaurada a la ubicación original. A partir de eso:

- dejó de aparecer la sesión visual previa en OpenCode
- surgió la necesidad de recuperar continuidad
- se verificó el estado actual del workspace
- se pidió reforzar memoria persistente y respaldo local

## Qué se verificó sobre Engram

- Engram sigue reconociendo este proyecto como `project i`
- la memoria histórica previa NO se perdió
- había sesiones y observaciones anteriores útiles del 2026-05-13 y 2026-05-14
- ya se guardaron nuevas observaciones de reasociación, inspección del estado local, continuidad y lectura completa del documento principal

## Qué se verificó sobre OpenCode

Se inspeccionaron de forma no destructiva rutas típicas de estado local:

- `~/.config/opencode`
- `~/.opencode`
- `~/Library/Application Support`
- `~/Library/Caches`

### Resultado
- se encontró configuración de OpenCode
- se encontró instalación/binarios locales
- NO se encontró una base visible y directa recuperable de la sesión UI previa del proyecto
- NO aparecieron referencias claras persistidas a `Project I` que permitieran restaurar automáticamente esa sesión visual

## Estructura actual confirmada del proyecto

### `docs/`
- `ATM_SIMULATION_SPEC.md`
- `ATM_SIMULATION_SPEC.pdf`
- `PROJECT_CONTINUITY.md`

### `data/`
- `customer_event_log.csv`
- `atm_state_log.csv`
- `system_snapshot_log.csv`

### `diagrams/`
Archivos `.puml`, `.png` y `.svg` de:

- `atm_activity`
- `atm_state`
- `atm_use_case`
- `atm_data_model`
- `atm_causal_map`
- `atm_bpmn_equivalent`

### `backupMemory/`
Esta carpeta fue creada para tener respaldo textual local de continuidad y memoria del proyecto.

## Estado documental actual

El documento principal declara:

- **Fase documental cerrada / pre-modelado computacional**

Y esa declaración es coherente con lo hallado en archivos.

## Estado conceptual del proyecto

- referencia teórica base: **M/M/4**
- modelo futuro recomendado: **simulación de eventos discretos en SimPy**
- separación metodológica central: **observado / inferido / estimado-modelado**
- contexto del caso: sistema ATM del Banco de la Nación, sede central Puno

## Lo que ya está bastante consolidado

- especificación metodológica completa
- criterios observacionales
- supuestos defendibles
- contexto 2026 Perú/Puno
- reglas operativas del sistema ATM
- estructura de datos en tres CSVs
- métricas mínimas
- parámetros preliminares de trabajo
- escenarios de simulación
- pseudológica previa a implementación
- anexos técnicos A–D
- diagramas renderizados y fuentes `.puml`

## Variables avanzadas ya implementadas en datos actuales

En los CSVs actuales ya se verificó presencia de variables como:

- `peak_intraday_band`
- `payroll_cycle_type`
- `peak_social_transfer_flag`
- `peak_operational_type`
- `peak_composite_level`

Estas ya forman parte real del estado actual de los artefactos, no solo de la teoría del documento.

## Variables aún planteadas como futura iteración o enriquecimiento

No se verificaron implementadas en los CSVs actuales estas variables avanzadas:

- `peak_intraday_flag`
- `peak_payroll_flag`
- `social_transfer_program`
- `social_transfer_access_channel`
- `peak_operational_flag`
- `assisted_service_flag`
- `priority_queue_flag`

## Evaluación actual del documento principal

Después de leer completo `ATM_SIMULATION_SPEC.md`, la evaluación correcta es:

- es un documento metodológicamente fuerte
- no es un borrador débil
- contiene anexos y estructura avanzada que una lectura parcial podía hacer parecer ausentes
- el principal punto mejorable a futuro es la armonización narrativa, no la falta de sustancia

## Archivos de continuidad ya creados

### `docs/PROJECT_CONTINUITY.md`
Resume:

- qué es el proyecto
- qué ya quedó hecho
- en qué fase está
- qué falta realmente
- siguiente paso recomendado

### `backupMemory/ATM_SIMULATION_SPEC_FULL_MEMORY.md`
Respaldo textual detallado del contenido y estructura del documento principal.

### `backupMemory/PROJECT_CURRENT_STATE_MEMORY.md`
Este snapshot del estado actual completo del proyecto, recuperación y memoria.

## Lo que ya quedó persistido en Engram durante esta recuperación

Se guardaron observaciones relacionadas con:

- reasociación de `Project I` en Engram
- inspección del estado local de OpenCode
- reconstrucción de continuidad del proyecto
- documentación de continuidad y auditoría de consistencia
- lectura completa del `ATM_SIMULATION_SPEC.md`
- consolidación del estado completo actual del proyecto

## Conclusión operativa

Aunque la sesión visual previa de OpenCode no se recuperó, el proyecto ya volvió a quedar bien sostenido por tres capas:

1. **archivos reales del proyecto**
2. **memoria persistente de Engram**
3. **respaldos locales en `docs/` y `backupMemory/`**

## Recomendación práctica futura

Cada vez que se cierre una fase relevante del proyecto, conviene actualizar:

- `docs/PROJECT_CONTINUITY.md`
- `backupMemory/ATM_SIMULATION_SPEC_FULL_MEMORY.md` si cambia el documento principal
- `backupMemory/PROJECT_CURRENT_STATE_MEMORY.md` si cambia el estado global de artefactos o continuidad

Eso reduce mucho la dependencia de la sesión visual de cualquier herramienta.
