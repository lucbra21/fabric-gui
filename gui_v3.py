import streamlit as st
import subprocess
import base64
import os
from datetime import datetime
import re
import shlex  # Importamos shlex para manejar el escape de caracteres
from fpdf import FPDF


class PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, "Generado por Fabric AI", 0, 1, "C")

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Página {self.page_no()}", 0, 0, "C")


def get_binary_file_downloader_html(bin_file, file_label="File"):
    with open(bin_file, "rb") as f:
        data = f.read()
    bin_str = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{file_label}">Descargar {file_label}</a>'
    return href


def get_file_description(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    match = re.search(r"# RESUMEN\s*(.*?)\s*# IDEAS", content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return "No se encontró descripción"


# Diccionario de descripciones en español para los comandos más comunes de Fabric
DESCRIPCIONES_ES = {
    "summarize": "Resume un texto en puntos principales manteniendo la información clave",
    "extract_wisdom": "Extrae conocimientos, ideas y conceptos valiosos del contenido",
    "analyze_claims": "Analiza y evalúa afirmaciones identificando su validez y evidencia",
    "improve_writing": "Mejora la calidad, claridad y estructura de un texto",
    "explain_code": "Explica el funcionamiento del código de manera detallada y comprensible",
    "simplify": "Simplifica contenido complejo haciéndolo más accesible",
    "create_outline": "Crea una estructura organizada para un documento o texto",
    "extract_topics": "Identifica y extrae los temas principales del contenido",
    "write_essay": "Genera un ensayo bien estructurado sobre el tema proporcionado",
    "write_latex": "Genera un documento en formato LaTeX a partir del contenido",
    "create_coding_feature": "Desarrolla código para una nueva característica o funcionalidad",
    "translate": "Traduce contenido a otro idioma preservando el significado original",
    "extract_action_items": "Identifica tareas y acciones concretas a realizar",
    "extract_insights": "Extrae observaciones significativas y perspectivas valiosas",
    "create_flashcards": "Genera tarjetas de estudio con preguntas y respuestas",
    "panel_topic_extractor": "Extrae temas para discusión en paneles o debates",
    "create_quiz": "Genera preguntas tipo quiz sobre el contenido",
    "extract_experts": "Identifica expertos mencionados en el contenido y sus áreas de especialización",
    "evaluate_article": "Evalúa la calidad y credibilidad de un artículo",
    "improve_seo": "Mejora el contenido para optimización de motores de búsqueda",
    "extract_key_concepts": "Identifica y explica los conceptos fundamentales del contenido",
    "create_metaphors": "Genera metáforas para explicar conceptos complejos",
    "extract_arguments": "Extrae los principales argumentos y contraargumentos",
    "write_press_release": "Genera un comunicado de prensa profesional",
    "convert_to_blog": "Reformatea el contenido como una entrada de blog estructurada",
    "generate_title_ideas": "Propone títulos atractivos y relevantes para el contenido",
    "extract_data": "Extrae datos estructurados y cifras importantes",
    "create_faq": "Genera preguntas frecuentes y sus respuestas",
    "extract_quotes": "Encuentra y extrae citas relevantes del contenido",
    "create_presentation": "Genera esquema para una presentación basada en el contenido",
    "write_documentation": "Crea documentación técnica clara y completa",
    "extract_timeline": "Organiza eventos en una línea temporal cronológica",
    "create_story": "Genera una narrativa o historia basada en el contenido",
    "comparative_analysis": "Realiza un análisis comparativo de distintos elementos",
    "h3_telos": "Desarrolla un marco de objetivos, propósito y estrategia",
    "generate_analogies": "Crea analogías para explicar conceptos complejos",
    "identify_trends": "Identifica tendencias y patrones en los datos o información",
}


@st.cache_data(ttl=3600)  # Cache por una hora
def get_fabric_options():
    resultado = subprocess.run(["fabric", "-l"], capture_output=True, text=True)
    opciones = [line.strip() for line in resultado.stdout.split("\n") if line.strip()]
    # Filtrar para obtener solo comandos válidos (eliminar encabezados)
    opciones = [opt for opt in opciones if not opt.startswith("Available") and not opt.startswith("==")]
    return opciones


def markdown_to_pdf(markdown_file, pdf_file):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    with open(markdown_file, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    for line in lines:
        if line.startswith("# "):
            pdf.set_font("Arial", "B", 16)
            pdf.cell(
                0, 10, line[2:].encode("latin-1", "replace").decode("latin-1"), ln=True
            )
        elif line.startswith("## "):
            pdf.set_font("Arial", "B", 14)
            pdf.cell(
                0, 10, line[3:].encode("latin-1", "replace").decode("latin-1"), ln=True
            )
        else:
            pdf.set_font("Arial", size=12)
            pdf.multi_cell(0, 5, line.encode("latin-1", "replace").decode("latin-1"))

    pdf.output(pdf_file)


# Crear directorio para resultados si no existe
if not os.path.exists("resultados"):
    os.makedirs("resultados")

st.title("Generador de contenido con Fabric AI")

st.sidebar.title("Opciones")
show_files = st.sidebar.button("Mostrar archivos generados")

if show_files:
    st.sidebar.write("Archivos generados:")
    for filename in os.listdir("resultados"):
        if filename.endswith(".md"):
            filepath = os.path.join("resultados", filename)
            description = get_file_description(filepath)
            st.sidebar.write(f"**{filename}**")
            st.sidebar.write(description)

            download_link_md = get_binary_file_downloader_html(filepath, filename)
            st.sidebar.markdown(download_link_md, unsafe_allow_html=True)

            pdf_filename = filename.replace(".md", ".pdf")
            pdf_filepath = os.path.join("resultados", pdf_filename)
            markdown_to_pdf(filepath, pdf_filepath)
            download_link_pdf = get_binary_file_downloader_html(
                pdf_filepath, pdf_filename
            )
            st.sidebar.markdown(download_link_pdf, unsafe_allow_html=True)

            # Botón para borrar archivos
            if st.sidebar.button(f"Borrar {filename}"):
                os.remove(filepath)
                if os.path.exists(pdf_filepath):
                    os.remove(pdf_filepath)
                st.sidebar.write(f"{filename} y su versión PDF han sido borrados.")

            st.sidebar.write("---")

input_type = st.radio("Selecciona el tipo de entrada:", ["Texto", "YouTube", "URL"])

# Obtener opciones de Fabric
fabric_options = get_fabric_options()

# Mostrar selectbox con un icono de ayuda
col1, col2 = st.columns([3, 1])
with col1:
    fabric_command = st.selectbox("Selecciona el comando de Fabric:", fabric_options)
with col2:
    st.markdown('<br>', unsafe_allow_html=True)  # Espacio para alinear con el selectbox
    with st.expander("ℹ️"):
        st.markdown("**Ayuda sobre comandos**")
        for cmd in fabric_options:
            if cmd in DESCRIPCIONES_ES:
                st.markdown(f"**{cmd}**: {DESCRIPCIONES_ES[cmd]}")

# Mostrar la descripción del comando seleccionado
if fabric_command in DESCRIPCIONES_ES:
    st.info(f"**{fabric_command}**: {DESCRIPCIONES_ES[fabric_command]}")

# Selección de modelo
fabric_models = ("gpt-4o-mini", "gpt-4-0125-preview", "claude-3-5-sonnet-20240620")
fabric_modelo = st.radio("Selecciona el Modelo de LLM:", fabric_models)

if "] " in fabric_modelo:
    _, model_name = fabric_modelo.split("] ", 1)
else:
    model_name = fabric_modelo

# Entradas según tipo seleccionado
if input_type == "Texto":
    prompt = st.text_area("Ingresa tu texto:", "Haz un chiste con manzanas", height=150)
elif input_type == "YouTube":
    prompt = st.text_input(
        "Ingresa la URL del video de YouTube:",
        "https://www.youtube.com/watch?v=5rUa0wGzgdA",
    )
else:  # URL
    prompt = st.text_input(
        "Ingresa la URL:",
        "https://medium.com/stackademic/16-killer-web-applications-to-boost-your-workflow-with-ai-38153ace9352",
    )

# Añadir instrucción para responder en español
st.write("📝 La respuesta siempre será en español gracias al parámetro `--language=es`")

if st.button("Generar contenido"):
    with st.spinner("Generando contenido con Fabric... esto puede tomar un momento"):
        if input_type == "Texto":
            # Aseguramos el prompt para manejar caracteres especiales
            safe_prompt = shlex.quote(prompt)

            comando = f'echo {safe_prompt} | fabric --pattern {fabric_command} --model {model_name} --language=es'

            # Imprimimos el comando
            st.code(comando, language="bash")

            # Ejecutamos el comando usando 'bash' para interpretar el pipe
            resultado = subprocess.run(['bash', '-c', comando], capture_output=True, text=True)
        elif input_type == "YouTube":
            comando = (
                f"fabric -y '{prompt}' --pattern {fabric_command} --model {model_name} --language=es"
            )

            st.code(comando, language="bash")

            resultado = subprocess.run(["bash", "-c", comando], capture_output=True, text=True)
        else:  # URL
            comando = (
                f"fabric -u '{prompt}' --pattern {fabric_command} --model {model_name} --language=es"
            )

            st.code(comando, language="bash")

            resultado = subprocess.run(["bash", "-c", comando], capture_output=True, text=True)

        if resultado.returncode != 0:
            st.error(f"Error al ejecutar el comando:\n{resultado.stderr}")
        else:
            st.success("¡Contenido generado con éxito!")
            
            st.subheader("Resultado:")
            st.text_area("", value=resultado.stdout, height=300)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"resultado_{timestamp}.md"
            filepath = os.path.join("resultados", filename)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(resultado.stdout)

            pdf_filename = filename.replace(".md", ".pdf")
            pdf_filepath = os.path.join("resultados", pdf_filename)
            markdown_to_pdf(filepath, pdf_filepath)

            col1, col2 = st.columns(2)
            with col1:
                st.markdown(
                    get_binary_file_downloader_html(filepath, filename), unsafe_allow_html=True
                )
            with col2:
                st.markdown(
                    get_binary_file_downloader_html(pdf_filepath, pdf_filename),
                    unsafe_allow_html=True,
                )

# Información adicional en el pie de página
st.markdown("---")
st.markdown("**Fabric AI** es un framework de código abierto para aumentar las capacidades humanas mediante IA")