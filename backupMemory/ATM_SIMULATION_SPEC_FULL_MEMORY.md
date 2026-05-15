# Backup Memory — ATM_SIMULATION_SPEC

## Archivo fuente

- `docs/ATM_SIMULATION_SPEC.md`
- Tema: simulación del sistema ATM del Banco de la Nación, sede central Puno
- Estado declarado en el documento: **Fase documental cerrada / pre-modelado computacional**

## Propósito del documento

El documento formaliza el caso ATM de BN Puno como una base metodológica seria para futura simulación. No busca solo describir la cola, sino preparar una representación defendible del sistema para análisis cuantitativo y futura implementación.

## Tesis metodológica central

La tesis principal del documento es esta:

- **M/M/4** sirve como referencia teórica inicial.
- El sistema real excede un modelo analítico puro.
- La implementación correcta debe hacerse como **simulación de eventos discretos en SimPy**.

Esto se justifica porque el sistema incorpora:

- abandono de cola
- fallas técnicas
- mantenimiento
- cashout
- restricciones horarias
- variación por franja horaria
- presión por calendario de pagos
- presión parcial por programas sociales
- heterogeneidad de usuarios

## Restricción observacional estructural

El documento insiste en una regla crítica:

- la observación fue externa
- no se observa la pantalla del ATM
- no se observa el tipo real de operación
- no se conoce edad real
- no se conoce identidad real de sexo/género
- no se observa con certeza el estado interno del ATM

Por tanto, el modelo debe separar estrictamente:

1. **dato observado**
2. **dato inferido**
3. **dato estimado/modelado**

Esta separación es uno de los pilares más fuertes del documento.

## Contexto real 2026 incorporado

El documento incorpora marco público 2026 para justificar supuestos:

- RENIEC: padrón y composición casi paritaria por sexo
- INEI: alta pobreza monetaria en Puno
- BCRP: crecimiento fuerte de pagos digitales
- SBS: marco de inclusión financiera y digitalización

Conclusión derivada:

- Perú 2026 es híbrido
- crecen los pagos digitales
- pero el efectivo sigue siendo importante
- en Puno el ATM no puede modelarse como canal residual

## Supuestos defendibles documentados

### Usuarios
- predominio de población 18+
- adolescentes como casos marginales
- distribución cercana a paridad por sexo/género percibido a nivel poblacional potencial

### Operaciones probables
Jerarquía propuesta:

1. retiro
2. consulta
3. pago
4. transferencia
5. otros

### Picos plausibles
- mañana temprana
- mediodía
- fin de tarde
- quincena
- fin de mes
- días de pago o depósitos masivos

### Dependencia del efectivo
- el retiro sigue siendo dominante
- la migración digital reduce parte de consultas/pagos
- no elimina la presión sobre ATM físico

## Frontera del sistema

### Dentro del sistema
- área ATM observada
- 4 ATM de la sede
- cola general
- cola preferencial cuando aplica
- clientes que llegan al área ATM
- espera, abandono, atención y salida
- cambios visibles o inferibles de disponibilidad

### Fuera del sistema
- ventanillas del banco
- core bancario interno
- saldos y autorizaciones reales
- usuarios que se retiran sin acercarse
- cobros de Pensión 65 por canales no ATM
- detalle exacto de logística de reposición

### Regla importante
Factores externos como pagos, Pensión 65, recarga o mantenimiento pueden afectar el sistema aunque estén fuera de la frontera directa; deben modelarse como **factores exógenos**.

## Reglas operativas reales consolidadas

- existen 4 ATM
- existe cola general única para el primer ATM funcional libre
- no hay ATM preferencial exclusivo
- existe cola preferencial ocasional para población vulnerable
- el usuario toma el primer ATM funcional libre
- puede haber ayuda del personal a personas vulnerables
- la ayuda puede aumentar tiempo visible de atención
- los ATM pueden estar busy, idle, down_failure, down_maintenance, cashout, reactivado/offline
- la reposición de efectivo existe pero no debe fijarse a hora exacta rígida

## Diseño de datos consolidado

El documento adopta tres archivos principales:

1. `customer_event_log.csv`
2. `atm_state_log.csv`
3. `system_snapshot_log.csv`

Esto representa correctamente tres granularidades:

- evento de cliente
- estado de ATM
- estado agregado del sistema

## Variables del modelo documentadas

### Customer event
Incluye identificación, timestamps, sexo/género percibido, edad estimada, tipo de operación inferido, cola, abandono, atención, ATM asignado, calidad del dato y presión simplificada.

### ATM state
Incluye estado del ATM, efectivo disponible, fallas, mantenimiento, conectividad y calidad del estado.

### System snapshot
Incluye cola agregada, ATM activos/ocupados/libres/fallidos/cashout, ventana restringida y presión del sistema.

## Variables derivadas obligatorias

Se documentan como mínimas:

- `interarrival_time_sec`
- `waiting_time_sec`
- `service_time_sec`
- `time_in_system_sec`
- `queue_delay_flag`
- `loss_flag`
- `rho_system`
- `Wq`
- `Lq`
- `loss_rate`

## Unidad temporal y snapshots

- unidad base recomendada: **segundos**
- snapshots recomendados: base cada **1 minuto**
- snapshots adicionales ante eventos críticos (abandono, falla, cashout, reactivación, cambio brusco de cola)

Esto prepara correctamente métricas agregadas como `Lq` y presión operativa por momento.

