# Euskalmet - Integración para Home Assistant

**Versión:** 0.1.0

**Euskalmet** te permite monitorizar datos meteorológicos de las estaciones de Euskalmet (Servicio Vasco de Meteorología) directamente en Home Assistant.

## Qué obtienes

### Entidad Weather (Pronóstico)
- Pronósticos meteorológicos para 236+ ubicaciones del País Vasco
- Pronóstico diario con temperaturas máximas/mínimas, condiciones, precipitación y viento
- Pronóstico horario con datos detallados
- Condiciones meteorológicas actuales
- Actualización automática cada 30 minutos
- Configuración independiente por ubicación

### Sensores de Estaciones Meteorológicas
- **Hasta 21 sensores diferentes** según disponibilidad de cada estación:
  - Temperatura, humedad, presión atmosférica
  - Velocidad del viento (media y máxima) con desviación estándar (sigma)
  - Dirección del viento con desviación estándar (sigma)
  - Precipitación
  - Irradiación solar
  - Niveles de agua (3 sensores)
  - Caudal (2 sensores)
  - Oleaje: altura máxima, altura significativa, periodo y periodo pico (4 sensores)
- Actualizaciones automáticas cada 10 minutos
- Solo se crean sensores disponibles en cada estación

### Características Generales
- Soporte completo para español, euskera e inglés
- Configuración sencilla mediante interfaz gráfica
- Selección jerárquica de ubicaciones (región/zona/ubicación)
- Reutilización automática de credenciales
- Múltiples configuraciones simultáneas (estaciones + ubicaciones)

## Requisitos

Necesitas credenciales de autenticación de Euskalmet (fingerprint y clave privada PEM) para usar esta integración. Visita [Euskalmet Open Data](https://opendata.euskadi.eus/api-euskalmet/) para solicitarlas.

## Configuración

1. Añade la integración a través de la interfaz de Home Assistant
2. Selecciona entre:
   - **Configurar Estación Meteorológica** (sensores en tiempo real)
   - **Configurar Pronóstico del Tiempo** (entidad weather)
3. Introduce tu fingerprint de Euskalmet (si es la primera configuración)
4. Pega tu clave privada en formato PEM (si es la primera configuración)
5. Selecciona tu estación meteorológica o ubicación de pronóstico
6. ¡Disfruta de tus datos meteorológicos!

## Más Información

Para documentación detallada, solución de problemas y ejemplos, por favor visita el [repositorio de GitHub](https://github.com/Arbide/euskalmet-hassio).
