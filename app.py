import streamlit as st
from PIL import Image
from pdf2image import convert_from_bytes
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
import io
import os

st.set_page_config(page_title="Gestor de Firmas y Huella para PDF", layout="wide")

st.title("✍️ Aplicación de Firma y Huella Digital para PDFs")
st.write("Sube tu documento, aplica la posición automática o ajústala manualmente, y descarga el PDF.")

# Sección lateral: Cargar recursos propios de cada usuario
st.sidebar.header("1. Tus Credenciales")
firma_file = st.sidebar.file_uploader("Sube tu Firma (PNG transparente)", type=["png", "jpg", "jpeg"])
huella_file = st.sidebar.file_uploader("Sube tu Huella Digital (PNG transparente)", type=["png", "jpg", "jpeg"])

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

# Sección principal: Cargar PDF
st.header("2. Sube el Documento a Firmar")
pdf_file = st.file_uploader("Sube el archivo PDF (ej. Constancia o formulario)", type=["pdf"])

if pdf_file and firma_img and huella_img:
    pdf_bytes = pdf_file.read()
    
    # Convertir PDF a imágenes para previsualización
    try:
        images = convert_from_bytes(pdf_bytes)
    except Exception as e:
        st.error("Error al procesar el PDF con Poppler. Verifica la configuración de rutas.")
        st.stop()
        
    st.subheader("3. Configuración de Posición")
    pagina_seleccionada = st.selectbox("Selecciona la página a firmar:", range(len(images)), format_func=lambda x: f"Página {x + 1}")
    
    current_image = images[pagina_seleccionada]
    img_width, img_height = current_image.size
    
    # Casilla para activar el posicionamiento automático inteligente para formato Promart
    auto_detectar = st.checkbox("✨ Aplicar Posicionamiento Automático (Formato Promart)", value=True)
    
    # Coordenadas ajustadas con precisión final para centrar la huella
    if auto_detectar:
        val_sig_x = int(img_width * 0.23)
        val_sig_y = int(img_height * 0.69)
        val_sig_w = 254
        
        val_hue_x = int(img_width * 0.33)  # Ajustado al punto exacto de centrado horizontal
        val_hue_y = int(img_height * 1.52)  
        val_hue_w = 165
    else:
        val_sig_x = 385
        val_sig_y = 1611
        val_sig_w = 254
        
        val_hue_x = 450
        val_hue_y = 3568
        val_hue_w = 165

    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.image(current_image, caption=f"Página {pagina_seleccionada + 1}", use_container_width=True)
        
    with col2:
        st.info("Ajusta los valores si es necesario o déjalo en automático.")
        
        st.write("**Firma:**")
        sig_x = st.slider("Posición X (Firma)", 0, img_width, val_sig_x, key="sig_x")
        sig_y = st.slider("Posición Y (Firma)", 0, img_height * 2, val_sig_y, key="sig_y")
        sig_w = st.slider("Ancho Firma", 50, 300, val_sig_w, key="sig_w")
        
        st.write("**Huella Digital:**")
        hue_x = st.slider("Posición X (Huella)", 0, img_width, val_hue_x, key="hue_x")
        hue_y = st.slider("Posición Y (Huella)", 0, img_height * 2, val_hue_y, key="hue_y")
        hue_w = st.slider("Ancho Huella", 30, 200, val_hue_w, key="hue_w")

    if st.button("Generar y Estampar PDF", type="primary"):
        reader_temp = PdfReader(io.BytesIO(pdf_bytes))
        page_temp = reader_temp.pages[pagina_seleccionada]
        pdf_w = float(page_temp.mediabox.width)
        pdf_h = float(page_temp.mediabox.height)
        
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=(pdf_w, pdf_h))
        
        scale_x = pdf_w / img_width
        scale_y = pdf_h / img_height
        
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
        
        st.success("¡Documento firmado con éxito!")
        st.download_button(
            label="📥 Descargar PDF Firmado",
            data=output_pdf_bytes,
            file_name="documento_firmado.pdf",
            mime="application/pdf"
        )
elif not (firma_img and huella_img):
    st.info("👈 Sube primero tu firma y huella digital en la barra lateral para comenzar.")
else:
    st.info("👆 Sube un documento PDF en la sección superior para continuar.")
