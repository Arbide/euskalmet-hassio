![imagen](assets/logo.png)

# Euskalmet - Integración para Home Assistant

[![HACS Supported](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)
![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024.1.0%2B-green.svg)

**Integración personalizada para Home Assistant que permite integrar datos meteorológicos de Euskalmet (Servicio Vasco de Meteorología)**

**Versión actual:** 0.1.0

## Características

### Entidad Weather (Pronóstico Meteorológico)
- **Pronósticos meteorológicos** para más de 236 ubicaciones del País Vasco
- **Pronóstico diario**: temperaturas máximas/mínimas, condiciones, precipitación y viento
- **Pronóstico horario**: datos detallados de temperatura, viento, precipitación y humedad
- **Condiciones actuales** desde la API de pronóstico
- Actualización automática cada 30 minutos
- Configuración independiente por ubicación (no vinculada a estaciones)
- Mapeo de 25 códigos de condiciones meteorológicas de Euskalmet a estándares de Home Assistant

### Sensores de Estaciones Meteorológicas
- **Datos en tiempo real** de las estaciones de Euskalmet
- **Hasta 21 sensores diferentes** (según disponibilidad de cada estación):

  **Atmosféricos:**
  - Temperatura (°C)
  - Humedad (%)
  - Presión atmosférica (hPa)
  - Precipitación (mm)
  - Irradiación solar (W/m²)

  **Viento:**
  - Velocidad del viento media (m/s)
  - Velocidad máxima del viento (m/s)
  - Dirección del viento (grados)
  - Desviación estándar de velocidad - Sigma (km/h)
  - Desviación estándar de dirección - Sigma (grados)

  **Hidrología:**
  - Nivel de agua 1, 2 y 3 (m)
  - Caudal 1 y 2 (m³/s)

  **Oleaje (estaciones costeras):**
  - Altura máxima de ola (m)
  - Altura significativa de ola (m)
  - Periodo de ola (s)
  - Periodo pico de ola (s)

- Solo se crean los sensores que realmente existen en cada estación
- Actualizaciones automáticas cada 10 minutos

### Configuración y Usabilidad
- Configuración sencilla mediante interfaz gráfica
- Menú inicial para elegir entre estación meteorológica o pronóstico del tiempo
- Selección jerárquica de ubicaciones (región → zona → ubicación)
- Reutilización automática de credenciales entre configuraciones
- Soporte para múltiples estaciones y ubicaciones simultáneamente
- Traducciones completas en español, euskera e inglés

## Instalación

### HACS (Recomendado)

1. Abre HACS en tu instancia de Home Assistant
2. Haz clic en "Integraciones"
3. Haz clic en los tres puntos en la esquina superior derecha
4. Selecciona "Repositorios personalizados"
5. Añade la URL de este repositorio: `https://github.com/Arbide/euskalmet-hassio`
6. Selecciona la categoría "Integration"
7. Haz clic en "Añadir"
8. Busca "Euskalmet" en HACS
9. Haz clic en "Descargar"
10. Reinicia Home Assistant

### Instalación Manual

1. Copia el directorio `custom_components/euskalmet` al directorio `custom_components` de tu Home Assistant
2. Reinicia Home Assistant

## Configuración

### Obtener Credenciales de API

Para usar esta integración, necesitas credenciales de autenticación de Euskalmet:

1. Visita el portal de Open Data de Euskalmet: [https://opendata.euskadi.eus/api-euskalmet/](https://opendata.euskadi.eus/api-euskalmet/)
2. Regístrate para obtener una cuenta si no la tienes
3. Navega a la sección de API y solicita acceso
4. Una vez aprobada tu solicitud, recibirás:
   - **Fingerprint**: Tu identificador único
   - **Clave Privada (Private Key)**: Un archivo en formato PEM

**Nota**: El proceso de aprobación puede tardar algún tiempo. Guarda la clave privada en un lugar seguro.

### Configurar la Integración

1. En Home Assistant, ve a **Configuración** > **Dispositivos y Servicios**
2. Haz clic en **Añadir Integración**
3. Busca **Euskalmet**
4. **Selecciona el tipo de configuración:**
   - **Configurar Estación Meteorológica**: Para obtener sensores en tiempo real de una estación
   - **Configurar Pronóstico del Tiempo**: Para obtener pronósticos meteorológicos de una ubicación

#### Opción 1: Configurar Estación Meteorológica
5. Introduce tu **Fingerprint** (solo la primera vez)
6. Pega el contenido completo de tu **clave privada PEM** (solo la primera vez)
7. Selecciona tu estación meteorológica preferida de la lista
8. La integración creará automáticamente los sensores disponibles para esa estación

#### Opción 2: Configurar Pronóstico del Tiempo
5. Introduce tu **Fingerprint** (solo la primera vez, si no tienes estaciones configuradas)
6. Pega el contenido completo de tu **clave privada PEM** (solo la primera vez)
7. Selecciona la **región** (actualmente solo País Vasco)
8. Selecciona la **zona** dentro de la región
9. Selecciona la **ubicación** específica
10. Se creará una entidad weather con pronósticos diarios y horarios

**Nota**: Si ya tienes configurada una estación o ubicación, las credenciales se reutilizarán automáticamente al añadir nuevas.

**Seguridad**: La clave privada se almacena de forma segura en Home Assistant y solo se usa para generar tokens JWT de autenticación.

## Sensores y Entidades

### Entidad Weather

Cada ubicación de pronóstico configurada crea una entidad `weather.euskalmet_<ubicación>` con:
- **Condición actual**: Estado meteorológico actual (sunny, cloudy, rainy, etc.)
- **Temperatura actual**: Temperatura en tiempo real
- **Pronóstico diario**: Hasta 7 días con temperatura máx/mín, precipitación, viento
- **Pronóstico horario**: Datos detallados cada hora
- **Atributos**: Humedad, presión, viento, visibilidad

### Sensores de Estación

La integración crea los siguientes sensores para cada estación configurada (según disponibilidad):

| Categoría | Sensor | Descripción | Unidad |
|-----------|--------|-------------|--------|
| **Atmosféricos** | Temperature | Temperatura actual | °C |
| | Humidity | Humedad relativa | % |
| | Pressure | Presión atmosférica | hPa |
| | Precipitation | Precipitación acumulada | mm |
| | Solar Irradiance | Irradiación solar | W/m² |
| **Viento** | Wind Speed | Velocidad media del viento | m/s |
| | Wind Speed Max | Velocidad máxima del viento | m/s |
| | Wind Direction | Dirección del viento | grados |
| | Wind Speed Sigma | Desviación estándar velocidad | km/h |
| | Wind Direction Sigma | Desviación estándar dirección | grados |
| **Hidrología** | Water Level 1 | Nivel de agua 1 | m |
| | Water Level 2 | Nivel de agua 2 | m |
| | Water Level 3 | Nivel de agua 3 | m |
| | Flow Rate 1 | Caudal 1 | m³/s |
| | Flow Rate 2 | Caudal 2 | m³/s |
| **Oleaje** | Max Wave Height | Altura máxima de ola | m |
| | Significant Wave Height | Altura significativa de ola | m |
| | Wave Period | Periodo de ola | s |
| | Wave Peak Period | Periodo pico de ola | s |

**Importante**: No todas las estaciones tienen todos los sensores. La integración detecta automáticamente qué sensores están disponibles y solo crea las entidades correspondientes.

Cada sensor incluye atributos adicionales:
- `station_id`: ID de la estación meteorológica
- `station_name`: Nombre de la estación meteorológica
- `last_update`: Marca de tiempo de la última actualización de datos

## Ejemplo de Uso

Una vez configurada, puedes usar las entidades weather y sensores en automatizaciones, scripts y paneles:

### Usando la Entidad Weather

```yaml
# Tarjeta Weather en Lovelace
type: weather-forecast
entity: weather.euskalmet_bilbao
show_forecast: true

# Automatización basada en pronóstico
automation:
  - alias: "Alerta de Lluvia Mañana"
    trigger:
      - platform: state
        entity_id: weather.euskalmet_bilbao
        to: 'rainy'
    action:
      - service: notify.mobile_app
        data:
          message: "Se espera lluvia. No olvides el paraguas!"
```

### Usando Sensores de Estación

```yaml
# Ejemplo de automatización con sensores
automation:
  - alias: "Alerta de Lluvia Intensa"
    trigger:
      - platform: numeric_state
        entity_id: sensor.euskalmet_STATION_ID_precipitation
        above: 5
    action:
      - service: notify.mobile_app
        data:
          message: "¡Está lloviendo intensamente! Precipitación: {{ states('sensor.euskalmet_STATION_ID_precipitation') }} mm"

  - alias: "Alerta de Viento Fuerte"
    trigger:
      - platform: numeric_state
        entity_id: sensor.euskalmet_STATION_ID_wind_speed_max
        above: 20
    action:
      - service: notify.mobile_app
        data:
          message: "¡Viento fuerte detectado! Velocidad máxima: {{ states('sensor.euskalmet_STATION_ID_wind_speed_max') }} m/s"

  - alias: "Alerta de Olas Grandes"
    trigger:
      - platform: numeric_state
        entity_id: sensor.euskalmet_STATION_ID_max_wave_height
        above: 3
    action:
      - service: notify.mobile_app
        data:
          message: "¡Olas grandes! Altura máxima: {{ states('sensor.euskalmet_STATION_ID_max_wave_height') }} m"
```

## Solución de Problemas

### La integración no aparece

- Asegúrate de haber reiniciado Home Assistant después de la instalación
- Revisa los logs de Home Assistant en busca de errores

### Error de conexión

- Verifica que tu fingerprint sea correcto
- Asegúrate de haber pegado la clave privada completa (incluyendo las líneas BEGIN y END)
- Comprueba tu conexión a Internet
- Asegúrate de que la API de Euskalmet sea accesible

### Error de autenticación inválida

- Verifica que el fingerprint coincida con el de tu cuenta
- Asegúrate de que la clave privada esté en formato PEM correcto
- Comprueba que la clave privada corresponda a tu cuenta de Euskalmet
- La clave debe incluir `-----BEGIN RSA PRIVATE KEY-----` al inicio y `-----END RSA PRIVATE KEY-----` al final

### No hay datos de los sensores

- Verifica que la estación seleccionada esté activa
- Comprueba que tus credenciales tengan los permisos adecuados
- Revisa los logs de Home Assistant para mensajes de error detallados

## Soporte

Para problemas, preguntas o solicitudes de funcionalidades, por favor abre un issue en GitHub.

## Contribuciones

¡Las contribuciones son bienvenidas! No dudes en enviar un Pull Request.

## Licencia

Este proyecto está licenciado bajo la Licencia MIT.

## Aviso Legal

Esta es una integración no oficial. No está afiliada ni respaldada por Euskalmet o el Gobierno Vasco.

## Créditos

- Datos meteorológicos proporcionados por [Euskalmet](https://www.euskalmet.euskadi.eus/)
- Integración inspirada en [AEMET OpenData](https://github.com/home-assistant/core/tree/dev/homeassistant/components/aemet)

## Registro de Cambios

Para ver el historial completo de cambios y versiones, consulta el archivo [CHANGELOG.md](CHANGELOG.md).

---

## ⚠️ Aviso Importante - Desarrollo Experimental con IA

Esta integración ha sido desarrollada **casi completamente mediante Inteligencia Artificial** como experimento tecnológico.

**Por favor, ten en cuenta:**

- ❌ **No hay garantía de la calidad del código**
- ❌ **No se asegura mantenimiento continuo**
- ❌ **No se garantiza corrección de errores**
- ❌ **El proyecto puede quedar abandonado en cualquier momento**

**Usa esta integración bajo tu propio riesgo.** Se recomienda revisarla y probarla exhaustivamente antes de usarla en entornos de producción.

Si encuentras problemas o deseas mejorar la integración, las contribuciones mediante Pull Requests son bienvenidas.
