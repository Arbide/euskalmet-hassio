# Euskalmet - Integración para Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
![Version](https://img.shields.io/badge/version-0.0.1-blue.svg)
![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024.1.0%2B-green.svg)

Integración personalizada **Euskalmet** para Home Assistant que permite integrar datos meteorológicos de Euskalmet (Servicio Vasco de Meteorología).

**Versión actual:** 0.0.1 (Beta)

## Características

- Datos meteorológicos en tiempo real de las estaciones de Euskalmet
- Soporte para múltiples sensores meteorológicos:
  - Temperatura (°C)
  - Humedad (%)
  - Velocidad del viento (m/s)
  - Dirección del viento (grados)
  - Presión atmosférica (hPa)
  - Precipitación (mm)
- Configuración sencilla a través de la interfaz de Home Assistant
- Actualizaciones automáticas cada 10 minutos
- Soporte para idiomas español y euskera

## Instalación

### HACS (Recomendado)

1. Abre HACS en tu instancia de Home Assistant
2. Haz clic en "Integraciones"
3. Haz clic en los tres puntos en la esquina superior derecha
4. Selecciona "Repositorios personalizados"
5. Añade la URL de este repositorio: `https://github.com/YOUR_USERNAME/euskalmet-hassio`
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
4. Introduce tu **Fingerprint**
5. Pega el contenido completo de tu **clave privada PEM** (incluyendo las líneas `-----BEGIN RSA PRIVATE KEY-----` y `-----END RSA PRIVATE KEY-----`)
6. Selecciona tu estación meteorológica preferida de la lista desplegable
7. Haz clic en **Enviar**

La integración creará sensores para todas las mediciones meteorológicas disponibles de la estación seleccionada.

**Seguridad**: La clave privada se almacena de forma segura en Home Assistant y solo se usa para generar tokens JWT de autenticación.

## Sensores

La integración crea los siguientes sensores para cada estación configurada:

| Sensor | Descripción | Unidad |
|--------|-------------|--------|
| Temperature | Temperatura actual | °C |
| Humidity | Humedad relativa | % |
| Wind Speed | Velocidad del viento | m/s |
| Wind Direction | Dirección del viento | grados |
| Pressure | Presión atmosférica | hPa |
| Precipitation | Precipitación acumulada | mm |

Cada sensor incluye atributos adicionales:
- `station_id`: ID de la estación meteorológica
- `station_name`: Nombre de la estación meteorológica
- `last_update`: Marca de tiempo de la última actualización de datos

## Ejemplo de Uso

Una vez configurada, puedes usar los sensores en automatizaciones, scripts y paneles:

```yaml
# Ejemplo de automatización
automation:
  - alias: "Alerta de Lluvia"
    trigger:
      - platform: numeric_state
        entity_id: sensor.euskalmet_STATION_ID_precipitation
        above: 5
    action:
      - service: notify.mobile_app
        data:
          message: "¡Está lloviendo! Precipitación: {{ states('sensor.euskalmet_STATION_ID_precipitation') }} mm"
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

### Versión 0.0.1 (Versión inicial - Beta)
- Lanzamiento inicial en versión beta
- Soporte para 6 sensores meteorológicos:
  - Temperatura (°C)
  - Humedad (%)
  - Velocidad del viento (m/s)
  - Dirección del viento (grados)
  - Presión atmosférica (hPa)
  - Precipitación acumulada (mm)
- Configuración basada en interfaz de usuario (UI)
- Autenticación JWT con fingerprint y clave privada PEM
- Traducciones completas en español y euskera
- Compatible con Home Assistant 2024.1.0+ (probado con 2025.11.3)
- Actualizaciones automáticas cada 10 minutos
- Soporte para instalación vía HACS
