# Changelog - Euskalmet

Todos los cambios notables de este proyecto se documentarán en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [0.0.1] - 2025-12-06

### Añadido
- Lanzamiento inicial del componente **Euskalmet** para Home Assistant
- Integración completa con la API de Euskalmet mediante autenticación JWT
- Soporte para 8 sensores meteorológicos:
  - Temperatura (°C)
  - Humedad relativa (%)
  - Velocidad del viento (m/s)
  - Velocidad máxima del viento (m/s)
  - Dirección del viento (grados)
  - Presión atmosférica (hPa)
  - Precipitación acumulada (mm)
  - Irradiación solar (W/m²)
- Configuración mediante interfaz de usuario (UI Config Flow)
  - Paso 1: Introducir fingerprint y clave privada PEM
  - Paso 2: Seleccionar estación meteorológica desde lista desplegable
- Traducciones completas en:
  - Español (es)
  - Euskera (eu)
  - Inglés (en) - por defecto
- Autenticación JWT segura con:
  - Fingerprint como loginId
  - Clave privada RSA en formato PEM
  - Tokens con expiración de 1 año (regenerados automáticamente)
- Actualizaciones automáticas cada 10 minutos mediante DataUpdateCoordinator
- Soporte para instalación vía HACS
- Compatibilidad con Home Assistant 2024.1.0+
- Probado y verificado con Home Assistant 2025.11.3

### Técnico
- Uso de `aiohttp.ClientTimeout` para timeouts modernos (sin `async_timeout`)
- `datetime.now(timezone.utc)` en lugar de `datetime.utcnow()` (deprecated)
- Type hints completos para Python 3.11+
- Manejo robusto de errores con excepciones específicas de Home Assistant
- Logging detallado para debugging
- Mapeo inteligente de sensores a medidas de la API
- Caché de información de estaciones para reducir llamadas a la API

### Dependencias
- aiohttp >= 3.8.0
- PyJWT >= 2.8.0
- cryptography >= 41.0.0

### Documentación
- README.md completo con instrucciones de instalación y configuración
- info.md para HACS
- CAMBIOS_COMPATIBILIDAD.md con detalles técnicos
- Ejemplos de uso en automatizaciones
- Guía de solución de problemas

### Notas
- Esta es una versión beta inicial
- Los nombres de las medidas (measureType/measureId) pueden necesitar ajustes según las estaciones
- No todas las estaciones tienen todos los sensores disponibles

[0.0.1]: https://github.com/YOUR_USERNAME/euskalmet-hassio/releases/tag/v0.0.1
