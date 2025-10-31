# ATOgen

Generador y editor de Air Tasking Orders (ATO) construido con Streamlit. Este MVP permite crear, editar, duplicar y exportar ATOs siguiendo la estructura doctrinal estándar (Header → Allotment → Tasking Units → Support/Control → SPINS → Footer).

## Características principales

- Listado de ATOs almacenadas localmente en `data/atos.json`.
- Editor paso a paso para capturar todos los bloques doctrinales del ATO.
- Gestión de múltiples Task Units, recursos de Allotment y elementos de Support/Control.
- Persistencia local basada en JSON sin necesidad de servicios externos.
- Validación básica de campos obligatorios y formato doctrinal DDHHmmZMMMYYYY para el bloque TIMEFRAM.
- Exportación del ATO a texto tipo USMTF y descarga del JSON completo con un clic.
- Ejemplos incluidos (`example_ato.json` y `example_ato.txt`).

## Requisitos

- Python 3.10 o superior.

## Instalación y ejecución

1. Crear y activar un entorno virtual (opcional pero recomendado).

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # En Windows usar .venv\Scripts\activate
   ```

2. Instalar las dependencias.

   ```bash
   pip install -r requirements.txt
   ```

3. Iniciar la aplicación Streamlit.

   ```bash
   streamlit run streamlit_app.py
   ```

4. Abrir el navegador en la URL que indique Streamlit (por defecto http://localhost:8501).

## Estructura del proyecto

```
app/
├── exporter.py      # Lógica de exportación USMTF-like
├── models.py        # Modelos de datos y validaciones
├── storage.py       # Persistencia en JSON
streamlit_app.py     # Interfaz principal en Streamlit
example_ato.json     # ATO de ejemplo
example_ato.txt      # Exportación en texto del ejemplo
requirements.txt     # Dependencias del proyecto
```

## Persistencia

Los datos se almacenan en el archivo `data/atos.json`. Puede editarse o respaldarse manualmente. Si el archivo se elimina, la aplicación creará uno nuevo vacío al iniciar.

## Exportación

Cada ATO puede exportarse en dos formatos:

- **TXT**: estructura USMTF simplificada generada por `app/exporter.py`.
- **JSON**: representación completa del objeto ATO.

## Datos de ejemplo

Se incluye `example_ato.json` con una misión ficticia. Puede cargarse copiando su contenido en `data/atos.json` (como único elemento de la lista) o creándose manualmente desde la interfaz. El archivo `example_ato.txt` muestra el resultado de la exportación del mismo ATO.

## Licencia

Este proyecto se distribuye con fines demostrativos. Ajuste y extienda según sus necesidades operacionales.
