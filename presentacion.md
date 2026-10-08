# Financial News Sentiment Analysis

## Diapositiva 1 — Portada

### Proyecto de Sistemas Distribuidos

- Análisis de sentimiento financiero en tiempo real
- Arquitectura basada en MQTT + Python + MongoDB + Node-RED
- Flujo de eventos distribuido para procesar noticias financieras

---

## Diapositiva 2 — Objetivo del proyecto

### ¿Qué queremos resolver?

- Hay un flujo continuo de noticias financieras no estructuradas
- Queremos convertir titulares y descripciones en eventos útiles
- Buscamos hacerlo en tiempo real, con observabilidad y bajo acoplamiento

### Resultado esperado

- Ingesta de noticias desde NewsAPI
- Análisis semántico con VADER
- Identificación de ticker relevante
- Persistencia en MongoDB
- Dashboard visual para monitorización

---

## Diapositiva 3 — Arquitectura general

```text
Producer --> MQTT Broker --> Analyzer --> MongoDB
                        \                 /
                         \--> Node-RED --> Dashboard
```

### Componentes clave

- Producer: obtiene artículos de NewsAPI o genera noticias sintéticas
- Broker MQTT: Mosquitto, coordina la comunicación por topics
- Analyzer: detecta ticker y calcula sentimiento con VADER
- DB Writer: persiste crudos y analizados en MongoDB
- Node-RED: visualización del dashboard

---

## Diapositiva 4 — Por qué MQTT

### Ventajas

- Comunicación desacoplada entre productores y consumidores
- Muy apropiado para flujos de eventos y telemetría
- Fácil integración con servicios heterogéneos
- Escala natural para sistemas distribuidos

### En este proyecto

- Los servicios no se llaman directamente entre sí
- Se comunican vía topics jerárquicos y eventos
- La arquitectura es extensible y tolera cambios parciales

---

## Diapositiva 5 — Topología y topics

### Topics principales

- `news/articles/raw` -> mensajes originales
- `news/articles/analyzed` -> mensajes procesados
- `news/alerts` -> alertas por sentimiento extremo
- `news/status/producer` -> estado del productor

### Decisión de diseño

- Se usa una convención jerárquica clara y consistente
- El estado del productor utiliza retained message y LWT

---

## Diapositiva 6 — Analizador de sentimiento

### ¿Qué hace?

- Recibe el artículo desde MQTT
- Busca ticker financiero en el texto combinado
- Aplica VADER sobre título + descripción
- Calcula scores: `compound`, `pos`, `neu`, `neg`
- Asigna etiqueta: positive / neutral / negative

### Regla de negocio

- `compound >= 0.05` -> positive
- `compound <= -0.05` -> negative
- resto -> neutral

### Alertas

- Si `abs(compound) > 0.6`, se publica una alerta en `news/alerts`

---

## Diapositiva 7 — Persistencia en MongoDB

### ¿Qué almacenamos?

- artículos crudos completos
- artículos analizados con sentimiento y ticker
- metadatos: `id`, `timestamp`, `source_name`, `url`, etc.

### ¿Por qué MongoDB?

- documentos JSON-like
- ideal para datos semiestructurados
- consulta y análisis posterior sencilla

### Idempotencia

- Se usa `replace_one` con `id` para evitar duplicados
- estrategia simple y adecuada para este proyecto

---

## Diapositiva 8 — Node-RED y dashboard

### ¿Qué aporta?

- visualización del flujo de mensajes
- monitorización del sistema en tiempo real
- integración directa con MQTT

### Estado actual

- flow exportado en JSON y versionado en el repositorio
- visible en http://localhost:1880
- conectado al broker MQTT

---

## Diapositiva 9 — Validación real del proyecto

### Evidencia ejecutada

- `pytest` ejecutado y en verde
- `ruff check .` ejecutado y en verde
- Docker levantado con `docker compose up -d --force-recreate`
- MongoDB con mensajes persistidos

### Resultado esperado en la demo

- noticias entrando por NewsAPI o mock
- análisis VADER en tiempo real
- persistencia y dashboard funcionando en paralelo

---

## Diapositiva 10 — Fortalezas del diseño

- desacoplamiento funcional
- arquitectura fácilmente extensible
- observabilidad con dashboard
- persistencia real y comprobada
- validación con entorno Docker y flujo real

### Beneficio principal

La solución no es sólo un ejercicio académico; es un sistema operativo con pipeline distribuido funcionando de forma clara para la demo.

---

## Diapositiva 11 — Límites y mejoras futuras

### Limitaciones actuales

- broker con una sola instancia
- MongoDB centralizado
- idempotencia básica, no distribuida
- pruebas de integración todavía mejorables

### Mejoras futuras

- cluster o particionado del broker
- replicación de MongoDB
- métricas y healthchecks más avanzados
- dashboard más detallado por ticker y fuente

---

## Diapositiva 12 — Conclusión

### Mensaje final

Este proyecto demuestra cómo construir un sistema distribuido para análisis de sentimiento financiero con:

- productores desacoplados
- comunicación por eventos
- análisis semántico aplicado
- almacenamiento documental
- observabilidad visual

### En una frase

Es una arquitectura realista de procesamiento de noticias financieras, con una base sólida para ampliación y defensa técnica.

---

## Diapositiva 13 — Cierre / preguntas

### Gracias

- ¿Preguntas?
- ¿Qué parte prefieren que profundicemos?

### Sugerencia para la defensa

- empezar por la arquitectura
- mostrar flujo de mensajes
- mostrar evidencias de Docker y MongoDB
