import dash
from dash import dcc, html, Input, Output, State, callback_context
import base64
import io
import dash_bootstrap_components as dbc
import plotly.express as px
import geopandas as gpd
import rasterio
from rasterio.features import rasterize
from rasterio.mask import mask
import numpy as np
import os
from rasterio.crs import CRS
from rasterio.enums import Resampling
from rasterio.windows import Window
from rasterio.warp import calculate_default_transform, reproject
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importar las funciones necesarias del script original
from modelo_Vdom import asignar_parametros, vector_a_raster, mapeo_nombres_a_codigos, calificar_variable, calificar_y_rasterizar

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    html.H1("Cálculo de Susceptibilidad y Amenaza por Incendios Forestales", className="text-center my-4"),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Datos de entrada", className="card-title"),
                    dbc.Input(id='ruta-cobertura', type='text', placeholder='Ruta al archivo de coberturas', className="mb-2"),
                    html.Small("Asegurese de que los datos de entrada esten con los dominios del modelo geográfico del ANLA.", className="text-muted mb-3 d-block"),
                    dbc.Input(id='campo-cobertura', type='text', placeholder='Nombre del campo de tipo de cobertura', className="mb-2"),
                    html.Small("Especifique el nombre del campo que contiene los tipos de cobertura en el shapefile (generalmente N3_COBERT).", className="text-muted mb-3 d-block"),
                    dbc.Button('Calcular Susceptibilidad', id='calcular-susceptibilidad-button', color="primary", className="mb-3"),
                    dbc.Input(id='ruta-rasters-amenaza', type='text', placeholder='Ruta a la carpeta con shapefiles de amenaza', className="mb-2"),
                    html.Small("Ingrese la ruta a la carpeta que contiene los shapefiles de las variables de amenaza, reclasificados segun la metodología.", className="text-muted mb-3 d-block"),
                    html.H5("Ajuste de pesos", className="mt-3"),
                    dbc.InputGroup([
                        dbc.InputGroupText("Susceptibilidad"),
                        dbc.Input(id='peso-susceptibilidad', type='number', value=0.17, min=0, max=1, step=0.01)
                    ], className="mb-2"),
                    dbc.InputGroup([
                        dbc.InputGroupText("Precipitación"),
                        dbc.Input(id='peso-precipitacion', type='number', value=0.20, min=0, max=1, step=0.01)
                    ], className="mb-2"),
                    dbc.InputGroup([
                        dbc.InputGroupText("Temperatura"),
                        dbc.Input(id='peso-temperatura', type='number', value=0.20, min=0, max=1, step=0.01)
                    ], className="mb-2"),
                    dbc.InputGroup([
                        dbc.InputGroupText("Pendiente"),
                        dbc.Input(id='peso-pendiente', type='number', value=0.07, min=0, max=1, step=0.01)
                    ], className="mb-2"),
                    dbc.InputGroup([
                        dbc.InputGroupText("Accesibilidad"),
                        dbc.Input(id='peso-accesibilidad', type='number', value=0.20, min=0, max=1, step=0.01)
                    ], className="mb-2"),
                    dbc.InputGroup([
                        dbc.InputGroupText("Frecuencia"),
                        dbc.Input(id='peso-frecuencia', type='number', value=0.10, min=0, max=1, step=0.01)
                    ], className="mb-2"),
                    dbc.InputGroup([
                        dbc.InputGroupText("Vientos"),
                        dbc.Input(id='peso-vientos', type='number', value=0.10, min=0, max=1, step=0.01)
                    ], className="mb-2"),
                    dbc.InputGroup([
                        dbc.InputGroupText("Radiación Solar"),
                        dbc.Input(id='peso-radiacion-solar', type='number', value=0.07, min=0, max=1, step=0.01)
                    ], className="mb-2"),
                    dbc.Button('Calcular Amenaza', id='calcular-amenaza-button', color="success", className="mt-3"),
                    html.Div(id='log-calculo', className="mt-3")
                ])
            ], className="mb-4"),
            dbc.Card([
                dbc.CardBody([
                    html.P("Este software utiliza la metodología del Protocolo para la realización de mapas de zonificación de riesgos a incendios de cobertura vegetal, escala 1:100.000 del Ministerio de Ambiente y Desarrollo Sostenible junto con el IDEAM.", className="small")
                ])
            ])
        ], md=3),
        dbc.Col([
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id='mapa-susceptibilidad', style={'height': '70vh'})
                ], md=6),
                dbc.Col([
                    dcc.Graph(id='mapa-amenaza', style={'height': '70vh'})
                ], md=6)
            ]),
            dbc.Row([
                dbc.Col([
                    html.Div(id='leyenda-susceptibilidad')
                ], md=6),
                dbc.Col([
                    html.Div(id='leyenda-amenaza')
                ], md=6)
            ], className="mt-3"),
            dbc.Row([
                dbc.Col([
                    html.Button("Descargar Raster de Susceptibilidad", id="btn-descargar-susceptibilidad", className="mt-3")
                ], md=6),
                dbc.Col([
                    html.Button("Descargar Raster de Amenaza", id="btn-descargar-amenaza", className="mt-3")
                ], md=6)
            ]),
            dcc.Download(id="descargar-susceptibilidad"),
            dcc.Download(id="descargar-amenaza")
        ], md=9)
    ]),
    html.Footer([
        html.Hr(),  # Línea horizontal para separar el contenido del pie de página
        html.P([
            "Software creado por Hector Camilo Pérez Contreras (2024), ",
            html.A("analista4.grd@crantioquia.org.co", href="mailto:analista4.grd@crantioquia.org.co"),
            ". Todos los derechos reservados."
        ], className="text-center text-muted")
    ], className="mt-4")
], fluid=True)  # Usa fluid=True para un contenedor de ancho completo

