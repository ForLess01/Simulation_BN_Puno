# Diseño de interfaz visual del simulador ATM

## Propósito

La interfaz visual del simulador no busca reemplazar la formulación metodológica ni la trazabilidad en CSV, sino complementar la comprensión del comportamiento dinámico del sistema. Su función principal es mostrar, de forma ordenada y pedagógica, cómo evoluciona la simulación mientras se ejecutan los eventos discretos.

## Objetivos de la interfaz

La primera versión de la interfaz debe permitir:

1. seleccionar escenario y semilla de ejecución
2. correr la simulación y ver resultados sin necesidad de inspeccionar manualmente los CSV
3. mostrar el estado actual de los 4 ATM
4. mostrar longitud de cola y eventos recientes
5. mostrar KPIs resumidos por corrida
6. exponer explícitamente la lógica pseudoaleatoria utilizada en la simulación

## Tecnología recomendada

Para una primera capa visual competente, la opción más adecuada es **Streamlit** por estas razones:

- integración rápida con Python y pandas
- suficiente calidad visual para exposición académica
- facilidad para mostrar tablas, KPIs y estados
- posibilidad de agregar controles laterales y paneles sin construir frontend dedicado

## Estructura funcional propuesta

### 1. Sidebar de control

Debe contener:

- selector de escenario (`S1` a `S9`)
- selector o input de semilla (`seed`)
- botón de ejecución
- resumen breve del escenario seleccionado

### 2. Panel superior de contexto

Debe mostrar:

- escenario activo
- semilla usada
- horizonte temporal de simulación
- cantidad total de ATM
- tasa o intensidad relativa de llegadas esperada por franja

### 3. Panel de pseudoaleatoriedad y motor estocástico

Debe mostrar, de forma pedagógica:

- tipo de distribución activa por fenómeno
- pseudoúltimo número uniforme generado en la corrida o muestra representativa
- explicación breve de cómo ese número alimenta interarribos, servicio o contingencias

### 4. Panel de estado operativo del sistema

Debe incluir:

- tarjetas para ATM 1–4
- estado actual (`idle`, `busy`, `down_failure`, `down_maintenance`, `cashout`)
- longitud de cola actual
- capacidad activa actual
- presencia de contingencias activas

### 5. Panel de eventos recientes

Debe listar eventos como:

- `customer_arrival`
- `service_start`
- `service_end`
- `customer_abandon`
- `atm_failure`
- `atm_cashout`
- `atm_maintenance_start`
- `atm_recovery`
- `cash_replenishment`

### 6. Panel de KPIs de corrida

Debe resumir:

- llegadas totales
- `Wq`
- `Lq`
- `loss_rate`
- cola máxima
- minutos de capacidad reducida
- utilización promedio ATM

### 7. Panel de artefactos de salida

Debe mostrar rutas o preview de:

- `customer_event_log.csv`
- `atm_state_log.csv`
- `system_snapshot_log.csv`
- `kpis.csv`

## Alcance de la primera versión

La primera versión no necesita animación continua frame a frame. Para un uso académico serio, es suficiente con:

- ejecución por escenario
- visualización del estado consolidado
- resumen de eventos recientes
- KPIs y previews de salida

## Relación con el proyecto

Esta interfaz debe presentarse como capa de apoyo para:

- explicar el modelo de simulación
- visualizar su comportamiento operativo
- conectar pseudoaleatoriedad, eventos y KPIs
- fortalecer la exposición del proyecto
