# Guion de Presentación — Rendo Alfonte Tarqui

## Simulación ATM — Banco de la Nación, Sede Central Puno

> Duración objetivo: ~10 minutos

---

## Segmento 1 — Contexto y Justificación del Modelo

**[ABRIR: Streamlit — `streamlit run streamlit_app.py`]**

**[MOSTRAR: Dashboard en pantalla completa]**

Lo que ven acá es el sistema de 4 cajeros automáticos del Banco de la Nación en la sede central de Puno. El problema es claro: colas, abandono, fallas técnicas, falta de efectivo. No alcanza con describir el problema — necesitamos herramientas cuantitativas para experimentar y tomar decisiones.

**[CAMBIAR A: `diagrams/atm_bpmn_equivalent.svg`]**

Este diagrama muestra el flujo real: llega un cliente, evalúa si hay ATM libre, entra a cola o abandona, es atendido o interrumpido por falla, cashout o mantenimiento. Esa complejidad — abandono, fallas, restricciones horarias, presión por calendario — hace que un modelo analítico puro como M/M/4 no capture la dinámica real. Por eso eligimos simulación de eventos discretos.

Un punto clave: la observación fue externa. No vemos la pantalla del ATM, no sabemos la operación real del usuario, no conocemos el estado interno del cajero. Por eso el proyecto marca explícitamente cada variable como observada, inferida o estimada. Eso no debilita el trabajo — lo vuelve intelectualmente honesto.

---

## Segmento 2 — Modelos Probabilísticos y Pseudoaleatoriedad

**[VOLVER A: Streamlit — ejecutar S1_normal con seed 42]**

**[CLICK: "Ejecutar simulación"]**

**[SCROLL HASTA: Panel "Pseudoazar visible y aplicado"]**

La simulación no usa azar físico — usa números pseudoaleatorios con semilla fija. Esto es metodológicamente correcto y además es reproducible: misma seed, misma corrida, mismos resultados. Permite auditoría y comparación controlada entre escenarios.

Las llegadas siguen un proceso de Poisson: el tiempo entre llegadas es exponencial. En el panel pueden ver un ejemplo concreto: se genera un número uniforme U entre 0 y 1, y se transforma en un interarribo con la fórmula T = -media × ln(1 - U). Para el abandono, se usa un esquema Bernoulli: si U < p, el cliente abandona.

**[SEÑALAR los valores en el panel: Seed 42, Multiplicador λ, Interarribo base]**

**[SCROLL HASTA: Panel "Métodos aplicados en la corrida"]**

Acá se ve cada componente estocástico: llegadas con Poisson ajustado por franja, servicio con distribución positiva, abandono con umbral más probabilidad, contingencias activadas pseudoaleatoriamente, y snapshots periódicos discretos.

La posición metodológica es: M/M/4 como referencia teórica base, M/G/4 como referencia más flexible para servicio, y simulación de eventos discretos como representación principal. Ni Poisson ni exponencial se presentan como verdades cerradas — son hipótesis iniciales defendibles sujetas a calibración.

---

## Segmento 3 — Arquitectura del Simulador

**[MOSTRAR: `diagrams/atm_simulation_architecture.svg`]**

La arquitectura del simulador se organiza en componentes bien separados.

**[CAMBIAR A: Editor de código — abrir archivos uno por uno brevemente]**

**[ABRIR: `src/atm_simulator/domain.py`]**

La entidad principal es el ATM con 6 estados mutuamente excluyentes: idle, busy, down_failure, down_maintenance, cashout, offline. Con jerarquía de precedencia: down_failure tiene prioridad sobre down_maintenance, que tiene prioridad sobre cashout, que tiene prioridad sobre busy, que tiene prioridad sobre idle.

**[ABRIR: `src/atm_simulator/config.py`]**

La configuración centraliza todos los parámetros: duración de la simulación, número de ATM, interarribo base, tiempo de servicio medio, umbral de abandono, tasas de falla, mantenimiento y cashout por hora. Cada escenario sobreescribe lo que necesita.

**[ABRIR: `src/atm_simulator/random.py`]**

