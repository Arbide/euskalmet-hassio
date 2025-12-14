# AGENTS.md

Este archivo proporciona instrucciones a asistentes de IA (como Claude Code) cuando trabajan con código en este repositorio.

## Descripción del Proyecto

**Euskalmet** es una integración personalizada de Home Assistant que proporciona datos meteorológicos de Euskalmet (Servicio Meteorológico Vasco). La integración usa autenticación JWT con claves privadas RSA para acceder a la API de Euskalmet y crea entidades de sensores para temperatura, humedad, viento, presión, precipitación, irradiancia solar, niveles de agua y caudales.

## Estructura del Código

### Archivos Principales (`custom_components/euskalmet/`)

- **`__init__.py`**: Punto de entrada de la integración. Gestiona setup y teardown de config entries, crea el coordinador y configura las plataformas de componentes.

- **`config_flow.py`**: Flujo de configuración basado en UI con dos pasos:
  1. Validación de credenciales (fingerprint + clave privada RSA en formato PEM)
  2. Selección de estación desde lista obtenida dinámicamente

- **`coordinator.py`**: DataUpdateCoordinator que gestiona la comunicación con la API:
  - Genera tokens JWT usando algoritmo RSA256
  - Cachea información de sensores de la estación en primera consulta
  - Obtiene lecturas actuales para cada tipo de sensor cada hora
  - Mapea estructura de API Euskalmet a tipos de sensores usando `SENSOR_MAPPINGS`

- **`sensor.py`**: Plataforma de sensores que crea entidades individuales para cada tipo de medición.

- **`const.py`**: Constantes incluyendo:
  - Configuración JWT (issuer, audience, algorithm)
  - Endpoints API y estructura de URL base
  - Definiciones de tipos de sensores con device classes y unidades
  - Intervalo de actualización (10 minutos)

### Sensores Disponibles

Configurados en `SENSOR_MAPPINGS` (coordinator.py):

| Sensor | measureType | measure |
|--------|-------------|---------|
| temperature | measuresForAir | temperature |
| humidity | measuresForAir | humidity |
| wind_speed | measuresForWind | mean_speed |
| wind_speed_max | measuresForWind | max_speed |
| wind_direction | measuresForWind | mean_direction |
| pressure | measuresForAtmosphere | pressure |
| precipitation | measuresForWater | precipitation |
| irradiance | measuresForSun | irradiance |
| sheet_level_1 | measuresForWater | sheet_level_1 |
| sheet_level_2 | measuresForWater | sheet_level_2 |
| sheet_level_3 | measuresForWater | sheet_level_3 |
| flow_1_computed | measuresForWater | flow_1_computed |
| flow_2_computed | measuresForWater | flow_2_computed |

### API Euskalmet

Base URL: `https://api.euskadi.eus/euskalmet/`

Endpoints utilizados:
- `GET /stations` - Lista todas las estaciones
- `GET /stations/{id}/current` - Obtiene detalles de estación y lista de sensores
- `GET /sensors/{id}` - Obtiene detalles del sensor y medidas disponibles
- `GET /readings/forStation/{station}/{sensor}/measures/{type}/{measure}/at/{year}/{month}/{day}/{hour}` - Obtiene lecturas horarias

### Flujo de Integración con API

1. **Autenticación**: Tokens JWT generados con RSA256 usando clave privada y fingerprint
2. **Descubrimiento de Estaciones**: Endpoint `/stations` consultado durante config flow
3. **Obtención de Datos**:
   - Primera consulta: Obtiene info de estación desde `/stations/{id}/current` (cachea lista de sensores)
   - Para cada sensor: Consulta detalles desde `/sensors/{id}` para descubrir medidas disponibles
   - Para cada medida: Consulta lectura desde `/readings/forStation/{station_id}/{sensor_id}/measures/{measureType}/{measureId}/at/{year}/{month}/{day}/{hour}`

### Autenticación JWT

Los tokens se generan con diferentes expiraciones según el contexto:
- **Config flow**: Tokens de 1 hora (solo para validación de credenciales)
- **Coordinator**: Tokens de 365 días (para operación normal de obtención de datos)

Estructura del token:
- `aud`: "met01.apikey"
- `iss`: "euskalmet-hassio"
- `loginId`: El fingerprint del usuario

## Reglas de Desarrollo

### 1. Al Hacer Cambios

**OBLIGATORIO**: Tras cada cambio solicitado por el usuario, actualiza `CHANGELOG.md`:

1. Añade una entrada en la sección correspondiente según el tipo de cambio:
   - **Añadido**: Nuevas funcionalidades
   - **Mejorado**: Mejoras en funcionalidades existentes
   - **Corregido**: Corrección de bugs
   - **Eliminado**: Funcionalidades eliminadas
   - **Técnico**: Cambios técnicos internos

2. Usa el formato del changelog (ver ejemplos en CHANGELOG.md):
   ```markdown
   ### Añadido
   - **Descripción breve en negrita** - Explicación detallada del cambio
   ```

3. Si es un cambio menor, agrúpalo con otros cambios similares
4. Si es un cambio mayor, considera crear una nueva versión

### 2. Añadir Nuevos Sensores

