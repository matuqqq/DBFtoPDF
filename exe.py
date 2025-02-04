import sys
import os
import pandas as pd
from dbfread import DBF
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import configparser

# Función para obtener la ruta de los archivos dentro del ejecutable empaquetado
def resource_path(relative_path):
    """Obtiene la ruta correcta del archivo empaquetado o en desarrollo."""
    try:
        # PyInstaller crea una carpeta temporal para los recursos al ejecutar el .exe
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

config = configparser.ConfigParser()
config.read('diario.ini')

# Registra las fuentes correctamente con las rutas adecuadas
font_path_bold = resource_path('fonts/CourierPrime-Bold.ttf')
font_path_regular = resource_path('fonts/CourierPrime-Regular.ttf')

pdfmetrics.registerFont(TTFont("Courier-Bold", font_path_bold))
pdfmetrics.registerFont(TTFont("Courier", font_path_regular))

header_file = config['General']['PathDBF'] + '\\LIBPDFH.dbf'
detail_file = config['General']['PathDBF'] + '\\LIBPDFD.dbf'
output_pdf = config['General']['PathSalida']

name_title = config['Titulos']['Name']
main_title = "pagina inicial"

# Leer archivos DBF
headers = pd.DataFrame(iter(DBF(header_file, load=True)))
details = pd.DataFrame(iter(DBF(detail_file, load=True)))

# Depuración: Ver contenido de los DataFrames
# Reemplazar valores NaN en 'ASIENTO' por un valor predeterminado (por ejemplo, 0)
details['ASIENTO'] = details['ASIENTO'].fillna(0).astype(int)

# Asegurarnos que 'ASIENTO' de headers sea un entero
headers['ASIENTO'] = headers['ASIENTO'].astype(int)

# Comprobación de valores específicos
# Crear el PDF
c = canvas.Canvas(output_pdf, pagesize=letter)
width, height = letter

# Inicializar el contador de páginas
page_count = int(input("Ingrese numero de hoja: ")) 

# Función para dibujar el número de página
def draw_page_number(c, page_count):
    c.line(50, height - 70, width - 50, height - 70)
    c.setFont("Courier-Bold", 11)
    c.drawString(50, height - 50, name_title)
    c.drawString(50, height - 65, main_title)
    c.setFont("Courier", 11)
    c.drawString(475, height - 65, f"Hoja Nº {page_count}")
    c.line(50, height - 90, width - 50, height - 90)
    c.setFont("Courier", 9)

# Línea decorativa debajo del título
c.setStrokeColor("black")
c.setLineWidth(1)

# Espaciado después del título
y_position = height - 90

# Subtítulos de columnas con línea debajo
c.setFont("Courier", 9)
subtitles_y = y_position

c.drawString(50, height - 80, "CUENTA")
c.drawString(100, height - 80, "DESCRIPCIÓN")
c.drawString(230, height - 80, "DETALLE")
c.drawString(400, height - 80, "DEBE")
c.drawString(480, height - 80, "HABER")

# Línea debajo de los subtítulos con separación

y_position -= 35

draw_page_number(c, page_count)

# Iterar sobre cada asiento en la cabecera
for _, header in headers.iterrows():
    c.setFont("Courier", 9)
    
    if y_position < 100:  # Salto de página si llega al final
        c.showPage()
        page_count += 1  # Incrementar el contador de páginas
        y_position = height - 50
        
        # Redibujar subtítulos en la nueva página
        c.setFont("Courier", 9)
        c.drawString(50, height - 80, "CUENTA")
        c.drawString(100, height - 80, "DESCRIPCIÓN")
        c.drawString(230, height - 80, "DETALLE")
        c.drawString(400, height - 80, "DEBE")
        c.drawString(480, height - 80, "HABER")
        
        # Línea debajo de los subtítulos con separación
        c.line(50, height - 85, width - 50, height - 85)
        y_position = height - 90

        # Dibujar el número de página en la nueva página
        draw_page_number(c, page_count)

    # Escribir cabecera del asiento
    c.setFont("Courier-Bold", 9)
    c.drawString(50, y_position, f"ASIENTO N°: {header['ASIENTO']}     FECHA: {header['FECHA_ASI']}     DETALLE: {header['DETALLE']}")
    
    y_position -= 20

    # Filtrar detalles correspondientes a este asiento
    asiento_details = details[details['ASIENTO'] == header['ASIENTO']]  

    # Escribir los detalles
    c.setFont("Courier", 9)
    for _, detail in asiento_details.iterrows():
        if y_position < 50:  # Salto de página si llega al final
            c.showPage()
            page_count += 1  # Incrementar el contador de páginas
            y_position = height - 50

            # Redibujar subtítulos en la nueva página
            c.setFont("Courier", 9)
            c.drawString(50, height - 80, "CUENTA")
            c.drawString(100, height - 80, "DESCRIPCIÓN")
            c.drawString(230, height - 80, "DETALLE")
            c.drawString(400, height - 80, "DEBE")
            c.drawString(480, height - 80, "HABER")

            # Línea debajo de los subtítulos con separación
            y_position = height - 100

            # Dibujar el número de página en la nueva página
            draw_page_number(c, page_count)
            c.setFont("Courier-Bold", 9)
            c.drawString(50, y_position-25, f"ASIENTO N°: {header['ASIENTO']}     FECHA: {header['FECHA_ASI']}     DETALLE: {header['DETALLE']}")
            y_position-=45


        c.setFont("Courier", 9)
        c.drawString(50, y_position, str(detail['CUENTA']))
        c.drawString(95, y_position, str(detail['DESCRIP']))
        c.drawString(230, y_position, str(detail['DETALLE']))

        if(float(detail['DEBE']) == 0.0):
            c.drawString(400, y_position, '')
        else:
            c.drawString(400, y_position, str(detail['DEBE']))

        if(float(detail['HABER']) == 0.0):
            c.drawString(480, y_position, '')
        else:
            c.drawString(480, y_position, str(detail['HABER']))

        y_position -= 10

    c.line(50, y_position - 1, width - 50, y_position - 1)

    y_position -= 30  # Espaciado entre asientos

# Guardar el PDF
c.save()
print(f"PDF generado en: {output_pdf}")
