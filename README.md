# Proyecto de Análisis de Incendios

Este proyecto permite analizar y visualizar datos de incendios forestales utilizando técnicas de clustering y visualización interactiva. La aplicación está dividida en dos módulos principales:

- **Backend:** (archivo `model_backend.py`) Se encarga de cargar, procesar y generar resúmenes, clusters y matrices de riesgo a partir de los datos.
- **Interfaz de Usuario (UI):** (archivo `model_ui.py`) Proporciona una aplicación interactiva desarrollada con Tkinter y matplotlib para explorar los resultados de forma visual.

## Requisitos

- Python 3.7 o superior.
- Las siguientes librerías de Python:
  - [pandas](https://pandas.pydata.org/)
  - [numpy](https://numpy.org/)
  - [matplotlib](https://matplotlib.org/)
  - [seaborn](https://seaborn.pydata.org/)
  - [scikit-learn](https://scikit-learn.org/)
  - [pillow](https://python-pillow.org/) (para el manejo de imágenes en Tkinter)
  - Tkinter (generalmente incluido con Python)

## Instalación

1. Clona este repositorio o descarga los archivos del proyecto.

2. Instala las dependencias necesarias con pip. Puedes hacerlo ejecutando en la terminal:

   ```bash
   pip install pandas numpy matplotlib seaborn scikit-learn pillow
   ```

3. Asegúrate de tener el archivo `BD.csv` en la raíz del proyecto. Este archivo debe contener los datos de incendios que utilizará la aplicación.

## Estructura del Proyecto

- `model_backend.py`: Lógica de procesamiento de datos, clustering y generación de resúmenes y matrices de riesgo.
- `model_ui.py`: Interfaz gráfica de usuario, que utiliza Tkinter y matplotlib para visualizar los resultados.
- `BD.csv`: Archivo con los datos de incendios (deben incluir al menos las columnas necesarias para el análisis, como `Latitud`, `Longitud`, `Año`, `Duración días`, `Tipo Vegetación`, etc.).

## Ejecución

Para iniciar la aplicación, ejecuta el siguiente comando desde la raíz del proyecto:

```bash
python model_ui.py
```

Se abrirá una ventana con la interfaz interactiva. Entre las funcionalidades se incluyen:

- **Selección de Año:** Navega entre los años (2015 a 2023) mediante los botones de "◀" y "▶". Al cambiar el año, se actualizan las visualizaciones.
- **Visualización de Clusters:** Muestra los clusters regionales e individuales generados para el año seleccionado.
- **Matriz de Riesgo:** Presenta una matriz que cruza los clusters regionales con los individuales.
- **Resumen:** Se muestran tablas con el Top 10 de regiones más afectadas y un resumen por ecosistema.
- **Análisis Histórico:** Accede a un análisis completo (acumulado de 2015 a 2023) con pestañas para clusters, matrices de riesgo y comparativas anuales.

## Uso

- **Cambiar de Año:** Usa los botones de navegación para actualizar la visualización al año deseado.
- **Explorar Pestañas:** La interfaz cuenta con pestañas para ver los distintos análisis (clusters, matriz de riesgo y resumen).
- **Consultar Leyendas:** En el panel lateral encontrarás leyendas que explican los colores y tamaños utilizados en los gráficos.

<img width="1278" alt="image" src="https://github.com/user-attachments/assets/ff7a5428-f412-44b3-8786-73b7f8d01905" />
