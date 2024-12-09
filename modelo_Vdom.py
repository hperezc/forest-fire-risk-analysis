import geopandas as gpd
import rasterio
from rasterio.features import rasterize
import numpy as np
from scipy import ndimage
import os
import pandas as pd
from rasterio.crs import CRS
from rasterio.warp import reproject, Resampling

def asignar_parametros(valor_cobertura):
    # Imprimir el valor recibido para depuración
    print(f"Valor de cobertura recibido: {valor_cobertura}")

    # Intentar convertir el valor a un código numérico
    try:
        if isinstance(valor_cobertura, str):
            # Si es una cadena, intentar convertirla a float y luego a int
            codigo_cobertura = int(float(valor_cobertura))
        elif isinstance(valor_cobertura, (int, float)):
            # Si ya es un número, simplemente convertirlo a int
            codigo_cobertura = int(valor_cobertura)
        else:
            # Si no es ni cadena ni número, levantar una excepción
            raise ValueError(f"Tipo de dato no esperado: {type(valor_cobertura)}")
    except ValueError as e:
        print(f"Error al convertir el valor de cobertura: {e}")
        return {}

    # Diccionario con los parámetros para cada tipo de cobertura
    parametros = {
        111: {'tipo_combustion': 'No combustibles', 'calific_tipoCombus': 0, 'tiempo_combustible': 'No combustibles', 'calific_tiempoCombus': 0, 'carga_total': 'No combustibles', 'calific_carga': 0},
        112: {'tipo_combustion': 'No combustibles', 'calific_tipoCombus': 0, 'tiempo_combustible': 'No combustibles', 'calific_tiempoCombus': 0, 'carga_total': 'No combustibles', 'calific_carga': 0},
        121: {'tipo_combustion': 'No combustibles', 'calific_tipoCombus': 0, 'tiempo_combustible': 'No combustibles', 'calific_tiempoCombus': 0, 'carga_total': 'No combustibles', 'calific_carga': 0},
        122: {'tipo_combustion': 'No combustibles', 'calific_tipoCombus': 0, 'tiempo_combustible': 'No combustibles', 'calific_tiempoCombus': 0, 'carga_total': 'No combustibles', 'calific_carga': 0},
        124: {'tipo_combustion': 'No combustibles', 'calific_tipoCombus': 0, 'tiempo_combustible': 'No combustibles', 'calific_tiempoCombus': 0, 'carga_total': 'No combustibles', 'calific_carga': 0},
        125: {'tipo_combustion': 'No combustibles', 'calific_tipoCombus': 0, 'tiempo_combustible': 'No combustibles', 'calific_tiempoCombus': 0, 'carga_total': 'No combustibles', 'calific_carga': 0},
        131: {'tipo_combustion': 'No combustibles', 'calific_tipoCombus': 0, 'tiempo_combustible': 'No combustibles', 'calific_tiempoCombus': 0, 'carga_total': 'No combustibles', 'calific_carga': 0},
        211: {'tipo_combustion': 'Hierbas / cultivos herbaceos', 'calific_tipoCombus': 4, 'tiempo_combustible': '1 hora', 'calific_tiempoCombus': 2, 'carga_total': '1-50ton/ha', 'calific_carga': 3},
        221: {'tipo_combustion': 'Hierbas / cultivos herbaceos', 'calific_tipoCombus': 4, 'tiempo_combustible': '1 hora', 'calific_tiempoCombus': 2, 'carga_total': '1-50ton/ha', 'calific_carga': 3},
        222: {'tipo_combustion': 'Hierbas / cultivos herbaceos', 'calific_tipoCombus': 4, 'tiempo_combustible': '1 hora', 'calific_tiempoCombus': 2, 'carga_total': '1-50ton/ha', 'calific_carga': 3},
        223: {'tipo_combustion': 'Hierbas / cultivos herbaceos', 'calific_tipoCombus': 4, 'tiempo_combustible': '1 hora', 'calific_tiempoCombus': 2, 'carga_total': '1-50ton/ha', 'calific_carga': 3},
        231: {'tipo_combustion': 'Pastos - Zonas verdes urbanas', 'calific_tipoCombus': 5, 'tiempo_combustible': '1 hora', 'calific_tiempoCombus': 1, 'carga_total': '1-50ton/ha', 'calific_carga': 2},
        232: {'tipo_combustion': 'Arbustos / hierbas - aroles / hierbas', 'calific_tipoCombus': 3, 'tiempo_combustible': '1 hora', 'calific_tiempoCombus': 1, 'carga_total': '1-50 ton/ha', 'calific_carga': 2},
        233: {'tipo_combustion': 'Hierbas / pastos', 'calific_tipoCombus': 5, 'tiempo_combustible': '1 hora', 'calific_tiempoCombus': 1, 'carga_total': '50-100 ton/ha', 'calific_carga': 3},
        241: {'tipo_combustion': 'Hierbas / cultivos herbaceos', 'calific_tipoCombus': 3, 'tiempo_combustible': '1 hora', 'calific_tiempoCombus': 1, 'carga_total': '1-50ton/ha', 'calific_carga': 2},
        242: {'tipo_combustion': 'Hierbas / cultivos herbaceos', 'calific_tipoCombus': 3, 'tiempo_combustible': '1 hora', 'calific_tiempoCombus': 1, 'carga_total': '1-50ton/ha', 'calific_carga': 2},
        243: {'tipo_combustion': 'Hierbas / cultivos herbaceos', 'calific_tipoCombus': 3, 'tiempo_combustible': '1 hora', 'calific_tiempoCombus': 1, 'carga_total': '1-50ton/ha', 'calific_carga': 2},
        244: {'tipo_combustion': 'Pastos - Zonas verdes urbanas', 'calific_tipoCombus': 3, 'tiempo_combustible': '1 hora', 'calific_tiempoCombus': 1, 'carga_total': '<10 ton/ha', 'calific_carga': 1},
        245: {'tipo_combustion': 'Hierbas / cultivos herbaceos', 'calific_tipoCombus': 3, 'tiempo_combustible': '1 hora', 'calific_tiempoCombus': 1, 'carga_total': '1-50ton/ha', 'calific_carga': 2},
        311: {'tipo_combustion': 'Arboles / atbustos', 'calific_tipoCombus': 2, 'tiempo_combustible': '100 horas', 'calific_tiempoCombus': 3, 'carga_total': '>100 ton/ha', 'calific_carga': 4},
        312: {'tipo_combustion': 'Arboles / atbustos', 'calific_tipoCombus': 2, 'tiempo_combustible': '100 horas', 'calific_tiempoCombus': 3, 'carga_total': '>100 ton/ha', 'calific_carga': 4},
        313: {'tipo_combustion': 'Arboles / atbustos', 'calific_tipoCombus': 2, 'tiempo_combustible': '100 horas', 'calific_tiempoCombus': 3, 'carga_total': '>100 ton/ha', 'calific_carga': 4},
        314: {'tipo_combustion': 'Arboles / atbustos', 'calific_tipoCombus': 2, 'tiempo_combustible': '100 horas', 'calific_tiempoCombus': 3, 'carga_total': '>100 ton/ha', 'calific_carga': 4},
        315: {'tipo_combustion': 'Arboles / atbustos', 'calific_tipoCombus': 3, 'tiempo_combustible': '100 horas', 'calific_tiempoCombus': 2, 'carga_total': '>100 ton/ha', 'calific_carga': 3},
        321: {'tipo_combustion': 'Hierbas / pastos', 'calific_tipoCombus': 5, 'tiempo_combustible': '1 hora', 'calific_tiempoCombus': 1, 'carga_total': '50-100 ton/ha', 'calific_carga': 3},
        322: {'tipo_combustion': 'Arbustos / hierbas - aroles / hierbas', 'calific_tipoCombus': 3, 'tiempo_combustible': '10 horas', 'calific_tiempoCombus': 2, 'carga_total': '50-100 ton/ha', 'calific_carga': 3},
        323: {'tipo_combustion': 'Arboles / atbustos', 'calific_tipoCombus': 2, 'tiempo_combustible': '100 horas', 'calific_tiempoCombus': 3, 'carga_total': '50-100 ton/ha', 'calific_carga': 3},
        331: {'tipo_combustion': 'No combustibles', 'calific_tipoCombus': 0, 'tiempo_combustible': 'No combustibles', 'calific_tiempoCombus': 0, 'carga_total': 'No combustibles', 'calific_carga': 0},
        332: {'tipo_combustion': 'No combustibles', 'calific_tipoCombus': 0, 'tiempo_combustible': 'No combustibles', 'calific_tiempoCombus': 0, 'carga_total': 'No combustibles', 'calific_carga': 0},
        333: {'tipo_combustion': 'No combustibles', 'calific_tipoCombus': 0, 'tiempo_combustible': 'No combustibles', 'calific_tiempoCombus': 0, 'carga_total': 'No combustibles', 'calific_carga': 0},
        334: {'tipo_combustion': 'No combustibles', 'calific_tipoCombus': 0, 'tiempo_combustible': 'No combustibles', 'calific_tiempoCombus': 0, 'carga_total': 'No combustibles', 'calific_carga': 0},
        411: {'tipo_combustion': 'No combustibles', 'calific_tipoCombus': 4, 'tiempo_combustible': 'No combustibles', 'calific_tiempoCombus': 1, 'carga_total': 'No combustibles', 'calific_carga': 2},
        413: {'tipo_combustion': 'No combustibles', 'calific_tipoCombus': 0, 'tiempo_combustible': 'No combustibles', 'calific_tiempoCombus': 0, 'carga_total': 'No combustibles', 'calific_carga': 0},
        511: {'tipo_combustion': 'No combustibles', 'calific_tipoCombus': 0, 'tiempo_combustible': 'No combustibles', 'calific_tiempoCombus': 0, 'carga_total': 'No combustibles', 'calific_carga': 0},
        512: {'tipo_combustion': 'No combustibles', 'calific_tipoCombus': 0, 'tiempo_combustible': 'No combustibles', 'calific_tiempoCombus': 0, 'carga_total': 'No combustibles', 'calific_carga': 0},
        514: {'tipo_combustion': 'No combustibles', 'calific_tipoCombus': 0, 'tiempo_combustible': 'No combustibles', 'calific_tiempoCombus': 0, 'carga_total': 'No combustibles', 'calific_carga': 0}
    }
    
    if codigo_cobertura not in parametros:
        print(f"Advertencia: No se encontraron parámetros para el tipo de cobertura con código '{codigo_cobertura}'")
        return {}
    
    return parametros[codigo_cobertura]