def crear_leyenda(titulo, labels):
    return html.Div([
        html.H6(titulo, className="mt-2"),
        html.Div([
            html.Span(label, style={
                "backgroundColor": color,
                "color": "white" if color in ["green", "red", "darkred"] else "black",
                "padding": "5px",
                "marginRight": "10px",
                "borderRadius": "3px",
                "display": "inline-block",
                "minWidth": "60px",
                "textAlign": "center"
            }) for label, color in labels
        ], style={"display": "flex", "justifyContent": "space-between", "flexWrap": "wrap"})
    ])

@app.callback(
    [Output('mapa-susceptibilidad', 'figure'),
     Output('leyenda-susceptibilidad', 'children')],
    [Input('calcular-susceptibilidad-button', 'n_clicks')],
    [State('ruta-cobertura', 'value'),
     State('campo-cobertura', 'value')]
)
def calcular_y_mostrar_susceptibilidad(n_clicks, ruta_cobertura, campo_cobertura):
    if n_clicks == 0 or not ruta_cobertura or not campo_cobertura:
        return dash.no_update, dash.no_update
    
    logger.info("Iniciando cálculo de susceptibilidad")
    
    # Cargar el archivo shapefile de vegetación
    vegetacion = gpd.read_file(ruta_cobertura)
    
    # Crear la carpeta de resultados si no existe
    ruta_base = os.path.dirname(ruta_cobertura)
    ruta_resultados = os.path.join(ruta_base, 'resultados')
    os.makedirs(ruta_resultados, exist_ok=True)

    # Definir el tamaño del píxel deseado (en unidades del CRS del shapefile)
    tamano_pixel = 2  

    # Aplicar la función a cada fila del GeoDataFrame
    vegetacion['parametros'] = vegetacion[campo_cobertura].apply(asignar_parametros)

    # Extraer los valores de calificación de los parámetros
    vegetacion['calific_tipoCombus'] = vegetacion['parametros'].apply(lambda x: x.get('calific_tipoCombus', 0))
    vegetacion['calific_tiempoCombus'] = vegetacion['parametros'].apply(lambda x: x.get('calific_tiempoCombus', 0))
    vegetacion['calific_carga'] = vegetacion['parametros'].apply(lambda x: x.get('calific_carga', 0))

    # Calcular la susceptibilidad como el promedio de las tres variables
    vegetacion['susceptibilidad'] = (
        (vegetacion['calific_tipoCombus'] + 
         vegetacion['calific_tiempoCombus'] + 
         vegetacion['calific_carga']) / 3
    )

    # Convertir la columna de susceptibilidad a raster
    raster_salida = os.path.join(ruta_resultados, 'susceptibilidad.tif')
    vector_a_raster(vegetacion, 'susceptibilidad', raster_salida, tamano_pixel)

    # Cargar el raster de susceptibilidad
    with rasterio.open(raster_salida) as src:
        susceptibilidad_data = src.read(1)

    # Reclasificar la susceptibilidad
    def reclasificar_susceptibilidad(valor):
        if valor == 0:
            return 0  # Sin riesgo
        elif valor <= 1:
            return 1  # Muy baja
        elif valor <= 2:
            return 2  # Baja
        elif valor <= 3:
            return 3  # Moderada
        elif valor <= 4:
            return 4  # Alta
        else:
            return 5  # Muy alta

    susceptibilidad_reclasificada = np.vectorize(reclasificar_susceptibilidad)(susceptibilidad_data)

    # Crear mapa con Plotly
    fig_susceptibilidad = px.imshow(susceptibilidad_reclasificada,
                                    color_continuous_scale=[
                                        (0, "white"),     # Sin riesgo
                                        (0.2, "green"),   # Muy baja
                                        (0.4, "yellow"),  # Baja
                                        (0.6, "orange"),  # Moderada
                                        (0.8, "red"),     # Alta
                                        (1, "darkred")    # Muy alta
                                    ],
                                    title='Mapa de Susceptibilidad',
                                    labels={'color': 'Nivel de Susceptibilidad'},
                                    zmin=0, zmax=5)

    # Personalizar la barra de color
    fig_susceptibilidad.update_coloraxes(
        colorbar=dict(
            tickvals=[0, 1, 2, 3, 4, 5],
            ticktext=['Sin riesgo', 'Muy baja', 'Baja', 'Moderada', 'Alta', 'Muy alta']
        )
    )
    fig_susceptibilidad.update_coloraxes(showscale=False)
    fig_susceptibilidad.update_layout(height=600, width=800)
    
    leyenda = crear_leyenda("Niveles de Susceptibilidad:", [
        ("Sin riesgo", "white"),
        ("Muy baja", "green"),
        ("Baja", "yellow"),
        ("Moderada", "orange"),
        ("Alta", "red"),
        ("Muy alta", "darkred")
    ])
    
    return fig_susceptibilidad, leyenda