El motor pseudoaleatorio encapsula las distribuciones: exponencial para tiempos, Bernoulli para decisiones binarias, choice para tipos de operación. La función key es `interarrival_sampler`: ajusta la media del exponencial dividiendo entre el multiplicador de presión del escenario.

**[ABRIR: `src/atm_simulator/policies.py`]**

La política de cola es FIFO con prioridad excepcional: se recorre la cola buscando clientes con flag de prioridad — adultos mayores, personas con discapacidad — y se despachan primero. Si no hay prioridad, se atiende al primero que llegó. La asignación de ATM es al primer cajero funcional libre que tenga efectivo.

**[ABRIR: `src/atm_simulator/processes/`]**

Los procesos son 5:

1. **arrivals.py** — Genera llegadas según intensidad λ ajustada por escenario. Si cae en ventana restringida 22:00–05:00, el cliente se marca como bloqueado y se contabiliza como pérdida.

2. **customer_flow.py** — Ciclo principal: busca ATM libre, selecciona próximo cliente de la cola, inicia servicio.

3. **service.py** — Atiende al cliente: asigna duración según tipo de operación, descuenta efectivo del ATM. Si el ATM queda sin efectivo, transiciona a cashout.

4. **abandonment.py** — Cada 5 segundos reevalúa clientes en cola: si superan el umbral de espera, abandonan; si no, se aplica probabilidad Bernoulli según nivel de presión compuesta.

5. **contingencies.py** — Genera fallas, cashout y mantenimiento como eventos estocásticos. Incluye recuperación con probabilidad 3% cada 30 segundos. En escenarios como S5, S9 se fuerzan eventos específicos en momentos concretos de la corrida.

**[ABRIR: `src/atm_simulator/runner.py`]**

El runner orquesta todo: crea el entorno SimPy, instancia los 5 procesos, ejecuta la corrida hasta la duración configurada, y produce los 3 logs más la tabla de KPIs.

El motor es SimPy: el tiempo avanza de evento en evento, no segundo a segundo. Eso lo hace eficiente y metodológicamente correcto para simulación de eventos discretos.

Los 11 eventos del sistema son: customer_arrival, queue_enter, service_start, service_end, customer_abandon, atm_failure, atm_cashout, atm_maintenance_start, atm_recovery, cash_replenishment y system_snapshot. Cada transición queda trazada en los logs.

---

## Segmento 4 — Escenarios S1 a S9

**[VOLVER A: Streamlit — mostar sidebar con selector de escenario]**

Diseñamos 9 escenarios para cubrir desde operación normal hasta estrés multicausal:

**[MOSTRAR cada escenario en el sidebar mientras se explica]**

**S1_normal** — Día hábil normal, 4 ATM operativos. Es la línea base.

**S2_fin_mes** — Presión por pagos de cierre de mes. Lambda se multiplica por 1.5.

**S3_quincena** — Presión intermedia por pagos quincenales. Lambda × 1.3.

**S4_pension65_atm** — Presión bimestral de Pensión 65. Lambda × 1.25 y probabilidad de cola prioritaria al 35%.

**S5_falla_1_atm** — Un ATM fuera por falla técnica al 20% de la corrida. Capacidad reducida.

**S6_cashout** — Un ATM sin efectivo. Reduce capacidad funcional y aumenta abandono percibido.

**S7_mantenimiento** — Intervención operativa temporal. Reduce capacidad.

**S8_nocturno_restringido** — Solo 6 horas, de 22:00 a 04:00. Lambda × 0.8 y clientes bloqueados por horario.

**S9_critico** — Combinación de pico de fin de mes, falla de ATM, cashout y mantenimiento simultáneo. Lambda × 2.0. Es el escenario de estrés máximo.

Cada escenario modifica la intensidad de llegadas, la probabilidad de contingencias, y en algunos casos el perfil del cliente. Esto permite comparación controlada entre condiciones operativas distintas.

---

## Segmento 5 — Ejecución en Vivo y KPIs

**[EJECUTAR: S1_normal con seed 42 si no se ejecutó antes]**

