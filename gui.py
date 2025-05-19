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


def get_fabric_options():
    resultado = subprocess.run(["fabric", "-l"], capture_output=True, text=True)
    opciones = [line.strip() for line in resultado.stdout.split("\n") if line.strip()]
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

            if st.sidebar.button(f"Borrar {filename}"):
                os.remove(filepath)
                if os.path.exists(pdf_filepath):
                    os.remove(pdf_filepath)
                st.sidebar.write(f"{filename} y su versión PDF han sido borrados.")

            st.sidebar.write("---")

input_type = st.radio("Selecciona el tipo de entrada:", ["Texto", "YouTube", "URL"])

fabric_options = get_fabric_options()
fabric_command = st.selectbox("Selecciona el comando de Fabric:", fabric_options)

fabric_models = ("gpt-4-0125-preview", "gpt-4o-mini", "claude-3-5-sonnet-20240620")
fabric_modelo = st.radio("Selecciona el Modelo de LLM:", fabric_models)

if "] " in fabric_modelo:
    _, model_name = fabric_modelo.split("] ", 1)
else:
    model_name = fabric_modelo

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

if st.button("Generar contenido"):
    if input_type == "Texto":
        # Aseguramos el prompt para manejar caracteres especiales
        prompt = prompt + '. El texto de la respuesta siempre en español.'
        safe_prompt = shlex.quote(prompt)

        comando = f'echo {safe_prompt} | fabric --pattern {fabric_command} --model {model_name}'

        # Imprimimos el comando
        st.write("Comando a ejecutar:")
        st.write(comando)

        # Ejecutamos el comando usando 'bash' para interpretar el pipe
        resultado = subprocess.run(['bash', '-c', comando], capture_output=True, text=True)
    elif input_type == "YouTube":
        comando = (
            f"fabric -y '{prompt}' --pattern {fabric_command} --model {model_name}"
        )

        st.write("Comando a ejecutar:")
        st.write(comando)

        resultado = subprocess.run(["bash", "-c", comando], capture_output=True, text=True)
    else:  # URL
        comando = (
            f"fabric -u '{prompt}' --pattern {fabric_command} --model {model_name}"
        )

        st.write("Comando a ejecutar:")
        st.write(comando)

        resultado = subprocess.run(["bash", "-c", comando], capture_output=True, text=True)

    if resultado.returncode != 0:
        st.error(f"Error al ejecutar el comando:\n{resultado.stderr}")
    else:
        st.text("Resultado:")
        st.text_area("", value=resultado.stdout, height=300)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"resultado_{timestamp}.md"
        filepath = os.path.join("resultados", filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(resultado.stdout)

        pdf_filename = filename.replace(".md", ".pdf")
        pdf_filepath = os.path.join("resultados", pdf_filename)
        markdown_to_pdf(filepath, pdf_filepath)

        st.markdown(
            get_binary_file_downloader_html(filepath, filename), unsafe_allow_html=True
        )
        st.markdown(
            get_binary_file_downloader_html(pdf_filepath, pdf_filename),
            unsafe_allow_html=True,
        )
