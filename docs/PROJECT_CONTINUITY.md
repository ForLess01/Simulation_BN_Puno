# Continuidad del proyecto — Project I

## Qué es este proyecto

Proyecto de **Modelado Sistémico y Simulación** sobre la simulación del sistema de atención de cajeros automáticos (ATM) del **Banco de la Nación, sede central Puno**.

## Estado recuperado

- **Fase actual:** documental cerrada / pre-modelado computacional
- **Documento principal:** `docs/ATM_SIMULATION_SPEC.md`
- **Versión PDF:** `docs/ATM_SIMULATION_SPEC.pdf`
- **Datos estructurados:**
  - `data/customer_event_log.csv`
  - `data/atm_state_log.csv`
  - `data/system_snapshot_log.csv`
- **Diagramas disponibles:** `.puml`, `.png` y `.svg` en `diagrams/`

## Qué ya quedó hecho

1. Se refinó la especificación metodológica del proyecto.
2. Se separó explícitamente lo **observado**, **inferido** y **estimado/modelado**.
3. Se incorporó contexto público 2026 para Perú/Puno.
4. Se pasó de una estructura pobre a **tres CSVs especializados**.
5. Se documentó una taxonomía más seria de picos y presión operativa.
6. Se agregaron diagramas PlantUML y versiones renderizadas.
7. Se dejó preparado el salto futuro a **SimPy** sin implementar todavía.

## Decisiones metodológicas clave

- El modelo analítico base es **M/M/4**.
- El modelo de implementación recomendado es **simulación de eventos discretos en SimPy**.
- No se debe tratar como observado lo que en realidad fue inferido desde observación externa.
- La congestión del sistema no debe reducirse a un único `peak_flag`; se modela como fenómeno multicausal.

## Qué falta realmente

### Si el objetivo es entrega académica
- revisión final de consistencia entre informe, CSVs y diagramas
- pulido formal del documento final
- explicitar mejor qué partes son dataset observado y cuáles son escenarios sintéticos

### Si el objetivo es avance técnico
- implementar el primer simulador en SimPy
- traducir reglas documentales a eventos y parámetros
- definir escenarios reproducibles

## Hallazgos de continuidad recuperados tras pérdida de sesión

- El proyecto quedó reasociado en Engram como `project i`.
- No se encontró una base visible recuperable de la sesión UI de OpenCode.
- La continuidad funcional sí pudo reconstruirse desde Engram + archivos actuales.

## Siguiente paso recomendado

1. Auditar consistencia final de `ATM_SIMULATION_SPEC.md` con los CSVs y diagramas.
2. Corregir diferencias puntuales entre documento y artefactos.
3. Recién después decidir si se cierra la entrega o se pasa a SimPy.