def vector_a_raster(gdf, columna, raster_salida, resolucion):
    # Obtener la extensión del GeoDataFrame
    minx, miny, maxx, maxy = gdf.total_bounds
    
    # Calcular las dimensiones del raster
    width = int((maxx - minx) / resolucion)
    height = int((maxy - miny) / resolucion)
    
    # Crear la transformación afín
    transform = rasterio.transform.from_origin(minx, maxy, resolucion, resolucion)
    
    # Rasterizar el GeoDataFrame
    raster = rasterize(
        [(geom, value) for geom, value in zip(gdf.geometry, gdf[columna])],
        out_shape=(height, width),
        transform=transform,
        fill=np.nan,
        all_touched=True,
        dtype=np.float32
    )
    
    # Obtener el sistema de coordenadas del GeoDataFrame
    crs = gdf.crs
    
    # Redondear los valores a enteros y convertir a uint8
    raster_uint8 = np.where(np.isnan(raster), 0, np.round(raster)).astype(np.uint8)
    
    # Guardar el raster
    with rasterio.open(
        raster_salida, 
        'w', 
        driver='GTiff', 
        height=height, 
        width=width,
        count=1, 
        dtype=rasterio.uint8,
        crs=crs, 
        transform=transform,
        tiled=True,
        compress='lzw'
    ) as dst:
        dst.write(raster_uint8, 1)
        
        # Crear una rampa de color
        colormap = {
            i: (255, int(255 * (1 - i/5)), 0, 255) for i in range(6)
        }
        dst.write_colormap(1, colormap)
    
    print(f"Se ha creado el raster en {raster_salida}")

