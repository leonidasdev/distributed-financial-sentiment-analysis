# Notas técnicas y de presentación

## 1. Contexto del proyecto

Este proyecto responde a un problema típico de sistemas distribuidos: procesar un flujo de mensajes no estructurados en tiempo real y convertirlos en información útil para un dominio específico. En este caso, el dominio es el mercado financiero y el análisis de sentimiento de publicaciones relacionadas con tickers y activos.

El Sistema se compone de varios componentes autónomos que intercambian información mediante MQTT. Esta elección reduce el acoplamiento entre servicios y permite manejar eventos en streaming de forma clara, robusta y extensible.

## 2. Teoría relevante

### 2.1 Sistemas distribuidos y mensajería asíncrona

En un sistema distribuido, cada componente puede ejecutarse de forma independiente y comunicarse a través de un middleware de mensajería. MQTT es un protocolo ligero muy utilizado en IoT y sistemas de eventos, especialmente cuando el volumen es moderado y la latencia es crítica.

Ventajas:

- desacoplamiento entre productores y consumidores
- comunicación basada en eventos
- fácil monitorización
- tolerancia a fallos parcial y recuperación incremental

Desventajas:

- requerimientos de diseño más cuidadosos para idempotencia
- dependencias en el broker
- necesidad de señales de control y monitorización

### 2.2 Patrón publish/subscribe

El patrón publish/subscribe elimina el acoplamiento directo entre componentes. Un productor no conoce quién consume el mensaje; solo publica en un topic. Los consumidores se suscriben a los topics relevantes y reaccionan cuando llega el evento.

Esto encaja muy bien con la necesidad de insertar un analizador entre productor y almacenamiento sin que exista dependencia directa entre ambos.

### 2.3 Análisis de sentimiento

El análisis de sentimiento operativo pretende detectar si un texto refleja tono positivo, negativo o neutro. En este proyecto se usa VADER, un modelo ligero y muy adecuado para textos cortos de redes sociales y comentarios.

Ventajas de VADER:

- funciona bien con texto informal y acortado
- no requiere entrenamiento pesado
- ofrece scores de polaridad útiles para análisis rápido

## 3. Arquitectura del sistema

### 3.1 Productor

El productor genera publicaciones con una estructura tipo:

```json
{
  "id": "uuid",
  "subreddit": "stocks",
  "ticker_hint": "NVDA",
  "title": "Bullish setup on NVDA after strong guidance",
  "author": "user_1234",
  "timestamp": "2026-10-08T12:00:00Z"
}
```

Tiene dos modalidades:

- mock generator: para pruebas locales y despliegue reproducible
- Reddit real: si se proporcionan credenciales y se activa el cliente real

### 3.2 Broker MQTT

El broker central es Mosquitto. Coordina la entrega de eventos entre todos los módulos. En este proyecto se usa una topología con topics jerárquicos y claros, por ejemplo:

- `reddit/posts/raw`
- `reddit/posts/analyzed`
- `reddit/alerts`
- `reddit/status/producer`

El uso de una convención estándar evita errores de interoperabilidad y simplifica la documentación.

### 3.3 Analizador

El analizador se subscriba a `reddit/posts/raw` y realiza las siguientes operaciones:

1. decodifica el payload JSON
2. obtiene el título
3. detecta ticker financiero
4. aplica VADER
5. calcula el valor compound
6. publica el resultado en `reddit/posts/analyzed`
7. si la alerta es importante, publica en `reddit/alerts`

### 3.4 Persistencia

El writer a MongoDB se ocupa de recibir tanto mensajes raw como analizados. Guarda documentos con:

- contenido original
- resultado del análisis
- timestamp
- source_topic
- ingested_at

Se usa `replace_one` con `id` como fuerza idempotente. Esto evita duplicados si el mismo evento llega dos veces durante un reinicio o reconexión.

### 3.5 Dashboard

Node-RED consume los topics relevantes y permite visualizar el flujo de mensajes. Esto mejora la observabilidad de la aplicación y permite una demostración más visual y didáctica durante la defensa.

## 4. Flujo de ejecución

### 4.1 Arranque del sistema