def reproyectar_y_alinear(src, dst_crs, dst_transform, dst_shape):
    """Reproyecta y alinea un raster a un CRS, transformación y forma de destino."""
    dst_array = np.zeros(dst_shape, dtype=rasterio.float32)
    reproject(
        source=rasterio.band(src, 1),
        destination=dst_array,
        src_transform=src.transform,
        src_crs=src.crs,
        dst_transform=dst_transform,
        dst_crs=dst_crs,
        resampling=Resampling.bilinear
    )
    return dst_array

def eliminar_valores_atipicos(data, percentil_bajo=1, percentil_alto=99):
    """Elimina valores atípicos reemplazándolos con NaN."""
    data_finita = data[np.isfinite(data)]
    if len(data_finita) == 0:
        logger.warning("Todos los valores son infinitos o NaN.")
        return np.full_like(data, np.nan)
    
    low = np.nanpercentile(data_finita, percentil_bajo)
    high = np.nanpercentile(data_finita, percentil_alto)
    logger.info(f"Umbral bajo: {low}, Umbral alto: {high}")
    
    data_limpia = np.where((data >= low) & (data <= high), data, np.nan)
    return data_limpia

# Modifica la función de callback para incluir las nuevas variables
@app.callback(
    [Output('mapa-amenaza', 'figure'),
     Output('leyenda-amenaza', 'children'),
     Output('log-calculo', 'children')],
    [Input('calcular-amenaza-button', 'n_clicks')],
    [State('ruta-cobertura', 'value'),
     State('ruta-rasters-amenaza', 'value'),
     State('peso-susceptibilidad', 'value'),
     State('peso-precipitacion', 'value'),
     State('peso-temperatura', 'value'),
     State('peso-pendiente', 'value'),
     State('peso-accesibilidad', 'value'),
     State('peso-frecuencia', 'value'),
     State('peso-vientos', 'value'),
     State('peso-radiacion-solar', 'value')]
)
def calcular_y_mostrar_amenaza(n_clicks, ruta_cobertura, ruta_shps_amenaza, 
                               peso_susceptibilidad, peso_precipitacion, peso_temperatura, 
                               peso_pendiente, peso_accesibilidad, peso_frecuencia,
                               peso_vientos, peso_radiacion_solar):
    if n_clicks == 0 or not ruta_cobertura or not ruta_shps_amenaza:
        return dash.no_update, dash.no_update, ""
    
    logger.info("Iniciando cálculo de amenaza")
    ruta_base = os.path.dirname(ruta_cobertura)
    ruta_resultados = os.path.join(ruta_base, 'resultados')
    ruta_susceptibilidad = os.path.join(ruta_resultados, 'susceptibilidad.tif')
    
    variables = {
        'susceptibilidad': {'ruta': ruta_susceptibilidad, 'peso': peso_susceptibilidad},
        'precipitacion': {'ruta': os.path.join(ruta_shps_amenaza, 'precipitacion.shp'), 'peso': peso_precipitacion},
        'temperatura': {'ruta': os.path.join(ruta_shps_amenaza, 'temperatura.shp'), 'peso': peso_temperatura},
        'pendiente': {'ruta': os.path.join(ruta_shps_amenaza, 'pendiente.shp'), 'peso': peso_pendiente},
        'accesibilidad': {'ruta': os.path.join(ruta_shps_amenaza, 'accesibilidad.shp'), 'peso': peso_accesibilidad},
        'frecuencia': {'ruta': os.path.join(ruta_shps_amenaza, 'frecuencia.shp'), 'peso': peso_frecuencia},
        'vientos': {'ruta': os.path.join(ruta_shps_amenaza, 'vientos.shp'), 'peso': peso_vientos},
        'radiacion_solar': {'ruta': os.path.join(ruta_shps_amenaza, 'radiacion_solar.shp'), 'peso': peso_radiacion_solar}
    }

    
    rasters_disponibles = {}
    for nombre, info in variables.items():
        if os.path.exists(info['ruta']):
            if nombre == 'susceptibilidad':
                rasters_disponibles[nombre] = rasterio.open(info['ruta'])
            else:
                gdf = gpd.read_file(info['ruta'])
                if 'gridcode' not in gdf.columns:
                    logger.warning(f"El campo 'gridcode' no existe en el shapefile de {nombre}. Buscando un campo numérico alternativo.")
                    numeric_columns = gdf.select_dtypes(include=[np.number]).columns
                    if len(numeric_columns) > 0:
                        gdf['gridcode'] = gdf[numeric_columns[0]]
                        logger.info(f"Usando el campo '{numeric_columns[0]}' como 'gridcode' para {nombre}")
                    else:
                        logger.error(f"No se encontró un campo numérico adecuado en el shapefile de {nombre}")
                        continue
                raster_salida = os.path.join(ruta_resultados, f'{nombre}_raster.tif')
                calificar_y_rasterizar(gdf, nombre, raster_salida)
                rasters_disponibles[nombre] = rasterio.open(raster_salida)
        else:
            logger.warning(f"El archivo {nombre} no está disponible.")
    
    if len(rasters_disponibles) < 2:
        return dash.no_update, dash.no_update, "No hay suficientes variables disponibles para calcular la amenaza."
    
    try:
        max_bounds = None
        max_crs = None
        for src in rasters_disponibles.values():
            bounds = src.bounds
            if max_bounds is None or (
                bounds.left < max_bounds[0] or
                bounds.bottom < max_bounds[1] or
                bounds.right > max_bounds[2] or
                bounds.top > max_bounds[3]
            ):
                max_bounds = (bounds.left, bounds.bottom, bounds.right, bounds.top)
                max_crs = src.crs

        dst_transform, width, height = calculate_default_transform(
            max_crs, max_crs, max_bounds[2] - max_bounds[0], max_bounds[3] - max_bounds[1],
            left=max_bounds[0], bottom=max_bounds[1], right=max_bounds[2], top=max_bounds[3]
        )
        dst_shape = (height, width)

        logger.info(f"CRS de referencia: {max_crs}")
        logger.info(f"Forma de referencia: {dst_shape}")

        datos_raster = {}
        for nombre, src in rasters_disponibles.items():
            datos = reproyectar_y_alinear(src, max_crs, dst_transform, dst_shape)
            datos_raster[nombre] = datos
            logger.info(f"Raster {nombre} alineado. Forma: {datos.shape}")
            logger.info(f"Valores de {nombre} - Min: {np.nanmin(datos)}, Max: {np.nanmax(datos)}, Media: {np.nanmean(datos)}")
        
        mascara = np.zeros(dst_shape, dtype=bool)
        for datos in datos_raster.values():
            mascara |= ~np.isnan(datos)
        
        logger.info(f"Número de píxeles válidos en la máscara: {np.sum(mascara)}")
        
        amenaza = np.zeros(dst_shape, dtype=np.float32)
        peso_total = np.zeros(dst_shape, dtype=np.float32)
        for nombre, datos in datos_raster.items():
            peso = variables[nombre]['peso']
            logger.info(f"Procesando {nombre} con peso {peso}")
            logger.info(f"Datos de {nombre} - Min: {np.nanmin(datos)}, Max: {np.nanmax(datos)}, Media: {np.nanmean(datos)}")
            amenaza += np.nan_to_num(datos * peso)
            peso_total += np.where(~np.isnan(datos), peso, 0)

        logger.info(f"Amenaza antes de dividir - Min: {np.nanmin(amenaza)}, Max: {np.nanmax(amenaza)}, Media: {np.nanmean(amenaza)}")
        logger.info(f"Peso total - Min: {np.nanmin(peso_total)}, Max: {np.nanmax(peso_total)}, Media: {np.nanmean(peso_total)}")

        # Evitar división por cero y reemplazar NaN por 0
        amenaza = np.where(peso_total > 0, amenaza / peso_total, 0)
        amenaza = np.nan_to_num(amenaza, nan=0)

        logger.info(f"Amenaza después de dividir - Min: {np.min(amenaza)}, Max: {np.max(amenaza)}, Media: {np.mean(amenaza)}")

        # Reclasificar la amenaza en 5 categorías
        def reclasificar_amenaza(valor):
            if valor == 0:
                return 0  # Sin datos
            elif valor <= 1:
                return 1  # Muy baja
            elif valor <= 2:
                return 2  # Baja
            elif valor <= 3:
                return 3  # Moderada
            elif valor <= 4:
                return 4  # Alta
            else:
                return 5  # Muy alta

        amenaza_reclasificada = np.vectorize(reclasificar_amenaza)(amenaza)

        logger.info(f"Amenaza reclasificada - Min: {np.min(amenaza_reclasificada)}, Max: {np.max(amenaza_reclasificada)}")
        logger.info(f"Valores únicos en amenaza reclasificada: {np.unique(amenaza_reclasificada)}")

        # Después de calcular la amenaza, guardamos el raster
        ruta_base = os.path.dirname(ruta_cobertura)
        ruta_resultados = os.path.join(ruta_base, 'resultados')
        os.makedirs(ruta_resultados, exist_ok=True)
        ruta_amenaza = os.path.join(ruta_resultados, 'amenaza.tif')

        # Usamos la misma transformación y CRS que usamos para alinear los rasters
        with rasterio.open(ruta_amenaza, 'w', driver='GTiff',
                        height=amenaza.shape[0], width=amenaza.shape[1],
                        count=1, dtype=amenaza.dtype,
                        crs=max_crs, transform=dst_transform) as dst:
            dst.write(amenaza, 1)

        logger.info(f"Raster de amenaza guardado en: {ruta_amenaza}")

        # Crear el mapa de amenaza
        fig_amenaza = px.imshow(amenaza_reclasificada,
                                color_continuous_scale=[
                                    (0, "white"),     # Sin datos
                                    (0.2, "green"),   # Muy baja
                                    (0.4, "yellow"),  # Baja
                                    (0.6, "orange"),  # Moderada
                                    (0.8, "red"),     # Alta
                                    (1, "darkred")    # Muy alta
                                ],
                                title='Mapa de Amenaza',
                                labels={'color': 'Nivel de Amenaza'},
                                zmin=0, zmax=5)

        # Personalizar la barra de color
        fig_amenaza.update_coloraxes(
            colorbar=dict(
                tickvals=[0, 1, 2, 3, 4, 5],
                ticktext=['Sin datos', 'Muy baja', 'Baja', 'Moderada', 'Alta', 'Muy alta']
            )
        )
        fig_amenaza.update_coloraxes(showscale=False)
        fig_amenaza.update_layout(height=600, width=800)

        leyenda = crear_leyenda("Niveles de Amenaza:", [
            ("Sin datos", "white"),
            ("Muy baja", "green"),
            ("Baja", "yellow"),
            ("Moderada", "orange"),
            ("Alta", "red"),
            ("Muy alta", "darkred")
        ])

        log_calculo = html.Ul([
            html.Li("Cálculo de amenaza completado y mapa generado."),
            html.Li(f"Raster de amenaza guardado en: {ruta_amenaza}"),
            html.Li(f"Forma del array de amenaza: {amenaza.shape}"),
            html.Li(f"Valores de amenaza - Min: {np.min(amenaza):.4f}, Max: {np.max(amenaza):.4f}, Media: {np.mean(amenaza):.4f}"),
            html.Li(f"Valores de amenaza reclasificada - Min: {np.min(amenaza_reclasificada)}, Max: {np.max(amenaza_reclasificada)}")
        ])

        return fig_amenaza, leyenda, log_calculo
        
    except Exception as e:
        logger.error(f"Error en el cálculo de amenaza: {str(e)}")
        return dash.no_update, dash.no_update, html.Ul([html.Li(f"Error: {str(e)}")])
    
    finally:
        for src in rasters_disponibles.values():
            src.close()

