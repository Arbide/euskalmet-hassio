# Changelog - Euskalmet

Todos los cambios notables de este proyecto se documentarán en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [0.0.3] - 2025-12-07

### Añadido
- **Sistema de logging mejorado** para diagnóstico de problemas de lectura de datos
  - Logs de nivel WARNING cuando la API retorna errores HTTP o valores nulos
  - Logs de nivel ERROR para errores de red con detalles completos
  - Logs informativos al inicializar estaciones (nombre y número de sensores)
  - Resumen al final de cada actualización indicando sensores exitosos y fallidos
  - Stack traces completos para errores inesperados
- **SCAN_INTERVAL** añadido a constantes (`const.py`) para claridad
- **Descripciones de ayuda** (`data_description`) en flujo de configuración para el campo de clave privada
  - Español: Instrucciones detalladas sobre formato PEM
  - Euskera: Instrucciones traducidas
  - Inglés: Instrucciones en inglés
- **Logo de Euskalmet** añadido a la cabecera del README.md con diseño centrado
- **Aviso sobre desarrollo experimental con IA** al final del README

### Mejorado
- **Lista de estaciones completa** en configuración
  - Eliminado límite de 50 estaciones
  - Ahora se muestran TODAS las estaciones disponibles
  - Optimización: se muestran IDs inicialmente para evitar peticiones HTTP masivas
  - El nombre real se obtiene solo cuando se selecciona una estación
- **Campo de clave privada más grande** en el flujo de configuración
  - Cambiado a área de texto multilínea sin restricciones de tipo
  - Mejor experiencia de usuario al pegar claves PEM largas
- **Precisión de visualización ajustada** para todos los sensores:
  - Humedad: 0 decimales (antes: sin definir)
  - Precipitación: 1 decimal (antes: sin definir)
  - Presión: 1 decimal (antes: sin definir)
  - Dirección del viento: 0 decimales (antes: sin definir)
  - Velocidad del viento: 1 decimal (antes: sin definir)
  - Velocidad máxima del viento: 1 decimal (antes: sin definir)
  - Temperatura: 1 decimal (antes: sin definir)
  - Irradiancia solar: 0 decimales (antes: sin definir)
- **README.md reorganizado**:
  - Registro de cambios movido a referencia a CHANGELOG.md
  - Estructura más limpia y mantenible
  - Diseño visual mejorado con logo centrado

### Corregido
- **Configuración de HACS** - Eliminada referencia a `"filename": "logo.png"`
  - Los iconos locales no funcionan en HACS/Home Assistant
  - Para iconos oficiales se requiere PR al repositorio home-assistant/brands
  - El logo permanece en README.md para visualización en GitHub

### Eliminado
- Importación innecesaria de `TextSelectorType` en `config_flow.py`
- Línea `"filename": "logo.png"` de `hacs.json`

### Técnico
- Manejo de errores mejorado en `coordinator.py`:
  - `_fetch_station_info()`: Manejo de errores de red con logs detallados
  - `_fetch_sensor_details()`: Distinción entre errores de red y otros errores
  - `_fetch_reading()`: Tres tipos de errores diferenciados (HTTP, red, inesperados)
  - `_async_update_data()`: Resumen estadístico de sensores exitosos vs fallidos
- Logs informativos al inicializar coordinador con intervalo de actualización configurado

## [0.0.2] - 2025-12-06

### Añadido
- **Sensor de velocidad máxima del viento** (Wind Speed Max)
  - measureType: `measuresForWind`
  - measureId: `max_speed`
  - Unidad: m/s
- **Sensor de irradiación solar** (Solar Irradiance)
  - measureType: `measuresForSun`
  - measureId: `irradiance`
  - Unidad: W/m²
- Archivo `logo.png` en la raíz del repositorio para HACS
- Configuración `"filename": "logo.png"` en `hacs.json`
- Documentación `MOSTRAR_ICONO.md` con instrucciones para visualizar el icono

### Corregido
- **SENSOR_MAPPINGS corregidos** - Los sensores ahora usan los valores correctos de la API:
  - Temperatura: `measuresForAir/temperature` (era `measuresForAmbient/temp`)
  - Humedad: `measuresForAir/humidity` (era `measuresForAmbient/hum`)
  - Presión: `measuresForAtmosphere/pressure` (era `measuresForPressure/pressure`)
  - Precipitación: `measuresForWater/precipitation` (era `measuresForRain/rain_acc`)
- Configuración de iconos para que aparezcan correctamente en HACS

### Mejorado
- Logging detallado con nivel DEBUG para diagnosticar problemas con sensores
- Total de **8 sensores meteorológicos** disponibles (era 6 en la versión anterior)

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

[0.0.3]: https://github.com/YOUR_USERNAME/euskalmet-hassio/releases/tag/v0.0.3
[0.0.2]: https://github.com/YOUR_USERNAME/euskalmet-hassio/releases/tag/v0.0.2
[0.0.1]: https://github.com/YOUR_USERNAME/euskalmet-hassio/releases/tag/v0.0.1
