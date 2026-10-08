# Distributed Financial Sentiment Analysis

## Diapositiva 1 — Portada

### Proyecto de Sistemas Distribuidos

- Análisis de sentimiento financiero en tiempo real
- Arquitectura basada en MQTT + Python + MongoDB + Node-RED
- Flujo de eventos distribuido para detectar sentimiento en publicaciones financieras

---

## Diapositiva 2 — Objetivo del proyecto

### ¿Qué queremos resolver?

- Tenemos un flujo continuo de mensajes de redes sociales y foros financieros
- Necesitamos transformar texto no estructurado en información útil para el mercado
- Queremos hacerlo en tiempo real, con desacoplamiento entre componentes y observabilidad

### Resultado esperado

- Publicaciones crudas en Kafka/MQTT
- Análisis semántico con VADER
- Identificación de ticker relevante
- Persistencia en base de datos documental
- Dashboard visual para monitorización

---

## Diapositiva 3 — Arquitectura general

```text
Producer --> MQTT Broker --> Analyzer --> MongoDB
                        \                 /
                         \--> Node-RED --> Dashboard
```

### Componentes clave

- Producer: genera publicaciones sintéticas o consume Reddit real si hay credenciales
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
- Se comunican via topics jerárquicos y eventos
- La arquitectura es extensible y tolera cambios parciales

---

## Diapositiva 5 — Topología y topics

### Topics principales

- `reddit/posts/raw` → mensajes originales
- `reddit/posts/analyzed` → mensajes procesados
- `reddit/alerts` → alertas por sentimiento extremo
- `reddit/status/producer` → estado del productor

### Decisión de diseño

- Se normalizó la convención para evitar barras dobles y mejorar claridad
- La estructura sigue un patrón estándar y fácil de observar

---

## Diapositiva 6 — Analizador de sentimiento

### ¿Qué hace?

- Recibe el post desde MQTT
- Busca ticker financiero en el título
- Aplica VADER sobre el texto
- Calcula scores: `compound`, `pos`, `neu`, `neg`
- Asigna etiqueta: positivo / neutro / negativo

### Regla de negocio

- `compound >= 0.05` → positivo
- `compound <= -0.05` → negativo
- resto → neutro

### Alertas

- Si `abs(compound) > 0.6`, se publica una alerta en `reddit/alerts`

---

## Diapositiva 7 — Persistencia en MongoDB

### ¿Qué almacenamos?

- mensajes crudos completos
- mensajes analizados con sentimiento y ticker
- metadatos: `id`, `timestamp`, `subreddit`, etc.

### ¿Por qué MongoDB?

- JSON-like documents
- ideal para flujos semiestructurados
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
- MongoDB con mensajes reales persistidos

### Resultados reales

- `raw= 1195`
- `analyzed= 1193`

Esto demuestra que el sistema funciona end-to-end y no solo a nivel unitario.

---

## Diapositiva 10 — Fortalezas del diseño

- desacoplamiento funcional
- arquitectura fácilmente extensible
- observabilidad con dashboard
- persistencia real y comprobada
- validación con entorno Docker y flujo real

### Beneficio principal

La solución no es solo un ejercicio académico; es un sistema operativo con pipeline distribuido funcionando en entorno real.

---

## Diapositiva 11 — Límites y mejoras futuras

### Limitaciones actuales

- broker con una sola instancia
- MongoDB centralizado
- idempotencia básica, no distribuida
- pruebas de integración todavía mejorables

### Mejoras futuras

- particionado y cluster para broker
- replicación de MongoDB
- métricas y healthchecks más avanzados
- dashboard más detallado por ticker y alertas

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

Es una arquitectura realista de procesamiento de eventos para información financiera, con una base sólida para ampliación y defensa técnica.

---

## Diapositiva 13 — Cierre / preguntas

### Gracias

- ¿Preguntas?
- ¿Qué parte prefieren que profundicemos?

### Sugerencia para la defensa

- empezar por la arquitectura
- mostrar flujo de mensajes
- mostrar evidencias de Docker y MongoDB
- cerrar con fortalezas y mejoras futuras

---

## Instrucciones para PowerPoint o exportación

Si el proyecto exige una presentación en PowerPoint, la forma más práctica es:

1. Usar esta presentación como base narrada en Markdown.
2. Exportarla a HTML o PDF si se usa Marp.
3. Copiar el contenido en una presentación de PowerPoint.
4. Mantener 1 idea por diapositiva y 30-60 segundos de explicación cada una.
5. Añadir una diapositiva final con “Conclusión y preguntas”.

Opciones recomendadas:

- Marp + VS Code: permite generar slides desde markdown
- PowerPoint: crear slides con los mismos títulos y contenido
- Google Slides: alternativa rápida si no se dispone de PowerPoint