**[SCROLL HASTA: Header del escenario + KPIs]**

Los KPIs de salida del sistema son estos 8:

**[SEÑALAR cada KPI uno por uno]**

**Llegadas totales** — número de clientes que ingresaron al sistema en la corrida.

**Wq promedio en segundos** — tiempo promedio de espera en cola. Este es el indicador central de congestión.

**Loss rate** — tasa de pérdida: clientes que abandonaron o fueron bloqueados dividido entre llegadas totales.

**Cola máxima** — longitud máxima alcanzada por la cola durante la simulación.

**Arribos pico por hora** — máxima concentración horaria de llegadas.

**Arribos máx por minuto** — intensidad máxima observada en un solo minuto.

**Minutos con capacidad reducida** — tiempo durante el cual hubo menos de 4 ATM operativos.

**Utilización ATM media** — fracción de tiempo que los ATM estuvieron ocupados atendiendo clientes.

**[SCROLL HASTA: Panel de Estado ATM]**

Cada ATM tiene su tarjeta de estado con colores: verde para idle, amarillo para busy, rojo para falla, naranja para cashout, violeta para mantenimiento. Se ve el efectivo disponible, si tiene falla técnica, si está en mantenimiento, si hay caída de red.

**[SCROLL HASTA: Simulación activa — mover el slider a un momento de pico]**

Acá podemos recorrer instante a instante la simulación. Selecciono un timestamp y veo: cola actual, ATM activos, ATM ocupados, capacidad reducida, presión operativa y presión compuesta. Esto permite analizar momentos críticos — por ejemplo, cuando un ATM se cae y la cola crece.

**[MOVER el slider a un momento con capacidad reducida y mostrar los eventos cercanos]**

A la derecha se ven los eventos de cliente cercanos al instante seleccionado: qué operación estaban haciendo, en qué ATM, cuánto esperaron, si abandonaron. Abajo se ven los segmentos de estado ATM correspondientes.

---

## Segmento 6 — Gráficos Analíticos

**[SCROLL HASTA: Gráficos]**

**[MOSTRAR: Llegadas por banda intradía — gráfico de barras]**

La distribución de llegadas por franja horaria. La concentración principal está en midday_peak y afternoon_peak — consistente con las hipótesis del modelo: mediodía y fin de tarde son los momentos de mayor demanda.

**[MOSTRAR: Intensidad de llegadas por minuto del día — gráfico de línea]**

Flujo minuto a minuto. Los picos corresponden a las ventanas de mayor demanda dentro de cada banda. Esto valida que el simulador está generando llegadas con intensidad variable, no constante.

**[MOSTRAR: Evolución temporal de la cola — gráfico de línea roja]**

Longitud de la cola a lo largo del tiempo. Los picos de cola coinciden con los momentos de alta demanda o reducción de capacidad. Cuando un ATM se cae, la cola sube visiblemente.

**[MOSTRAR: Evolución de la capacidad activa — gráfico de línea verde]**

ATM activos a lo largo del tiempo. Los momentos donde baja de 4 corresponden a fallas, cashout o mantenimiento. La recuperación se ve cuando vuelve a 4.

**[EJECUTAR: S9_critico con seed 42]**

**[CLICK: Cambiar escenario a S9_critico y ejecutar]**

**[SCROLL HASTA: Comparativa rápida de escenarios]**

La tabla comparativa muestra lado a lado: llegadas totales, Wq, loss_rate, cola máxima y capacidad reducida para cada escenario corrido con la misma seed.

**[MOSTRAR: Gráficos comparativos de Wq_mean_sec, loss_rate, arrivals_total por escenario]**

Estos gráficos de barras comparan directamente los escenarios. S9_critico tiene los peores indicadores: mayor espera, mayor pérdida, mayor cola, más minutos con capacidad reducida. La diferencia con S1_normal es significativa y cuantificable.

**[MOSTRAR: Comparativa de cola máxima y reducción de capacidad — gráfico combinado]**

Cola máxima y minutos con capacidad reducida lado a lado. Esto muestra la relación directa entre pérdida de infraestructura y congestión.

---

