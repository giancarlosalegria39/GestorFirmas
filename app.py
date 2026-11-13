import streamlit as st
from PIL import Image
from pdf2image import convert_from_bytes
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
import pdfplumber
import io
import os
from datetime import datetime

st.set_page_config(page_title="Gestor Inteligente de Firmas y PDFs", layout="wide")

st.title("✍️ Aplicación Inteligente de Firma, Huella y Llenado de PDFs")
st.write("Sube cualquier variante de documento y el sistema detectará automáticamente las palabras clave para rellenar y firmar con precisión.")

# Sección lateral: Cargar Credenciales
st.sidebar.header("1. Tus Credenciales")
firma_file = st.sidebar.file_uploader("Sube tu Firma (PNG transparente)", type=["png", "jpg", "jpeg"])
huella_file = st.sidebar.file_uploader("Sube tu Huella Digital (PNG transparente)", type=["png", "jpg", "jpeg"])

st.sidebar.header("2. Datos del Trabajador")
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
    st.sidebar.warning("⚠️ Sube tu firma para continuar.")

if huella_file:
    huella_img = Image.open(huella_file)
    st.sidebar.image(huella_img, caption="Tu Huella Registrada", width=150)
else:
    st.sidebar.warning("⚠️ Sube tu huella para continuar.")

# Función para buscar coordenadas relativas de palabras clave en el PDF
def buscar_coordenada_palabra(pdf_bytes, pagina_idx, palabra_clave):
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        page = pdf.pages[pagina_idx]
        words = page.extract_words()
        for word in words:
            if palabra_clave.lower() in word['text'].lower():
                return word['x0'] / page.width, word['top'] / page.height
    return None

# Sección principal: Cargar PDF
st.header("3. Sube el Documento a Rellenar y Firmar")
pdf_file = st.file_uploader("Sube el archivo PDF de la Constancia", type=["pdf"])