Para añadir un nuevo sensor:

1. **`const.py`**:
   - Añadir constante `SENSOR_NOMBRE = "nombre"`
   - Añadir definición completa en `SENSOR_TYPES` con device_class, unit, icon, precision
   - Importar unidades necesarias de `homeassistant.const`

2. **`coordinator.py`**:
   - Añadir mapeo en `SENSOR_MAPPINGS` con measureType y measure
   - Añadir campo en `processed_data` inicializado a `None`

3. **`sensor.py`**: No requiere cambios (es genérico)

4. **CHANGELOG.md**: Documentar el nuevo sensor añadido

### 3. Traducciones

Archivos en `translations/`: `en.json`, `es.json`, `eu.json`

Siempre actualizar los 3 idiomas cuando se añadan nuevos strings traducibles.

### 4. Actualizar Versión

Cuando se actualice la versión:
1. `manifest.json` - campo `version`
2. `hacs.json` - campo `version`
3. `README.md` - sección de versión
4. `CHANGELOG.md` - nueva sección `## [X.Y.Z] - YYYY-MM-DD`

### 5. Patrones Importantes

#### Manejo de Errores

- **Errores de autenticación (401/403)**: Lanzar `ConfigEntryAuthFailed` para activar flujo de re-autenticación
- **Errores de conexión**: Lanzar `UpdateFailed` que marca los sensores como no disponibles
- **Datos nulos**: El sensor establece `available = False`

#### Disponibilidad de Sensores

Los sensores establecen `available = False` cuando:
- La actualización del coordinador falla
- Los datos del coordinador son None
- El valor específico del sensor es None

Esto previene mostrar datos obsoletos o faltantes.

#### Logging

- `_LOGGER.debug()` - Detalles de depuración (meteoros disponibles, valores de sensores)
- `_LOGGER.info()` - Información general (inicialización, actualizaciones exitosas, resumen de sensores)
- `_LOGGER.warning()` - Problemas no críticos (datos faltantes, HTTP 404, valores nulos)
- `_LOGGER.error()` - Errores críticos (red, autenticación, siempre con `exc_info=True`)

#### Actualización de Datos

- **Intervalo**: 10 minutos (`UPDATE_INTERVAL` en const.py)
- **Creación dinámica**: Los sensores se crean solo si están disponibles en la estación
- **Caché**: Información de estación y sensores se cachea para reducir llamadas API
- **Desfase temporal**: Las lecturas se obtienen con 10 minutos de retraso para evitar errores 404 en transiciones horarias

### 6. Entorno de Desarrollo

#### Python Environment

El proyecto usa un entorno virtual Python en `.venv/`:

```bash
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

#### Testing

Para probar cambios:
1. Copiar `custom_components/euskalmet` a directorio `custom_components/` de Home Assistant
2. Usar scripts `deploy_to_ha.ps1` o `deploy_to_ha.bat` (ver DESARROLLO.md para configuración)
3. Reiniciar Home Assistant
4. Añadir integración via UI: Configuration > Devices & Services > Add Integration > Euskalmet
5. Verificar logs en Home Assistant para debugging

### 7. Dependencias

Especificadas en `manifest.json`:
- `aiohttp>=3.8.0` - Cliente HTTP asíncrono para peticiones API
- `PyJWT>=2.8.0` - Generación de tokens JWT
- `cryptography>=41.0.0` - Manejo de claves RSA

### 8. Internacionalización

La integración soporta traducciones en español y euskera en `translations/`:
- `es.json` - Español
- `eu.json` - Euskera

Las claves de traducción están definidas en `strings.json` y cubren pasos del config flow y mensajes de error.

### 9. Integración con HACS

Configurado via `hacs.json`:
- Renderiza README en interfaz HACS
- Dominio: sensor
- Clase IoT: Cloud Polling
- Versión mínima HA: 2024.1.0

## Notas Importantes

- **No crear sensores inexistentes**: Solo se crean sensores que la estación realmente proporciona
- **Formato PEM**: La clave privada debe estar en formato PEM completo con headers
- **Horarios UTC**: Usar `datetime.now(timezone.utc)` (no `datetime.utcnow()` que está deprecated)
- **Timeouts modernos**: Usar `aiohttp.ClientTimeout` (no `async_timeout` deprecated)
- **Type hints**: Mantener anotaciones de tipos completas (compatibilidad Python 3.11+)
- **Sensor genérico**: `sensor.py` es completamente genérico y no requiere cambios al añadir sensores

## Agentes
* Todos los documentos o tests creados por el agente se almacencarán en la carpeta `agent/`.º

## Resumen de Workflow

1. Usuario solicita cambio
2. Implementar cambio en archivos correspondientes
3. **Actualizar CHANGELOG.md** con descripción del cambio, pero sin incluir detalles técnicos ni información sobre documentacion generada
4. Actualizar README.md e info.md si es necesario tras un cambio
5. Si aplica, actualizar traducciones (3 idiomas)
6. Si es cambio mayor, considerar incremento de versión
7. Verificar que no se rompe funcionalidad existente

---

**Home Assistant mínimo**: 2024.1.0
**Python mínimo**: 3.11