## Segmento 7 — Interpretación y Hallazgos

**[SCROLL HASTA: Panel de interpretación automática]**

El dashboard genera una interpretación automática de cada corrida. Para S1_normal: espera moderada compatible con operación cargada pero funcional, pérdida contenida. Para S9_critico: tiempos de espera altos, tasa de pérdida elevada, minutos significativos con capacidad reducida.

Cuatro hallazgos clave:

**Primero**: la mediana de espera en cero segundos indica que una parte importante de clientes accede sin demora, pero otra fracción experimenta congestión real. El promedio no cuenta toda la historia.

**Segundo**: la pérdida es sensible a la reducción de capacidad. S5, S6 y S7 muestran cómo pierde un ATM y la pérdida sube.

**Tercero**: el calendario laboral — fin de mes, quincena — se refleja en la presión de llegadas, no en la infraestructura. Mismos 4 ATM, más demanda.

**Cuarto**: el abandono no depende solo del tiempo de espera. También de la longitud visible de la cola y de la indisponibilidad percibida. El modelo captura eso con umbral más probabilidad Bernoulli condicionada al nivel de presión compuesta.

---

## Segmento 8 — Integración: Del Dataset al Simulador

**[MOSTRAR: `diagrams/atm_data_model.svg`]**

El proyecto tiene dos pilares complementarios:

**Pilar 1**: captura y estructuración de datos observacionales reales — el aplicativo web que Carlos desarrolló para registrar datos en campo, que alimenta el dataset estructural con las variables del proyecto.

**Pilar 2**: construcción del modelo de simulación de eventos discretos — lo que acabo de presentar: el simulador SimPy con 9 escenarios, motor pseudoaleatorio, trazabilidad completa y KPIs de salida.

Los tres logs de salida — customer_event_log, atm_state_log y system_snapshot_log — son coherentes entre sí. Cada evento de cliente se corresponde con un cambio de estado ATM y un snapshot agregado en el mismo instante. Esa trazabilidad entre evento individual, estado de recurso y estado agregado del sistema es obligatoria para cualquier trabajo de simulación serio.

**[MOSTRAR brevemente: una fila de cada CSV de salida]**

**[SEÑALAR: `outputs/S1_normal/seed42/customer_event_log.csv`]**

Cada fila tiene: quién llegó, cuándo, qué operación inferida, cuánto esperó, si abandonó, por qué, en qué ATM fue atendido, y todas las variables de contexto — franja horaria, tipo de pico, nivel compuesto de presión.

**[SEÑALAR: `outputs/S1_normal/seed42/atm_state_log.csv`]**

Cada cambio de estado del ATM queda registrado: cuándo empieza, cuándo termina, en qué estado estaba, si tenía efectivo, si hubo falla o mantenimiento.

**[SEÑALAR: `outputs/S1_normal/seed42/system_snapshot_log.csv`]**

Cada minuto se captura el estado agregado: cola total, ATM activos, ocupados, fallidos, en cashout, y el nivel de presión compuesta.

---

## Cierre

El valor de este modelo no está en predecir el futuro. Está en permitir experimentación controlada: si quitamos un ATM, cuánto sube la cola. Si es fin de mes, cuántos clientes perdemos. Si hay falla y cashout simultáneo, colapsa el sistema. Esas son preguntas que un modelo analítico puro no puede responder. La simulación de eventos discretos sí.

**[PAUSA — FIN DE LA PARTE DE RENDO]**

---

## Checklist Pre-Presentación

- [ ] Ejecutar `source .venv/bin/activate && streamlit run streamlit_app.py`
- [ ] Verificar que S1_normal con seed 42 corre sin errores
- [ ] Verificar que S9_critico con seed 42 corre sin errores
- [ ] Tener los diagramas SVG abiertos en pestañas del navegador
- [ ] Tener el editor de código preparado para mostrar `domain.py`, `random.py`, `policies.py`, `config.py`
- [ ] Tener el spec `docs/ATM_SIMULATION_SPEC.md` accesible por si hay preguntas
- [ ] Cerrar aplicaciones innecesarias para evitar lentitud durante la demo