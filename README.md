# 🔥 Aplicación de Incendios Forestales

Esta aplicación está diseñada para calcular la susceptibilidad y amenaza de incendios forestales utilizando datos geoespaciales. Utiliza la metodología del Protocolo para la realización de mapas de zonificación de riesgos a incendios de cobertura vegetal, escala 1:100.000 del Ministerio de Ambiente y Desarrollo Sostenible junto con el IDEAM.

## ✨ Características

- 📊 **Cálculo de Susceptibilidad**: Basado en parámetros de vegetación.
- 🗺️ **Cálculo de Amenaza**: Integra múltiples variables como precipitación, temperatura, pendiente, accesibilidad, frecuencia de incendios, vientos y radiación solar.
- 📈 **Visualización Interactiva**: Mapas generados con Plotly para visualizar los niveles de susceptibilidad y amenaza.
- 💾 **Descarga de Resultados**: Posibilidad de descargar los mapas de susceptibilidad y amenaza en formato raster.

## 🛠️ Requisitos

- Python 3.x
- Bibliotecas principales:
  - 🎯 Dash
  - 🎨 Dash Bootstrap Components
  - 📊 Plotly
  - 🗺️ Geopandas
  - 📷 Rasterio
  - 🔢 Numpy

## ⚙️ Instalación

1. Clona este repositorio:
   ```bash
   git clone https://github.com/hperezc/forest-fire-risk-analysis.git
   ```
2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 Uso

1. Ejecuta la aplicación:
   ```bash
   python app/app_Vdom.py
   ```
2. Abre tu navegador y ve a `http://127.0.0.1:8050` para interactuar con la aplicación.

## 📁 Datos de Ejemplo

Incluye una carpeta con datos de ejemplo en formato shapefile para probar la aplicación. Asegúrate de ajustar las rutas de los archivos en la interfaz de usuario.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue o envía un pull request para mejoras o correcciones.

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo `LICENSE` para más detalles.

---

# 🔥 Wildfire Application

This application is designed to calculate wildfire susceptibility and threat using geospatial data. It employs the methodology of the Protocol for creating risk zoning maps for vegetation cover fires, scale 1:100,000, from the Ministry of Environment and Sustainable Development along with IDEAM.

## ✨ Features

- 📊 **Susceptibility Calculation**: Based on vegetation parameters.
- 🗺️ **Threat Calculation**: Integrates multiple variables such as precipitation, temperature, slope, accessibility, fire frequency, winds, and solar radiation.
- 📈 **Interactive Visualization**: Maps generated with Plotly to visualize susceptibility and threat levels.
- 💾 **Results Download**: Ability to download susceptibility and threat maps in raster format.

## 🛠️ Requirements

- Python 3.x
- Main libraries:
  - 🎯 Dash
  - 🎨 Dash Bootstrap Components
  - 📊 Plotly
  - 🗺️ Geopandas
  - 📷 Rasterio
  - 🔢 Numpy

## ⚙️ Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/hperezc/forest-fire-risk-analysis.git
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 Usage

1. Run the application:
   ```bash
   python app/app_Vdom.py
   ```
2. Open your browser and go to `http://127.0.0.1:8050` to interact with the application.

## 📁 Example Data

Includes a folder with example data in shapefile format to test the application. Make sure to adjust the file paths in the user interface.

## 🤝 Contributions

Contributions are welcome. Please open an issue or submit a pull request for improvements or fixes.

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for more details.