# Diccionario para mapear nombres de cobertura a códigos
mapeo_nombres_a_codigos = {
    'Tejido urbano continuo': 111,
    'Tejido urbano discontinuo': 112,
    'Zonas industriales o comerciales': 121,
    'Red vial, ferroviaria y terrenos asociados': 122,
    'Aeropuertos': 124,
    'Obras hidráulicas': 125,
    'Zonas de extracción minera': 131,
    'Otros cultivos transitorios': 211,
    'Cultivos permanentes herbáceos': 221,
    'Cultivos permanentes arbustivos': 222,
    'Cultivos permanentes arbóreos': 223,
    'Pastos limpios': 231,
    'Pastos arbolados': 232,
    'Pastos enmalezados': 233,
    'Mosaico de cultivos': 241,
    'Mosaico de pastos y cultivos': 242,
    'Mosaico de cultivos, pastos y espacios naturales': 243,
    'Mosaico de pastos con espacios naturales': 244,
    'Mosaico de cultivos con espacios naturales': 245,
    'Bosque denso': 311,
    'Bosque abierto': 312,
    'Bosque fragmentado': 313,
    'Bosque de galería y ripario': 314,
    'Plantación forestal': 315,
    'Herbazal': 321,
    'Arbustal': 322,
    'Vegetación secundaria o en transición': 323,
    'Zonas arenosas naturales': 331,
    'Afloramientos rocosos': 332,
    'Tierras desnudas y degradadas': 333,
    'Zonas quemadas': 334,
    'Zonas Pantanosas': 411,
    'Vegetación acuática sobre cuerpos de agua': 413,
    'Ríos (50 m)': 511,
    'Lagunas, lagos y ciénagas naturales': 512,
    'Cuerpos de agua artificiales': 514
}