@app.callback(
    Output("descargar-susceptibilidad", "data"),
    [Input("btn-descargar-susceptibilidad", "n_clicks")],
    [State('ruta-cobertura', 'value')],
    prevent_initial_call=True,
)
def descargar_susceptibilidad(n_clicks, ruta_cobertura):
    if n_clicks is None or not ruta_cobertura:
        return dash.no_update
    
    ruta_base = os.path.dirname(ruta_cobertura)
    ruta_resultados = os.path.join(ruta_base, 'resultados')
    ruta_susceptibilidad = os.path.join(ruta_resultados, 'susceptibilidad.tif')
    
    if os.path.exists(ruta_susceptibilidad):
        return dcc.send_file(ruta_susceptibilidad)
    else:
        return dash.no_update

@app.callback(
    Output("descargar-amenaza", "data"),
    [Input("btn-descargar-amenaza", "n_clicks")],
    [State('ruta-cobertura', 'value')],
    prevent_initial_call=True,
)
def descargar_amenaza(n_clicks, ruta_cobertura):
    if n_clicks is None or not ruta_cobertura:
        return dash.no_update
    
    ruta_base = os.path.dirname(ruta_cobertura)
    ruta_resultados = os.path.join(ruta_base, 'resultados')
    ruta_amenaza = os.path.join(ruta_resultados, 'amenaza.tif')
    
    if os.path.exists(ruta_amenaza):
        return dcc.send_file(ruta_amenaza)
    else:
        return dash.no_update

if __name__ == '__main__':
    logger.info("Iniciando la aplicación Dash")
    app.run_server(debug=True, use_reloader=False)
    logger.info("Aplicación Dash iniciada")