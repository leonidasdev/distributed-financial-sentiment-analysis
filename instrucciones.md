# Instrucciones de ejecución y memoria

## Objetivo

Este documento sirve como guía de trabajo para levantar el proyecto desde cero, hacer una demo con datos reales de NewsAPI y volver a un modo estable con mock cuando convenga.

## 1. Limpieza completa del entorno

Antes de empezar una demo nueva, dejar el entorno limpio:

```powershell
Set-Location "c:\Users\Leo\OneDrive - Universidad Politécnica de Madrid\1st half - 5th year\sistemas distribuidos\group project\distributed-financial-sentiment-analysis"
docker compose down --volumes --remove-orphans
```

Esto elimina contenedores, red y volúmenes del proyecto.

## 2. Arranque limpio del proyecto

Levantar el stack desde cero:

```powershell
docker compose up --build -d
```

Comprobar que todo está arriba:

```powershell
docker compose ps
```

Servicios esperados:

- `broker-mqtt`
- `db-mongodb`
- `producer-newsapi`
- `analyzer-sentiment`
- `consumer-db`
- `dashboard-nodered`

## 3. Modo NewsAPI real para la demo

El proyecto puede usar datos reales de NewsAPI durante unos minutos para enseñar el flujo con artículos auténticos.

### 3.1 Activar NewsAPI real

En `.env` o temporalmente en la sesión de shell:

```powershell
$env:NEWSAPI_USE_MOCK = "false"
docker compose up -d --build producer-newsapi
```

Si ya está todo levantado, basta con recrear el productor.

### 3.2 Qué enseñar

- el productor publica artículos reales
- el analizador extrae ticker y sentimiento
- MongoDB guarda el evento crudo y el analizado
- Node-RED recibe el flujo analizado y las alertas

### 3.3 Volver a mock

Cuando queráis estabilizar la demo:

```powershell
$env:NEWSAPI_USE_MOCK = "true"
docker compose up -d --build producer-newsapi
```

## 4. Validación de estado

Comandos útiles:

```powershell
docker compose logs -f producer-newsapi
docker compose logs -f analyzer-sentiment
docker compose logs -f consumer-db
docker compose logs -f dashboard-nodered
```

Comprobar MongoDB:

```powershell
docker exec -it db-mongodb mongosh
```

Ejemplos de consulta:

```javascript
use news_analytics
db.raw_articles.countDocuments()
db.sentiment_analyzed.countDocuments()
```

## 5. Capturas para la memoria

### 5.1 Capturas necesarias

- Arquitectura general del sistema
- Flow de Node-RED con los topics nuevos
- Productor funcionando con NewsAPI real
- MongoDB con documentos insertados
- Dashboard mostrando análisis y alertas
- Docker Compose con todos los servicios arriba

### 5.2 Orden recomendado

1. Capturar Docker Compose arriba
2. Capturar Node-RED con el flow abierto
3. Capturar una noticia real entrando
4. Capturar MongoDB con datos persistidos
5. Capturar dashboard y alertas

## 6. Capturas para la presentación

- una diapositiva de arquitectura
- una captura del flujo de Node-RED
- una captura de un artículo real de NewsAPI entrando al sistema
- una captura del dashboard con el resultado final
- una captura de Docker o del terminal mostrando la ejecución

## 7. Qué debe saber cada miembro

### Miembro 1

- arquitectura global
- MQTT, topics, QoS y retained messages
- Node-RED y demo visual

### Miembro 2

- NewsAPI y productor
- variables de entorno y modo mock
- MongoDB y persistencia

### Ambos

- PACELC y trade-offs
- limitaciones del sistema
- trabajo futuro
- respuestas a preguntas del tribunal

## 8. Mensajes clave para defender el diseño

- MQTT es el eje distribuido obligatorio del proyecto.
- NewsAPI mejora la calidad de los datos frente a Reddit.
- La base de datos se mantiene centralizada por simplicidad y estabilidad de demo.
- PACELC favorece latencia y operatividad en esta entrega.
- El modo mock permite repetir la demo sin depender siempre de la API externa.

## 9. Checklist final antes de entregar

- [ ] Stack levantado y probado
- [ ] NewsAPI validado con una tanda real breve
- [ ] Mock activado otra vez para demo estable
- [ ] Capturas hechas
- [ ] Memoria revisada
- [ ] Presentación final lista
- [ ] Flow de Node-RED exportado a PDF

## 10. Nota operativa

Si algo no cuadra en la demo, volver a mock primero. El objetivo es enseñar un sistema estable y reproducible, no forzar una dependencia externa en el último minuto.