if pdf_file and firma_img and huella_img:
    pdf_bytes = pdf_file.read()
    
    try:
        images = convert_from_bytes(pdf_bytes)
    except Exception as e:
        st.error("Error al procesar el PDF con Poppler. Verifica la configuración de rutas.")
        st.stop()
        
    st.subheader("4. Previsualización y Posicionamiento Inteligente por Anclaje")
    pagina_seleccionada = st.selectbox("Selecciona la página a rellenar:", range(len(images)), format_func=lambda x: f"Página {x + 1}")
    
    current_image = images[pagina_seleccionada]
    img_width, img_height = current_image.size
    
    auto_detectar = st.checkbox("✨ Activar Detección Automática por Palabras Clave", value=True)
    
    # --- VALORES POR DEFECTO (RESPALDO) ---
    pos_nombre_x, pos_nombre_y = 0.16, 0.745
    pos_dni_x, pos_dni_y = 0.75, 0.745
    pos_empresa_x, pos_empresa_y = 0.38, 0.715
    pos_puesto_x, pos_puesto_y = 0.16, 0.685
    pos_firma_x, pos_firma_y = 0.21, 0.70
    pos_lugar_x, pos_lugar_y = 0.23, 0.44
    
    if auto_detectar:
        # Búsqueda dinámica de anclajes en el documento actual
        c_yo = buscar_coordenada_palabra(pdf_bytes, pagina_seleccionada, "Yo")
        c_dni = buscar_coordenada_palabra(pdf_bytes, pagina_seleccionada, "DNI")
        c_empresa = buscar_coordenada_palabra(pdf_bytes, pagina_seleccionada, "empresa")
        c_puesto = buscar_coordenada_palabra(pdf_bytes, pagina_seleccionada, "puesto")
        c_firma = buscar_coordenada_palabra(pdf_bytes, pagina_seleccionada, "Firma")
        c_lugar = buscar_coordenada_palabra(pdf_bytes, pagina_seleccionada, "Lima") or buscar_coordenada_palabra(pdf_bytes, pagina_seleccionada, "Lugar")
        
        if c_yo:
            pos_nombre_x = c_yo[0] + 0.04
            pos_nombre_y = c_yo[1]
        if c_dni:
            pos_dni_x = c_dni[0] + 0.08
            pos_dni_y = c_dni[1]
        if c_empresa:
            pos_empresa_x = c_empresa[0] + 0.08
            pos_empresa_y = c_empresa[1]
        if c_puesto:
            pos_puesto_x = c_puesto[0] + 0.04
            pos_puesto_y = c_puesto[1]
        if c_firma:
            pos_firma_x = c_firma[0]
            pos_firma_y = c_firma[1] + 0.02
        if c_lugar:
            pos_lugar_x = c_lugar[0]
            pos_lugar_y = c_lugar[1]
            
        st.success("🔍 ¡Palabras clave detectadas y adaptadas automáticamente al nuevo documento!")

    val_sig_x = int(img_width * pos_firma_x)  
    val_sig_y = int(img_height * pos_firma_y)  
    val_sig_w = 254
    
    val_hue_x = int(img_width * 0.27)  
    val_hue_y = int(img_height * 1.52)  
    val_hue_w = 165

    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.image(current_image, caption=f"Página {pagina_seleccionada + 1}", use_container_width=True)
        
    with col2:
        st.info("Puedes afinar la posición con los controles si es necesario.")
        
        st.write("**Firma:**")
        sig_x = st.slider("Posición X (Firma)", 0, img_width, val_sig_x, key="sig_x")
        sig_y = st.slider("Posición Y (Firma)", 0, img_height * 2, val_sig_y, key="sig_y")
        sig_w = st.slider("Ancho Firma", 50, 300, val_sig_w, key="sig_w")
        
        st.write("**Huella Digital:**")
        hue_x = st.slider("Posición X (Huella)", 0, img_width, val_hue_x, key="hue_x")
        hue_y = st.slider("Posición Y (Huella)", 0, img_height * 2, val_hue_y, key="hue_y")
        hue_w = st.slider("Ancho Huella", 30, 200, val_hue_w, key="hue_w")

    if st.button("Generar, Rellenar y Estampar PDF", type="primary"):
        reader_temp = PdfReader(io.BytesIO(pdf_bytes))
        page_temp = reader_temp.pages[pagina_seleccionada]
        pdf_w = float(page_temp.mediabox.width)
        pdf_h = float(page_temp.mediabox.height)
        
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=(pdf_w, pdf_h))
        
        scale_x = pdf_w / img_width
        scale_y = pdf_h / img_height
        
        # --- ESTAMPAR TEXTOS CON COORDENADAS DINÁMICAS ---
        can.setFont("Helvetica", 10)
        
        can.drawString(pdf_w * pos_nombre_x, pdf_h * (1 - pos_nombre_y), txt_nombre)
        can.drawString(pdf_w * pos_dni_x, pdf_h * (1 - pos_dni_y), txt_dni)
        can.drawString(pdf_w * pos_empresa_x, pdf_h * (1 - pos_empresa_y), txt_empresa)
        can.drawString(pdf_w * pos_puesto_x, pdf_h * (1 - pos_puesto_y), txt_puesto)
        
        try:
            partes_fecha = txt_fecha.replace("-", "/").split("/")
            dia, mes, anio = partes_fecha[0], partes_fecha[1], partes_fecha[2]
        except:
            dia, mes, anio = txt_fecha, "", ""

        y_fecha = pdf_h * 0.47
        can.drawString(pdf_w * 0.23, y_fecha, str(dia))    
        can.drawString(pdf_w * 0.31, y_fecha, str(mes))    
        can.drawString(pdf_w * 0.42, y_fecha, str(anio))   
        
        can.drawString(pdf_w * pos_lugar_x, pdf_h * (1 - pos_lugar_y), txt_lugar)
        
        # --- ESTAMPAR FIRMA Y HUELLA ---
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
    st.info("👈 Sube primero tu firma y huella digital en la barra lateral para comenzar.")
else:
    st.info("👆 Sube un documento PDF en la sección superior para continuar.")
