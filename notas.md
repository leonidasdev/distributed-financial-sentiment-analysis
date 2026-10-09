# Notas técnicas y de presentación

## 1. Idea central

El proyecto convierte un flujo continuo de noticias financieras en eventos distribuidos que pueden analizarse, persistirse y visualizarse en tiempo real. La fuente de datos es NewsAPI, con modo mock como respaldo para no depender siempre de la API externa.

## 2. Qué debe saber el equipo

### 2.1 Mensaje corto del proyecto

- Resolvemos el problema de procesar noticias financieras como un pipeline distribuido.
- MQTT es el eje publish/subscribe obligatorio de la asignatura.
- MongoDB guarda los documentos y Node-RED enseña el flujo en vivo.
- NewsAPI nos da noticias de mejor calidad que Reddit y evita el problema de credenciales y límites de esa API.

### 2.2 Qué hace cada componente

- `producer-newsapi`: obtiene noticias reales o genera mock, publica `news/articles/raw` y mantiene LWT más retained status.
- `analyzer-sentiment`: consume artículos, combina título y descripción, extrae ticker, calcula sentimiento y publica `news/articles/analyzed` y `news/alerts`.
- `consumer-db`: persiste artículos y resultados analizados con `replace_one` por `id`.
- `dashboard-nodered`: visualiza eventos analizados y alertas.

### 2.3 Qué tiene que dominar cada miembro

- Miembro 1: arquitectura global, MQTT, topics, QoS, demo en Node-RED.
- Miembro 2: productor, NewsAPI, variables de entorno, modo mock y flujo de datos.
- Ambos: análisis de sentimiento, MongoDB, limitaciones, trabajo futuro y preguntas del tribunal.

## 3. Flujo de mensajes

1. el productor publica un artículo en `news/articles/raw`
2. el analizador consume el artículo
3. el analizador enriquece el evento con ticker y sentimiento
4. MongoDB guarda la versión cruda y la analizada
5. Node-RED visualiza el resultado

## 4. PACELC y consistencia

### 4.1 Cómo explicarlo

PACELC dice que, si hay partición, un sistema distribuye entre disponibilidad y consistencia; y si no hay partición, entre latencia y consistencia.

### 4.2 Qué hemos elegido

- En el proyecto actual no desplegamos un cluster MongoDB real, así que la base de datos está centralizada.
- Aun así, la filosofía del sistema es priorizar disponibilidad y baja latencia para la ingesta y la demo, porque el valor principal está en procesar noticias rápido.
- La consistencia se refuerza con `replace_one` por `id` y con índices, no con un cluster complejo.

### 4.3 Trade-off que hay que defender

- Ganamos simplicidad, velocidad de demo y menos riesgo operacional.
- Perdemos una capa de consistencia/replicación distribuida real.
- Para esta asignatura, esa pérdida es aceptable porque el requisito mínimo es MQTT y el caso de uso no necesita una base distribuida pesada para lucir bien.

### 4.4 Si preguntan por una evolución futura

- Replica set de MongoDB: más fácil de justificar que sharding.
- Sharding: útil si el volumen crece mucho y queremos particionar por ticker o por tiempo.
- Si montáramos sharding, el shard key más natural sería algo como `ticker` más tiempo o un hash sobre `id`, según el patrón de consulta.

## 5. Ideas para la demo

- Podemos arrancar con `NEWSAPI_USE_MOCK=false` durante un rato para enseñar noticias reales.
- Si vemos que no hace falta seguir consumiendo cuota, volvemos a `NEWSAPI_USE_MOCK=true` para estabilizar la demo.
- Esa transición no cambia la arquitectura; sólo cambia la fuente de entrada.

## 6. Preguntas probables del tribunal

- ¿Por qué NewsAPI en lugar de Reddit?
- ¿Por qué MQTT y no HTTP directo?
- ¿Cómo se evita duplicar información en MongoDB?
- ¿Qué ocurre si el broker cae?
- ¿Por qué no habéis montado un cluster MongoDB real?

## 7. Respuestas cortas recomendadas

- NewsAPI ofrece noticias más limpias y estables.
- MQTT desacopla componentes y hace la arquitectura más clara.
- `replace_one` con `id` reduce duplicados.
- Si cae el broker, el sistema se degrada pero se puede reanudar fácil.
- No montamos un cluster MongoDB real para no complicar la demo; la mejora está documentada como trabajo futuro.

## 8. Qué mostrar en la defensa

- Docker Compose levantado
- productor publicando
- analizador recibiendo eventos
- MongoDB con documentos persistidos
- Node-RED mostrando el flujo

## 9. Cierre

La idea que debe quedar clara es que el sistema no depende de una red social concreta. NewsAPI mejora la calidad de la fuente, y el modo mock asegura que la demo siga siendo controlable y robusta.