1. arrancar Docker Desktop
2. ejecutar desde la raíz del proyecto:
   - `docker compose up -d --force-recreate`
3. comprobar contenedores:
   - `docker compose ps`
4. abrir visual dashboard:
   - http://localhost:1880
5. comprobar MongoDB:
   - `docker exec db-mongodb mongosh --quiet --eval "..."`

### 4.2 Flujo de mensajes

- Productor publica en `reddit/posts/raw`
- Analyzer suscrito a ese topic
- Analyzer publica resultado en `reddit/posts/analyzed`
- Writer persiste ambos tipos de mensajes
- Node-RED observa el flujo y muestra estado/alertas

## 5. Puntos clave de la lógica del código

### 5.1 Productor

Responsabilidades:

- crear payload tipo Reddit con ticker, subreddit, autor y timestamp
- publicar estado online/offline con retained message
- publicar mensajes periódicamente con intervalo configurable
- soportar modo mock para desarrollo y validación

### 5.2 Analizador

Responsabilidades:

- conectarse al broker MQTT
- suscribirse al topic raw
- detectar ticker en el texto
- calcular sentimiento
- publicar análisis y alertas según thresholds

### 5.3 MongoDB writer

Responsabilidades:

- conectar a la base
- crear índices sobre `ticker` y `timestamp`
- persistir documentos tanto en raw como en analizados
- usar `replace_one` para evitar duplicados

## 6. Qué explicar en la defensa oral

### Estructura recomendable

1. presentar el problema y la motivación
2. explicar por qué MQTT es una buena solución
3. describir la arquitectura por módulos
4. mostrar el flujo de eventos con un ejemplo real
5. presentar la validación con Docker + MongoDB
6. cerrar con fortalezas, riesgos y mejoras futuras

### Frases guía para la exposición

- “La arquitectura está basada en eventos y desacopla la generación, el análisis y la persistencia.”
- “El broker actúa como middleware central y permite que cada componente evolucione de forma independiente.”
- “La solución no solo está implementada; está validada en entorno real con Docker y MongoDB.”
- “La decisión de normalizar los topics reduce complejidad y mejora interoperabilidad.”

## 7. Riesgos y limitaciones

- dependencia del broker: si cae, el sistema se ve afectado
- idempotencia básica: suficiente para la entrega, no para producción extrema
- falta de clustering y particionado para crecimiento serio
- dashboard aún simple y centrado en demostración, no en un panel de negocio completo

## 8. Mejoras futuras recomendadas

- introducir broker con cluster o particionado
- replicación y sharding en MongoDB
- métricas y observabilidad más avanzadas
- soporte para más fuentes de datos además de Reddit
- panel más completo de análisis y alertas por ticker
- pruebas de integración con contenedores efímeros

## 9. Criterio de evaluación del proyecto

Se valora:

- claridad y modularidad del diseño
- uso correcto de tecnologías distribuidas
- calidad del código y foco en cumplimiento de requisitos
- capacidad de demostrar funcionamiento real
- nivel de documentación y argumentación técnica

## 10. Resumen ejecutivo para la defensa

Este proyecto implementa un pipeline distribuido de análisis de sentimiento financiero con MQTT como capa de comunicación, VADER como motor semántico, MongoDB como almacenamiento persistente y Node-RED como dashboard visual. El sistema se valida con Docker y con datos reales generados durante la ejecución, demostrando que el flujo completo funciona end-to-end. La solución está construida como un sistema de eventos con baja dependencia entre módulos, una arquitectura clara y una base sólida para futuras ampliaciones.

## 11. Sugerencia para preguntas del tribunal

Es útil anticipar preguntas sobre:

- por qué no usamos directamente llamadas REST entre servicios
- cómo se asegura la integridad de los mensajes
- qué pasaría si el broker falla
- qué estrategia de idempotencia se usa
- qué se podría escalar en una versión profesional

## 12. Pista para la demo

Durante la demostración, conviene mostrar:

- que el producer emite mensajes
- que el analyzer procesa mensajes
- que DB Writer persiste
- que Node-RED visualiza resultados
- que los contenedores están arriba y sanos
- que MongoDB tiene documentos insertados

Esto hace que la defensa sea más sólida y convincente.
