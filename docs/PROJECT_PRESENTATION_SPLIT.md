# División de exposición del proyecto (2 integrantes)

## Objetivo

Este documento organiza una exposición equitativa y profesional del proyecto entre dos integrantes, dejando claro el aporte técnico de cada uno y la secuencia sugerida para presentar el trabajo de forma coherente.

## Integrantes

1. **Rendo Alfonte Tarqui**
2. **Carlos David Turpo**

## Principio de reparto

La división no debe hacerse solo por cantidad de diapositivas o páginas, sino por **responsabilidad técnica real dentro del proyecto**.

## Aporte técnico clave de Carlos David Turpo

Debe resaltarse explícitamente que uno de los aportes centrales del proyecto fue el desarrollo de un **software web desplegado para la toma de muestras en tiempo real**.

Ese aplicativo permitió:

- registrar con rapidez datos esenciales del usuario observado
- capturar si el usuario ingresó directamente o esperó en cola
- registrar información mínima clave para el dataset observacional
- almacenar dicha información como base estructurada para el proyecto

Este punto es importante porque conecta el trabajo no solo con simulación, sino también con **ingeniería de captura de datos en campo**.

## Reparto sugerido de exposición

### Parte 1 — Contexto, problema y captura de datos
**Responsable sugerido: Carlos David Turpo**

Temas:

1. problema del sistema ATM en BN Puno
2. necesidad de observación y levantamiento de datos
3. dificultades de observación externa
4. lógica del aplicativo web desplegado
5. cómo se capturaron los datos esenciales en tiempo real
6. cómo el dataset observacional alimenta el proyecto

### Parte 2 — Modelo de simulación y estructura analítica
**Responsable sugerido: Rendo Alfonte Tarqui**

Temas:

1. justificación de la simulación de eventos discretos
2. uso de Poisson, exponencial, M/M/4 y M/G/4 como referencias
3. papel de los números pseudoaleatorios
4. arquitectura del simulador
5. escenarios S1–S9
6. KPIs y outputs del sistema

### Parte 3 — Integración del proyecto
**Responsabilidad compartida**

Temas:

1. relación entre dataset real, dataset sintético-realista y simulador
2. interpretación de KPIs
3. hallazgos del comportamiento del sistema
4. valor del modelo para análisis y toma de decisiones

## Secuencia sugerida de exposición

1. problema real y contexto de Puno
2. captura de datos en campo mediante aplicativo web
3. construcción del dataset y variables
4. formulación del modelo de simulación
5. pseudoaleatoriedad y modelos probabilísticos
6. arquitectura del simulador
7. escenarios y KPIs
8. conclusiones

## Recomendación profesional para la exposición

- No presentar el trabajo como “solo análisis de datos”.
- No presentar el simulador como “solo código”.
- Presentarlo como un proyecto integrado de:
  - captura de datos en campo
  - formalización de variables
  - modelado estocástico
  - simulación de eventos discretos
  - análisis de resultados

## Nota final

La exposición debe dejar claro que el proyecto tiene dos pilares complementarios:

1. **captura y estructuración de datos observacionales reales**
2. **construcción de un modelo de simulación de eventos discretos para representar y experimentar el sistema ATM**
