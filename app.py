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

# Función para conectar con Gemini usando el modelo correcto requerido por la API
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
            model='gemini-3.8-flash',  # Modelo requerido por la API de Google
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
        sig_y = st.slider("Posición Y (Firma)", 0, img_height * 2, int(img_height * c.get("firma_y", 0.70)))
        sig_w = st.slider("Ancho Firma", 50, 300, 254)
        
        hue_x = st.slider("Posición X (Huella)", 0, img_width, int(img_width * 0.27))
        hue_y = st.slider("Posición Y (Huella)", 0, img_height * 2, int(img_height * 0.52))
        hue_w = st.slider("Ancho Huella", 30, 200, 165)

    if st.button("Generar, Rellenar y Estampar PDF"):
        reader_temp = PdfReader(io.BytesIO(pdf_bytes))
        page_temp = reader_temp.pages[pagina_seleccionada]
        pdf_w = float(page_temp.mediabox.width)
        pdf_h = float(page_temp.mediabox.height)
        
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=(pdf_w, pdf_h))
        
        scale_x = pdf_w / img_width
        scale_y = pdf_h / img_height
        
        # Estampar Textos
        can.setFont("Helvetica", 10)
        can.drawString(pdf_w * c.get("nombre_x", 0.16), pdf_h * (1 - c.get("nombre_y", 0.745)), txt_nombre)
        can.drawString(pdf_w * c.get("dni_x", 0.75), pdf_h * (1 - c.get("dni_y", 0.745)), txt_dni)
        can.drawString(pdf_w * c.get("empresa_x", 0.38), pdf_h * (1 - c.get("empresa_y", 0.715)), txt_empresa)
        can.drawString(pdf_w * c.get("puesto_x", 0.16), pdf_h * (1 - c.get("puesto_y", 0.685)), txt_puesto)
        
        try:
            partes_fecha = txt_fecha.replace("-", "/").split("/")
            dia, mes, anio = partes_fecha[0], partes_fecha[1], partes_fecha[2]
        except:
            dia, mes, anio = txt_fecha, "", ""

        y_fecha = pdf_h * 0.47
        can.drawString(pdf_w * 0.23, y_fecha, str(dia))    
        can.drawString(pdf_w * 0.31, y_fecha, str(mes))    
        can.drawString(pdf_w * 0.42, y_fecha, str(anio))   
        
        can.drawString(pdf_w * c.get("lugar_x", 0.23), pdf_h * (1 - c.get("lugar_y", 0.44)), txt_lugar)
        
        # Estampar Firma y Huella
        r_sig_h = sig_w * scale_x * (firma_img.height / firma_img.width)
        r_hue_h = hue_w * scale_x * (huella_img.height / huella_img.width)
        
        r_sig_x = sig_x * scale_x
        r_sig_y = pdf_h - (sig_y * scale_y) - r_sig_h
        r_sig_w = sig_w * scale_x
        
        r_hue_x = hue_x * scale_x
        r_hue_y = pdf_h - (hue_y * scale_y) - r_hue_h
        r_hue_w = hue_w * scale_x
        
        temp_sig_path = "temp_firma.png"
        temp_hue_path = "temp_huella.png"
        firma_img.save(temp_sig_path)
        huella_img.save(temp_hue_path)
        
        can.drawImage(temp_sig_path, r_sig_x, r_sig_y, width=r_sig_w, preserveAspectRatio=True, mask='auto')
        can.drawImage(temp_hue_path, r_hue_x, r_hue_y, width=r_hue_w, preserveAspectRatio=True, mask='auto')
        can.save()
        
        if os.path.exists(temp_sig_path): os.remove(temp_sig_path)
        if os.path.exists(temp_hue_path): os.remove(temp_hue_path)
        
        packet.seek(0)
        overlay_pdf = PdfReader(packet)
        overlay_page = overlay_pdf.pages[0]
        
        writer = PdfWriter()
        writer.append(reader_temp)
        writer.pages[pagina_seleccionada].merge_page(overlay_page)
            
        output_pdf_bytes = io.BytesIO()
        writer.write(output_pdf_bytes)
        output_pdf_bytes.seek(0)
        
        st.success("¡Documento rellenado y firmado con éxito!")
        st.download_button(
            label="📥 Descargar PDF Rellenado y Firmado",
            data=output_pdf_bytes,
            file_name="constancia_completa.pdf",
            mime="application/pdf"
        )
elif not (firma_img and huella_img):
    st.info("👈 Sube primero tu firma y huella digital en la barra lateral.")
else:
    st.info("👆 Sube un documento PDF en la sección superior.")
