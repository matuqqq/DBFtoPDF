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

def format_currency(value):
    return "{:,.2f}".format(value).replace(",", "X").replace(".", ",").replace("X", ".")

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
main_title = "Libro Diario"

transporte_debe = 0.0
transporte_haber = 0.0

# Leer archivos DBF
headers = pd.DataFrame(iter(DBF(header_file, load=True, encoding='latin1')))
details = pd.DataFrame(iter(DBF(detail_file, load=True, encoding='latin1')))

# Depuración: Ver contenido de los DataFrames
headers['FECHA_ASI'] = pd.to_datetime(headers['FECHA_ASI'], format='%Y-%m-%d').dt.strftime('%d-%m-%Y')
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
    c.setFont("Courier-Bold", 11)
    c.drawString(50, height - 10, name_title)
    c.drawString(50, height - 25, main_title)
    c.setFont("Courier", 11)
    c.drawString(475, height - 25, f"Hoja Nº {page_count}")
    c.line(30, height - 45, width - 30, height - 45)
    c.setFont("Courier", 9)

# Línea decorativa debajo del título
c.setStrokeColor("black")
c.setLineWidth(1)

# Espaciado después del título
y_position = height - 30

# Subtítulos de columnas con línea debajo
c.setFont("Courier", 9)
subtitles_y = y_position

c.drawString(30, height - 40, "CUENTA")
c.drawString(80, height - 40, "DESCRIPCIÓN")
c.drawString(230, height - 40, "DETALLE")
c.drawString(400, height - 40, "DEBE")
c.drawString(480, height - 40, "HABER")

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
        c.drawString(30, height - 40, "CUENTA")
        c.drawString(80, height - 40, "DESCRIPCIÓN")
        c.drawString(230, height - 40, "DETALLE")
        c.drawString(400, height - 40, "DEBE")
        c.drawString(480, height - 40, "HABER")
        
        # Línea debajo de los subtítulos con separación
        c.line(30, height - 45, width - 30, height - 45)
        y_position = height - 40

        # Dibujar el número de página en la nueva página
        draw_page_number(c, page_count)

    # Escribir cabecera del asiento
    c.setFont("Courier-Bold", 9)
    c.drawString(50, y_position, f"ASIENTO N°: {header['ASIENTO']}     FECHA: {header['FECHA_ASI']}     DETALLE: {header['DETALLE']}")
    
    y_position -= 10

    # Filtrar detalles correspondientes a este asiento
    asiento_details = details[details['ASIENTO'] == header['ASIENTO']]  

    # Escribir los detalles
    c.setFont("Courier", 9)
    for _, detail in asiento_details.iterrows():
        if y_position < 5:  # Salto de página si llega al final
            c.showPage()
            page_count += 1  # Incrementar el contador de páginas
            y_position = height - 10

            # Redibujar subtítulos en la nueva página
            c.setFont("Courier", 9)
            c.drawString(30, height - 40, "CUENTA")
            c.drawString(80, height - 40, "DESCRIPCIÓN")
            c.drawString(230, height - 40, "DETALLE")
            c.drawString(400, height - 40, "DEBE")
            c.drawString(480, height - 40, "HABER")

            # Línea debajo de los subtítulos con separación
            y_position = height - 60

            # Dibujar el número de página en la nueva página
            draw_page_number(c, page_count)
            c.setFont("Courier-Bold", 9)
            c.drawString(50, y_position, f"ASIENTO N°: {header['ASIENTO']}     FECHA: {header['FECHA_ASI']}     DETALLE: {header['DETALLE']}")
            y_position-=10


        c.setFont("Courier", 9)
        c.drawString(30, y_position, str(detail['CUENTA']))
        c.drawString(75, y_position, str(detail['DESCRIP']))
        c.drawString(230, y_position, str(detail['DETALLE']))

        if(float(detail['DEBE']) == 0.0):
            c.drawString(400, y_position, '')
        else:
            c.drawString(400, y_position, format_currency(float(detail['DEBE'])))
            transporte_debe+=float(detail['DEBE'])

        if(float(detail['HABER']) == 0.0):
            c.drawString(480, y_position, '')
        else:
            c.drawString(480, y_position, format_currency(float(detail['HABER'])))
            transporte_haber+=float(detail['HABER'])

        y_position -= 10

    c.line(50, y_position - 1, width - 50, y_position - 1)

    y_position -= 20  # Espaciado entre asientos

c.drawString(275, y_position-25, "Transporte")

c.drawString(345, y_position-25, format_currency(float(str(transporte_debe))))

c.drawString(450, y_position-25, format_currency(float(str(transporte_haber))))

# Guardar el PDF
c.save()
print(f"PDF generado en: {output_pdf}")
