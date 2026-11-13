from google import genai
from google.genai import types

def detectar_coordenadas_con_ia(imagen_pil, api_key):
    """
    Envía la imagen del documento a Google Gemini Vision para detectar 
    las coordenadas normalizadas (0.0 a 1.0) de los campos.
    """
    if not api_key:
        return None
    
    try:
        # Inicializar el cliente oficial de Google GenAI
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
        
        # Llamada al modelo multimodal Gemini 2.5 Flash / 1.5 Flash
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[imagen_pil, prompt]
        )
        
        # Limpiar la respuesta para asegurar que sea un JSON válido
        texto_respuesta = response.text.strip()
        if texto_respuesta.startswith("```json"):
            texto_respuesta = texto_respuesta[7:-3].strip()
        elif texto_respuesta.startswith("```"):
            texto_respuesta = texto_respuesta[3:-3].strip()
            
        coordenadas = json.loads(texto_respuesta)
        return coordenadas

    except Exception as e:
        st.error(f"Error al conectar con Gemini: {e}")
        return None
