# Memoria del proyecto: Financial News Sentiment Analysis

## 1. Problema y motivación

En los mercados financieros, el flujo de noticias influye en la percepción pública, en la toma de decisiones y en la evolución de los precios. Sin embargo, la información llega de forma continua, heterogénea y poco estructurada. El objetivo de este proyecto es transformar ese flujo de noticias en eventos útiles que puedan analizarse y visualizarse en tiempo real.

La solución propuesta combina NewsAPI como fuente de artículos, MQTT como eje de comunicación, VADER para el análisis de sentimiento, MongoDB para persistencia y Node-RED para la visualización. El sistema se ha diseñado como una arquitectura orientada a eventos con productores y consumidores desacoplados.

## 2. Diseño del sistema

### 2.1 Arquitectura global

El sistema está compuesto por los siguientes componentes:

- Productor: obtiene artículos de NewsAPI o genera noticias sintéticas en modo mock.
- Broker MQTT: Mosquitto, que centraliza la comunicación publish/subscribe.
- Analizador: consume noticias crudas, detecta tickers relevantes y calcula sentimiento con VADER.
- Persistencia: MongoDB almacena tanto los artículos originales como los enriquecidos.
- Dashboard: Node-RED consume los topics analizados y de alerta para visualizar el flujo.

El flujo principal es:

1. El productor publica artículos en `news/articles/raw`.
2. El analizador se suscribe a ese topic.
3. El analizador evalúa el texto, detecta el ticker y publica el resultado en `news/articles/analyzed`.
4. El writer de MongoDB persiste los documentos crudos y analizados.
5. Node-RED consume el topic analizado y las alertas para monitorizar el sistema.

### 2.2 Diagrama de componentes

```text
+-------------------+        MQTT        +-------------------+
| Producer          | ----------------> | Mosquitto Broker  |
| (mock / NewsAPI)  |                    | MQTT              |
+-------------------+                    +-------------------+
                                                 |
                                                 v
                                        +-------------------+
                                        | Analyzer          |
                                        | VADER + ticker    |
                                        +-------------------+
                                                 |
                                                 v
                                        +-------------------+
                                        | DB Writer         |
                                        | MongoDB           |
                                        +-------------------+
                                                 |
                                                 v
                                        +-------------------+
                                        | Node-RED          |
                                        | Dashboard         |
                                        +-------------------+
```

### 2.3 Topología MQTT

La topología MQTT es simple y legible, con topics jerárquicos para cada fase del pipeline:

- `news/articles/raw`: artículos crudos publicados por el productor.
- `news/articles/analyzed`: resultados enriquecidos del analizador.
- `news/alerts`: alertas por sentimiento extremo.
- `news/status/producer`: estado del productor con retained message.

El diseño evita barras dobles y mantiene una convención consistente. Además, el estado del productor usa retained message y Last Will & Testament para facilitar observabilidad.

### 2.4 Semántica de entrega

En este proyecto se utiliza principalmente QoS 1 para los mensajes de negocio críticos:

- `news/articles/raw`
- `news/articles/analyzed`

Las alertas usan QoS 0 porque son eventos auxiliares de observabilidad. El compromiso elegido es at-least-once para el flujo principal. Para evitar duplicados en persistencia se usa `replace_one` con `id` como clave básica de idempotencia.

### 2.5 Persistencia en MongoDB

MongoDB se utiliza como almacén documental para guardar tanto el artículo original como el analizado. La colección cruda indexa `source_name` y `timestamp`, mientras que la colección analizada indexa `ticker` y `timestamp`.

Aunque en esta entrega no se despliega un cluster distribuido real, la elección de MongoDB encaja bien con el formato JSON de los mensajes y con la evolución futura hacia particionado o replicación.

En la defensa oral conviene explicar este punto con claridad: la asignatura exige como mínimo un sistema publish/subscribe, y ese eje está cubierto por MQTT. La base de datos se mantiene centralizada de forma deliberada para no aumentar la complejidad operativa del proyecto ni comprometer la demo, pero el diseño deja abierta la evolución hacia un replica set o un despliegue sharded.

Desde el punto de vista PACELC, la solución actual prioriza latencia y simplicidad operativa sobre una consistencia distribuida fuerte en la capa de persistencia. En ausencia de un cluster real, el proyecto opta por una implementación centralizada con idempotencia en la aplicación y deja el salto a replica set o sharding como mejora futura. Esto es coherente con el objetivo de la asignatura: demostrar una arquitectura distribuida basada en eventos y una demo estable, no montar una plataforma de almacenamiento compleja innecesaria.

## 3. Implementación del análisis de sentimiento

El analizador recibe el título y la descripción del artículo, construye un texto combinado y aplica VADER. Para extraer el ticker usa una expresión regular sobre una lista de símbolos financieros conocida.

La salida incluye:

- `compound`
- `pos`, `neu`, `neg`
- `label` calculado con los siguientes umbrales:
  - `>= 0.05` -> positive
  - `<= -0.05` -> negative
  - en otro caso -> neutral

Si el valor absoluto del `compound` supera 0.6, el analizador publica una alerta adicional en `news/alerts`.

## 4. Patrones de arquitectura orientada a eventos

El proyecto aplica varios principios de arquitectura orientada a eventos:

- desacoplamiento entre productor, analizador y almacenamiento
- comunicación asíncrona mediante broker MQTT
- persistencia de eventos para análisis posterior
- mensajes retained para estado operativo
- uso de alertas como canal complementario de observabilidad

No se ha implementado Event Sourcing completo ni CQRS, pero sí una arquitectura claramente guiada por eventos.

## 5. Conclusiones

La solución cumple el requisito mínimo de la asignatura al usar MQTT como eje de comunicación y combinarlo con procesamiento y persistencia de datos. La modularidad del diseño facilita la demostración en vivo y la posible ampliación posterior.

Los principales beneficios son:

- desacoplamiento entre componentes
- observabilidad con Node-RED y retained messages
- persistencia de documentos en formato natural para análisis posterior
- posibilidad de usar datos reales o mock según el contexto de demo

Las limitaciones principales son:

- broker único sin replicación
- MongoDB centralizado
- idempotencia básica, no distribuida
- dependencia de la cuota de NewsAPI en modo real

## 6. Trabajo futuro

- añadir una capa de cache o colas auxiliares para absorber ráfagas
- incorporar réplica o cluster en MongoDB si el volumen de datos crece
- ampliar Node-RED con métricas por ticker y por fuente
- añadir pruebas de integración con contenedores efímeros
- explorar Kafka como evolución natural para más particiones y consumidores
- revisar un shard key razonable si el equipo decide llevar el almacenamiento a sharding en una iteración futura

## 7. Cierre

El proyecto demuestra un pipeline distribuido completo para análisis de noticias financieras en tiempo real, con una arquitectura sencilla de explicar y una implementación suficientemente sólida para la presentación y la defensa oral.