def calificar_variable(gdf, nombre_variable):
    """
    Califica una variable según su tipo y rango de valores.
    """
    # Asegúrate de que el campo 'gridcode' existe en el GeoDataFrame
    if 'gridcode' not in gdf.columns:
        raise ValueError(f"El campo 'gridcode' no existe en el shapefile de {nombre_variable}")

    # Imprimir los valores únicos de gridcode para depuración
    print(f"Valores únicos en gridcode para {nombre_variable}: {gdf['gridcode'].unique()}")

    if nombre_variable == 'precipitacion':
        gdf['calificacion'] = pd.cut(gdf['gridcode'], 
                                     bins=[0, 1, 2, 3, 4, 5],
                                     labels=[1, 2, 3, 4, 5],
                                     include_lowest=True)
    elif nombre_variable == 'temperatura':
        gdf['calificacion'] = pd.cut(gdf['gridcode'], 
                                     bins=[0, 1, 2, 3, 4, 5],
                                     labels=[1, 2, 3, 4, 5],
                                     include_lowest=True)
    elif nombre_variable == 'pendiente':
        gdf['calificacion'] = pd.cut(gdf['gridcode'], 
                                     bins=[0, 1, 2, 3, 4, 5],
                                     labels=[1, 2, 3, 4, 5],
                                     include_lowest=True)
    elif nombre_variable == 'accesibilidad':
        gdf['calificacion'] = pd.cut(gdf['gridcode'], 
                                     bins=[0, 1, 2, 3, 4, 5],
                                     labels=[5, 4, 3, 2, 1],
                                     include_lowest=True)
    elif nombre_variable == 'frecuencia':
        gdf['calificacion'] = pd.cut(gdf['gridcode'], 
                                     bins=[0, 1, 2, 3, 4, 5],
                                     labels=[1, 2, 3, 4, 5],
                                     include_lowest=True)
    elif nombre_variable == 'vientos':
        gdf['calificacion'] = pd.cut(gdf['gridcode'], 
                                     bins=[0, 1, 2, 3, 4, 5],
                                     labels=[1, 2, 3, 4, 5],
                                     include_lowest=True)
    elif nombre_variable == 'radiacion_solar':
        gdf['calificacion'] = pd.cut(gdf['gridcode'], 
                                     bins=[0, 1, 2, 3, 4, 5],
                                     labels=[1, 2, 3, 4, 5],
                                     include_lowest=True)
    else:
        raise ValueError(f"Variable desconocida: {nombre_variable}")
    
    # Convertir la calificación a tipo entero
    gdf['calificacion'] = gdf['calificacion'].astype(int)
    
    return gdf

def calificar_y_rasterizar(gdf, nombre_variable, raster_salida, resolucion=30):
    """
    Califica una variable y la convierte a raster.
    """
    try:
        gdf_calificado = calificar_variable(gdf, nombre_variable)
    except ValueError as e:
        print(f"Error al calificar la variable {nombre_variable}: {str(e)}")
        print(f"Valores únicos en gridcode para {nombre_variable}: {gdf['gridcode'].unique()}")
        raise

    vector_a_raster(gdf_calificado, 'calificacion', raster_salida, resolucion)

def reproyectar_y_alinear(src, dst_crs, dst_transform, dst_shape):
    """
    Reproyecta y alinea un raster a un CRS, transformación y forma de destino.
    """
    datos = np.full(dst_shape, np.nan, dtype=np.float32)
    reproject(
        source=rasterio.band(src, 1),
        destination=datos,
        src_transform=src.transform,
        src_crs=src.crs,
        dst_transform=dst_transform,
        dst_crs=dst_crs,
        resampling=Resampling.nearest
    )
    return datos

def eliminar_valores_atipicos(datos, umbral=3):
    """
    Elimina valores atípicos de un array numpy.
    """
    datos_validos = datos[~np.isnan(datos)]
    media = np.mean(datos_validos)
    desv_est = np.std(datos_validos)
    datos_limpios = np.where(np.abs(datos - media) > umbral * desv_est, np.nan, datos)
    return datos_limpios