## KPIs mínimos documentados

- `Wq`
- `Lq`
- `ρ`
- `loss_rate`
- atendidos por franja
- perdidos por franja
- utilización por ATM
- impacto de fallas/recargas sobre la cola

## Metodología de levantamiento

El documento define:

- estudio observacional no experimental
- observación directa externa
- procedimiento de registro
- frecuencia recomendada por franjas y tipos de día
- reglas de calidad de datos
- consideraciones éticas

## Capítulo 16 — núcleo de preparación pre-simulación

Esta es la parte más importante para transición futura.

### Contiene:
- criterios de llenado de CSV
- política de servicio realista
- política de abandono realista
- parámetros confirmados, inferidos y pendientes
- objetivos experimentales
- matriz de escenarios
- estrategia de calibración
- limitaciones del modelo
- tabla de parámetros iniciales
- valores preliminares numéricos de trabajo
- alcance actual del proyecto
- reglas exactas preliminares de generación de eventos
- pseudológica detallada del simulador sin implementación

### Escenarios definidos
- `S1_normal`
- `S2_fin_mes`
- `S3_quincena`
- `S4_pension65_atm`
- `S5_falla_1_atm`
- `S6_cashout`
- `S7_mantenimiento`
- `S8_nocturno_restringido`
- `S9_critico`

### Parámetros preliminares destacados
- 4 ATM
- snapshot base cada 1 minuto
- unidad temporal de 1 segundo
- ventanas documentales de inicio de mes, quincena y fin de mes
- rangos preliminares de tiempos visibles
- umbral documental inicial de abandono por espera alta

### Regla de alcance actual
El documento deja explícito que **todavía no se inicia implementación en SimPy**. Todo el trabajo actual es de especificación/preparación.

## Reglas preliminares del futuro simulador

Eventos mínimos previstos:

- `customer_arrival`
- `queue_enter`
- `service_start`
- `service_end`
- `customer_abandon`
- `atm_failure`
- `atm_cashout`
- `atm_maintenance_start`
- `atm_recovery`
- `cash_replenishment`
- `system_snapshot`

La pseudológica posterior detalla:

- inicialización
- motor de eventos
- procesamiento de llegada
- cola
- servicio
- contingencias
- cierre de cliente
- métricas finales

## Anexo A — Matriz de trazabilidad epistemológica

Este anexo justifica cada regla/variable por:

- origen de evidencia
- nivel de evidencia (`E1`–`E4`)
- tipo de construcción
- impacto
- sensibilidad
- plan de validación

También clasifica prioridades de validación:

- prioridad 1: llegadas, picos, mezcla de operaciones, pagos, Pensión 65, abandono
- prioridad 2: franja etaria, sexo/género percibido, distribución de fallas
- prioridad 3: refinamientos descriptivos

## Anexo B — Diccionario formal de datos

El anexo B define operativamente:

- `customer_event_log.csv`
- `atm_state_log.csv`
- `system_snapshot_log.csv`

Incluye por variable:

- nombre legible
- tipo
- dominio/formato
- nulos
- origen
- definición operacional
- regla de consistencia

También incluye:

- variables recomendadas para futura iteración
- reglas generales de consistencia cruzada

### Variables futuras destacadas
- `peak_intraday_flag`
- `peak_payroll_flag`
- `social_transfer_program`
- `social_transfer_access_channel`
- `peak_operational_flag`
- `assisted_service_flag`
- `priority_queue_flag`

## Anexo C — Taxonomía de peak flags y calendario operativo

El anexo C redefine la idea de pico como fenómeno multicausal.

Variables y dimensiones documentadas:

- `peak_intraday_flag`
- `peak_intraday_band`
- `peak_payroll_flag`
- `payroll_cycle_type`
- `peak_social_transfer_flag`
- `social_transfer_program`
- `social_transfer_access_channel`
- `peak_operational_flag`
- `peak_operational_type`
- `peak_composite_level`

También fija:

- regla operativa inicial de calendario laboral
- criterio bimestral para Pensión 65
- lógica de combinación para `peak_composite_level`
- tabla maestra de interpretación

## Anexo D — Diagramas y modelos visuales

El anexo D contiene:

- `D.1` Activity Diagram
- `D.2` State Diagram
- `D.3` Use Case Diagram
- `D.4` estructura lógica de datos
- `D.5` mapa causal simplificado
- `D.6` BPMN completo en texto estructurado + representación PlantUML equivalente con lanes
- `D.7` priorización práctica de qué renderizar primero

## Evaluación global del documento

Después de releerlo completo, la evaluación correcta es:

- documentalmente maduro
- metodológicamente sólido para nivel universitario serio
- conceptualmente fuerte
- listo para revisión estructurada o defensa académica
- preparado para futura transición a SimPy

## Tensión principal detectada

La tensión real del documento no es falta de sustancia, sino mezcla de tres tiempos narrativos:

1. estado actual
2. recomendación futura
3. ideal metodológico

Muchos puntos que parecían faltantes en lectura parcial sí están presentes en anexos y secciones posteriores. Por eso cualquier revisión futura debe basarse en lectura completa, no parcial.

## Estado de madurez resumido

- nivel conceptual: alto
- nivel metodológico: alto para trabajo universitario
- estructuración de datos: alta
- preparación para simulación: medio-alta
- armonización editorial: mejorable, pero sin afectar la base conceptual
