import streamlit as st
from PIL import Image
from pdf2image import convert_from_bytes
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
import io
import os
import json
from datetime import datetime
from google import genai

st.set_page_config(page_title="Gestor IA de Firmas y PDFs", layout="wide")

st.title("🤖 Aplicación con IA para Detección de Campos en PDFs")
st.write("Sube cualquier tipo de formato y la IA analizará visualmente el documento para ubicar los campos con precisión.")

# Sección lateral: Credenciales de IA y Archivos
st.sidebar.header("1. Configuración de IA")
api_key = st.sidebar.text_input("API Key de Gemini", type="password", placeholder="Pega tu clave aquí")

st.sidebar.header("2. Tus Credenciales")
firma_file = st.sidebar.file_uploader("Sube tu Firma (PNG transparente)", type=["png", "jpg", "jpeg"])
huella_file = st.sidebar.file_uploader("Sube tu Huella Digital (PNG transparente)", type=["png", "jpg", "jpeg"])

st.sidebar.header("3. Datos del Trabajador")
txt_nombre = st.sidebar.text_input("Nombre Completo", placeholder="Ej. Juan Pérez")
txt_dni = st.sidebar.text_input("DNI", placeholder="Ej. 74859612")
txt_empresa = st.sidebar.text_input("Empresa", value="HOMECENTERS PERUANOS S.A.")
txt_puesto = st.sidebar.text_input("Puesto", placeholder="Ej. Asistente de Ventas")

txt_fecha = st.sidebar.text_input("Fecha", value=datetime.now().strftime("%d/%m/%Y"), placeholder="Ej. 25/11/2026")
txt_lugar = st.sidebar.text_input("Lugar", value="Lima", placeholder="Ej. Lima")

firma_img = None
huella_img = None

if firma_file:
    firma_img = Image.open(firma_file)
    st.sidebar.image(firma_img, caption="Tu Firma Registrada", width=150)
else:
    st.sidebar.warning("⚠️ Sube tu firma.")

if huella_file:
    huella_img = Image.open(huella_file)
    st.sidebar.image(huella_img, caption="Tu Huella Registrada", width=150)
else:
    st.sidebar.warning("⚠️ Sube tu huella.")

# Función para conectar con Gemini y detectar coordenadas visuales con el modelo estable
def detectar_coordenadas_con_ia(imagen_pil, api_key):
    if not api_key:
        return None
    try:
        client = genai.Client(api_key=api_key)
        prompt = """
        Analiza visualmente este documento de trabajo o constancia.
        Identifica la ubicación aproximada de los siguientes elementos en una escala normalizada de 0.0 a 1.0 (donde 0,0 es la esquina superior izquierda):
        1. Nombre del trabajador y DNI.
        2. Empresa.
        3. Puesto.
        4. Espacio para la Firma.
        5. Espacio para la Huella Digital.
        6. Lugar.

        Devuelve la respuesta EXCLUSIVAMENTE en un formato JSON válido (sin texto adicional ni bloques de Markdown como ```json) con las siguientes llaves exactas:
        {
          "nombre_x": 0.0, "nombre_y": 0.0,
          "dni_x": 0.0, "dni_y": 0.0,
          "empresa_x": 0.0, "empresa_y": 0.0,
          "puesto_x": 0.0, "puesto_y": 0.0,
          "firma_x": 0.0, "firma_y": 0.0,
          "huella_x": 0.0, "huella_y": 0.0,
          "lugar_x": 0.0, "lugar_y": 0.0
        }
        """
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=[imagen_pil, prompt]
        )
        texto_respuesta = response.text.strip()
        if texto_respuesta.startswith("```json"):
            texto_respuesta = texto_respuesta[7:-3].strip()
        elif texto_respuesta.startswith("```"):
            texto_respuesta = texto_respuesta[3:-3].strip()
            
        return json.loads(texto_respuesta)
    except Exception as e:
        st.error(f"Error al conectar con Gemini: {e}")
        return None

# Sección principal: Cargar PDF
st.header("4. Sube el Documento a Rellenar y Firmar")
pdf_file = st.file_uploader("Sube el archivo PDF", type=["pdf"])

if pdf_file and firma_img and huella_img:
    pdf_bytes = pdf_file.read()
    
    try:
        images = convert_from_bytes(pdf_bytes)
    except Exception as e:
        st.error("Error al procesar el PDF con Poppler. Verifica la configuración de rutas.")
        st.stop()
        
    st.subheader("5. Previsualización y Análisis con IA")
    pagina_seleccionada = st.selectbox("Selecciona la página:", range(len(images)), format_func=lambda x: f"Página {x + 1}")
    
    current_image = images[pagina_seleccionada]
    img_width, img_height = current_image.size
    
    # Inicializar estado para coordenadas si no existen
    if "coords" not in st.session_state:
        st.session_state["coords"] = {
            "nombre_x": 0.16, "nombre_y": 0.745,
            "dni_x": 0.75, "dni_y": 0.745,
            "empresa_x": 0.38, "empresa_y": 0.715,
            "puesto_x": 0.16, "puesto_y": 0.685,
            "firma_x": 0.21, "firma_y": 0.70,
            "huella_x": 0.27, "huella_y": 1.52,
            "lugar_x": 0.23, "lugar_y": 0.44
        }

    if st.button("✨ Analizar Documento con IA y Auto-ubicar", type="primary"):
        if api_key:
            with st.spinner("La IA está analizando la estructura visual de tu documento..."):
                res_ia = detectar_coordenadas_con_ia(current_image, api_key)
                if res_ia:
                    st.session_state["coords"].update(res_ia)
                    st.success("¡Coordenadas detectadas y adaptadas por la IA con éxito!")
                else:
                    st.warning("No se pudo obtener respuesta de la IA, usando valores predeterminados.")
        else:
            st.error("Por favor ingresa tu API Key de Gemini en la barra lateral.")

    c = st.session_state["coords"]

    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.image(current_image, caption=f"Página {pagina_seleccionada + 1}", use_container_width=True)
        
    with col2:
        st.info("Ajusta las posiciones si es necesario.")
        sig_x = st.slider("Posición X (Firma)", 0, img_width, int(img_width * c.get("firma_x", 0.21)))
        sig_y = st.slider
