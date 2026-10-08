# Notas técnicas y de presentación

## 1. Idea central

El proyecto convierte un flujo continuo de noticias financieras en eventos distribuidos que pueden analizarse, persistirse y visualizarse en tiempo real. La fuente de datos ya no es Reddit: ahora usamos NewsAPI para trabajar con artículos de mayor calidad y evitar depender de la API de Reddit.

## 2. Mensaje técnico principal

La arquitectura se apoya en MQTT como eje de comunicación. Producer, analyzer y DB writer no se llaman entre sí directamente; sólo intercambian mensajes a través del broker. Esto reduce el acoplamiento y simplifica la demostración de la asignatura.

## 3. Qué hace cada componente

### 3.1 Producer

- obtiene artículos reales desde NewsAPI o genera artículos sintéticos en modo mock
- publica `news/articles/raw`
- mantiene estado online/offline con retained message y LWT
- permite variar intervalos y palabras clave por variables de entorno

### 3.2 Analyzer

- consume `news/articles/raw`
- combina título y descripción
- detecta ticker financiero con una expresión regular
- aplica VADER al texto completo
- publica `news/articles/analyzed`
- publica `news/alerts` si el sentimiento es extremo

### 3.3 DB writer

- consume artículos crudos y analizados
- persiste en MongoDB con `replace_one` por `id`
- crea índices sobre `source_name`/`timestamp` y `ticker`/`timestamp`

### 3.4 Node-RED

- escucha los topics analizados y de alerta
- permite enseñar el flujo en directo durante la demo
- sirve como pieza visual para la defensa oral

## 4. Puntos importantes para explicar

- NewsAPI ofrece noticias más limpias y más controladas que un stream de Reddit.
- MQTT encaja bien porque necesitamos un canal pub/sub y eventos desacoplados.
- La idempotencia en MongoDB es básica, pero suficiente para la entrega.
- El modo mock permite demostrar el sistema sin depender de credenciales externas.
- La solución está validada con tests unitarios y con el arranque local en Docker.

## 5. Flujo de mensajes

1. el productor publica un artículo
2. el analizador consume el artículo
3. el analizador enriquece el evento con ticker y sentimiento
4. MongoDB guarda la versión cruda y la analizada
5. Node-RED visualiza el resultado

## 6. Preguntas probables del tribunal

- ¿Por qué NewsAPI en lugar de Reddit?
- ¿Por qué MQTT y no una simple llamada HTTP entre servicios?
- ¿Cómo se evita duplicar información en MongoDB?
- ¿Qué ocurre si el broker cae?
- ¿Qué se podría escalar en una versión más avanzada?

## 7. Respuestas cortas recomendadas

- NewsAPI mejora la calidad y estabilidad de la fuente.
- MQTT desacopla componentes y hace más clara la arquitectura distribuida.
- `replace_one` con `id` reduce duplicados en persistencia.
- Si cae el broker, el sistema se degrada, pero el diseño es fácil de reanudar.
- Lo más natural para crecer sería añadir replicación, más consumers o incluso Kafka.

## 8. Demo

Durante la demo conviene mostrar:

- Docker Compose levantado
- productor publicando
- analizador recibiendo eventos
- MongoDB con documentos persistidos
- Node-RED mostrando el flujo

## 9. Cierre

La idea que debe quedar clara es que el sistema no depende de una red social concreta. El cambio a NewsAPI mejora la calidad de la fuente y hace la demo más robusta y defendible.
