# TODO

## Estado actual

- [x] Arquitectura Docker Compose y red privada `reddit_net`.
- [x] Broker MQTT, MongoDB, productor, analizador, writer y Node-RED definidos.
- [x] Productor con mock generator, LWT y publicación de estado.
- [x] Analizador VADER con detección de tickers y alertas.
- [x] Persistencia en MongoDB de crudos y analizados.
- [x] README con funcionamiento, esquemas de mensajes y arranque local.
- [x] Aislamiento de dependencias en contenedores y guía para `.venv` local.
- [x] `.gitignore` para evitar subir artefactos de entorno y caché.
- [x] `requirements-dev.txt` para tooling local sin tocar el sistema.
- [x] `pyproject.toml` con configuración de `pytest` y `ruff`.
- [x] Workflow de CI para lint + tests.
- [x] Tests unitarios para lógica pura de los tres servicios.
- [x] Entorno virtual local `.venv` creado y seleccionado en el proyecto.
- [x] Dependencias de desarrollo instaladas en `.venv`.
- [x] `ruff check .` ejecutado y dejado en verde.
- [x] `pytest` ejecutado y dejado en verde.

## Pendiente para entrega de alta calidad

### Prioridad 0: validación real del sistema
- [x] Validar el pipeline completo con `docker compose up --build -d` y comprobar mensajes end-to-end.
- [x] Verificar funcionamiento de Mosquitto, productor, analizador y escritor de MongoDB.
- [x] Confirmar que la persistencia real en MongoDB guarda mensajes crudos y analizados.

### Prioridad 1: diseño y normalización del broker MQTT
- [x] Normalizar el tópico MQTT a una convención estándar sin barras dobles.
- [x] Ajustar los topics de producción, consumo y alertas en todos los servicios para mantener el diseño coherente.
- [x] Documentar la semántica QoS y la elección de `at-least-once` en la memoria.

### Prioridad 2: robustez operativa
- [x] Añadir observabilidad mínima: healthchecks básicos en Docker y validación real del pipeline.
- [x] Revisar estrategia de idempotencia en MongoDB para evitar duplicados entre reinicios.
- [x] Comprobar comportamiento ante mensajes duplicados o pérdida temporal de conexión mediante una validación real del flujo y la upsert por `id`.

### Prioridad 3: dashboard y demo
- [x] Añadir un flow de Node-RED exportable y versionado.
- [x] Validar que el dashboard recibe eventos analizados y alertas en tiempo real.
- [x] Preparar la demostración end-to-end para la presentación oral con arranque real y validación de mensajes en MongoDB.

### Prioridad 4: cierre académico y defensa
- [x] Redactar la memoria final con estructura del enunciado.
- [x] Preparar la presentación oral con estructura de diapositivas y notas de apoyo.
- [ ] Añadir pruebas de integración para MQTT y Mongo con contenedores efímeros si el tiempo lo permite.

## Riesgos técnicos

- El tópico `reddit//posts/raw` ya no se usa; la convención actual es estándar y consistente.
- El dashboard de Node-RED ya tiene un flow exportado y validado.
- Las pruebas actuales cubren la lógica pura y la validación real con Docker/MQTT/Mongo confirma el comportamiento end-to-end.

## Criterios de acabado

- La documentación debe permitir arrancar el proyecto sin leer el código.
- El código debe conservar sólo comentarios justificativos, no ruido explicativo.
- El entorno local debe vivir en `.venv`; nada global salvo Docker y Python base.