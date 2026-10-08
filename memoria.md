# Memoria del proyecto: Distributed Financial Sentiment Analysis

## 1. Problema y motivación

En los mercados financieros, la percepción del sentimiento público puede influir en la evolución de precios y en la toma de decisiones de inversores. Sin embargo, la información de redes sociales y foros financieros aparece en forma de flujos continuos y heterogéneos, con gran volumen y poca estructura. Para convertir esos datos en información útil, es necesario procesarlos en tiempo real y combinarlos con técnicas de análisis de opinión.

Este proyecto propone un sistema distribuido basado en MQTT para ingestar publicaciones generadas de forma sintética o real, analizarlas con VADER, detectar tickers relevantes y persistir tanto los mensajes originales como los resultados enriquecidos en MongoDB. La solución se diseñó como una arquitectura orientada a eventos con desacoplamiento entre productores, consumidores y almacenamiento, con un componente visual de monitorización mediante Node-RED.

La motivación principal es demostrar, de forma aplicada, cómo un sistema publish/subscribe permite construir un pipeline de análisis distribuidos con baja acoplamiento, escalabilidad horizontal y capacidad de observabilidad en tiempo real.

## 2. Diseño del sistema

### 2.1 Arquitectura global

El sistema está compuesto por los siguientes componentes:

- Productor: genera mensajes de tipo Reddit sintéticos o intenta consumir Reddit real si hay credenciales configuradas.
- Broker MQTT: Mosquitto, que actúa como middleware central de comunicación.
- Analizador: consume mensajes crudos, extrae el ticker, calcula el sentimiento con VADER y publica el resultado enriquecido.
- Persistencia: MongoDB almacena tanto mensajes originales como analizados.
- Dashboard: Node-RED subscribido a los topics de análisis y alertas para visualizar eventos en tiempo real.

El flujo principal es:

1. El productor publica mensajes en `reddit/posts/raw`.
2. El analizador se suscribe a dicho topic.
3. El analizador analiza el texto, detecta el ticker y publica el resultado en `reddit/posts/analyzed`.
4. El escritor a MongoDB recibe ambos topics y persiste los documentos.
5. Node-RED consume el topic analizado y las alertas para monitorizar el sistema.

### 2.2 Diagrama de componentes

```text
+-------------------+        MQTT        +-------------------+
| Producer          | ----------------> | Mosquitto Broker  |
| (mock / Reddit)   |                    | MQTT              |
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

El proyecto usa una topología muy simple, pero efectiva, de tipo publish/subscribe con broker central:

- `reddit/posts/raw`: eventos generados por el productor.
- `reddit/posts/analyzed`: resultados del analizador.
- `reddit/alerts`: alertas por sentimiento extremo.
- `reddit/status/producer`: estado del productor con retained message.

Se eligió una jerarquía de topics ordenada y estándar, eliminando barras dobles para evitar complejidad y mejoras de interoperabilidad. Los topics siguen una estructura jerárquica clara y legible, compatible con consumidores típicos de MQTT.

### 2.4 Semántica de recepción y publicación

En MQTT, la elección del nivel QoS condiciona la fiabilidad de entrega. En este proyecto se usa:

- QoS 1 para mensajes de negocio críticos: `reddit/posts/raw` y `reddit/posts/analyzed`.
- QoS 0 para alertas no críticas: `reddit/alerts`.

Esto implica una semántica de tipo at-least-once para los eventos principales. La aplicación asume que un mensaje duplicado puede aparecer en caso de reintento del broker o reconexión del cliente; por eso el sistema usa `replace_one` con `id` como clave de idempotencia básica en MongoDB. Esto evita duplicados de persistencia de un mismo evento, aunque no reemplaza una estrategia de deduplicación más fuerte para sistemas distribuidos a mayor escala.

En términos de la taxonomía de entrega:

- at-most-once: no es el modelo elegido
- at-least-once: sí es el modelo principal
- exactly-once: no se implementa de forma nativa por MQTT; se hace parcialmente mediante upsert en MongoDB

### 2.5 Base de datos distribuida

Se usa MongoDB como almacenamiento persistente. Aunque no es un sistema distribuido multi-nodo en la práctica de esta entrega, la persistencia está diseñada para un patrón de almacenamiento centralizado con índices sobre campos de consulta relevantes.

Modelos de consulta:

- `raw_posts`: índice sobre `ticker_hint` y `timestamp`
- `sentiment_analyzed`: índice sobre `ticker` y `timestamp`

La decisión de usar MongoDB es razonable para este caso por su capacidad para guardar documentos JSON, su rapidez y su compatibilidad con flujos de datos semiestructurados.

## 3. Implementación del análisis de sentimiento

El analizador recibe un post, detecta el ticker del título mediante una expresión regular sobre una lista de símbolos financieros predefinida y aplica VADER. El cálculo se genera sobre el texto del título, que es la parte más clara y descriptiva del post.

La salida incluye:

- `compound`
- `pos`, `neu`, `neg`
- `label` calculado con thresholds claros:
  - `>= 0.05` → positivo
  - `<= -0.05` → negativo
  - en otro caso → neutro

Además, si el valor absoluto del compound supera 0.6, se genera una alerta en `reddit/alerts`.

## 4. Patrones de arquitectura orientada a eventos

Se aplican varios principios de arquitectura orientada a eventos:

- desacople entre productores y consumidores mediante el broker MQTT
- flujo basado en eventos en lugar de llamadas síncronas directas
- persistencia de eventos en MongoDB para análisis posterior
- uso de mensajes de estado con retained message para conocer el estado del productor

Este proyecto no implementa un patrón formal completo de Event Sourcing ni CQRS, pero sí usa una lógica orientada a eventos muy clara y fiel a la asignatura.

## 5. Conclusiones

El sistema cumple con el eje mínimo exigido por el enunciado: usa MQTT como mecanismo central de comunicación y combina este patrón con procesamiento de datos y persistencia. La estructura modular hace que sea fácilmente extensible y la integración con Node-RED permite monitorización visual con poco esfuerzo.

Los principales beneficios son:

- desacoplamiento entre componentes
- tolerancia a cambios de implementación de cada módulo
- observabilidad mejorada gracias a MQTT y dashboard visual
- capacidad de expansión a más productores o análisis

Las limitaciones principales son:

- uso de un único broker, sin replicas ni cluster
- persistencia centralizada sin sharding ni replicación distribuidos
- lack de pruebas de integración completas con escenarios de desconexión o errores de red
- idempotencia solo parcial, no completa para escenarios de producción extremo

## 6. Trabajo futuro

- incorporar Kafka como alternativa o evolución del sistema para particiones y grupos de consumidores
- añadir réplicas o clúster de MongoDB
- implementar healthchecks más completos y métricas de monitorización
- mejorar la idempotencia con claves compuestas o colecciones de control
- ampliar Node-RED con paneles más avanzados y visualizaciones por ticker
- contemplar un modelo de seguridad con autenticación MQTT y controles de acceso

## 7. Conclusión final

El proyecto demuestra un pipeline completo y funcional de análisis financiero basado en publish/subscribe, donde Python, MQTT y MongoDB trabajan de manera coordenada. Aun cuando se puede mejorar la robustez operativa y la escala, la solución cumple adecuadamente el objetivo académico propuesto y deja una base sólida para ampliación y defensa oral.
