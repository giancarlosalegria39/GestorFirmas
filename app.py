import os
import streamlit as st
from PIL import Image
from pdf2image import convert_from_bytes
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
import io

st.set_page_config(page_title="Gestor de Firmas y Huella para PDF", layout="wide")

st.title("✍️ Aplicación de Firma y Huella Digital para PDFs")
st.write("Sube tu documento, ajusta la posición de tu firma y huella, y descarga el PDF listo para enviar.")

# Crear carpeta assets si no existe
os.makedirs("assets", exist_ok=True)

# Sección lateral: Cargar recursos fijos (Firma y Huella)
st.sidebar.header("1. Tus Recursos Guardados")
firma_file = st.sidebar.file_uploader("Sube tu Firma (PNG transparente)", type=["png", "jpg", "jpeg"])
huella_file = st.sidebar.file_uploader("Sube tu Huella Digital (PNG transparente)", type=["png", "jpg", "jpeg"])

if firma_file:
    with open("assets/firma.png", "wb") as f:
        f.write(firma_file.getbuffer())

if huella_file:
    with open("assets/huella.png", "wb") as f:
        f.write(huella_file.getbuffer())

# Rutas de recursos
firma_path = "assets/firma.png"
huella_path = "assets/huella.png"

has_firma = os.path.exists(firma_path)
has_huella = os.path.exists(huella_path)

if has_firma:
    st.sidebar.image(firma_path, caption="Firma Registrada", width=150)
else:
    st.sidebar.warning("⚠️ Falta subir tu firma.")

if has_huella:
    st.sidebar.image(huella_path, caption="Huella Registrada", width=150)
else:
    st.sidebar.warning("⚠️ Falta subir tu huella.")

# Sección principal: Cargar PDF
st.header("2. Sube el Documento a Firmar")
pdf_file = st.file_uploader("Sube el archivo PDF (ej. Constancia de trabajo)", type=["pdf"])

if pdf_file and has_firma and has_huella:
    pdf_bytes = pdf_file.read()
    
    # Convertir PDF a imágenes para previsualización
    try:
        images = convert_from_bytes(pdf_bytes)
    except Exception as e:
        st.error("Error al procesar el PDF con Poppler. Verifica la configuración de rutas.")
        st.stop()
        
    st.subheader("3. Previsualización y Posicionamiento")
    pagina_seleccionada = st.selectbox("Selecciona la página a firmar:", range(len(images)), format_func=lambda x: f"Página {x + 1}")
    
    current_image = images[pagina_seleccionada]
    img_width, img_height = current_image.size
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.image(current_image, caption=f"Página {pagina_seleccionada + 1}", use_container_width=True)
        
    with col2:
        st.info("Ajusta las coordenadas y tamaños para ubicar perfectamente tu firma y huella.")
        
        st.write("**Firma:**")
        sig_x = st.slider("Posición X (Firma)", 0, img_width, int(img_width * 0.4), key="sig_x")
        sig_y = st.slider("Posición Y (Firma)", 0, img_height, int(img_height * 0.8), key="sig_y")
        sig_w = st.slider("Ancho Firma", 50, 300, 150, key="sig_w")
        
        st.write("**Huella Digital:**")
        hue_x = st.slider("Posición X (Huella)", 0, img_width, int(img_width * 0.7), key="hue_x")
        hue_y = st.slider("Posición Y (Huella)", 0, img_height, int(img_height * 0.8), key="hue_y")
        hue_w = st.slider("Ancho Huella", 30, 200, 70, key="hue_w")

    if st.button("Generar y Estampar PDF", type="primary"):
        reader_temp = PdfReader(io.BytesIO(pdf_bytes))
        page_temp = reader_temp.pages[pagina_seleccionada]
        pdf_w = float(page_temp.mediabox.width)
        pdf_h = float(page_temp.mediabox.height)
        
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=(pdf_w, pdf_h))
        
        # Factores de escala entre la imagen mostrada y el PDF real
        scale_x = pdf_w / img_width
        scale_y = pdf_h / img_height
        
        # Mapeo de coordenadas (invirtiendo el eje Y de pantalla a PDF)
        r_sig_x = sig_x * scale_x
        r_sig_y = pdf_h - (sig_y * scale_y)
        r_sig_w = sig_w * scale_x
        
        r_hue_x = hue_x * scale_x
        r_hue_y = pdf_h - (hue_y * scale_y)
        r_hue_w = hue_w * scale_x
        
        can.drawImage(firma_path, r_sig_x, r_sig_y, width=r_sig_w, preserveAspectRatio=True, mask='auto')
        can.drawImage(huella_path, r_hue_x, r_hue_y, width=r_hue_w, preserveAspectRatio=True, mask='auto')
        can.save()
        
        packet.seek(0)
        overlay_pdf = PdfReader(packet)
        overlay_page = overlay_pdf.pages[0]
        
        # Fusionar capa con el PDF original
        writer = PdfWriter()
        for i, page in enumerate(reader_temp.pages):
            if i == pagina_seleccionada:
                page.merge_page(overlay_page)
            writer.add_page(page)
            
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
elif not (has_firma and has_huella):
    st.info("👈 Sube primero tu imagen de firma y tu huella digital en la barra lateral.")
else:
    st.info("👆 Sube un documento PDF en la sección superior para comenzar.")