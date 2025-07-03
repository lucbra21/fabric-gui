import streamlit as st
import subprocess
import base64
import os
from datetime import datetime
import re
import shlex  # Importamos shlex para manejar el escape de caracteres
from fpdf import FPDF
import whisper
import tempfile


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


def transcribir_archivo(archivo, modelo="base"):
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(archivo.name)[1]) as temp:
        temp.write(archivo.read())
        temp_path = temp.name
    model = whisper.load_model(modelo)
    result = model.transcribe(temp_path, language="es")
    os.remove(temp_path)
    return result["text"]

def generar_srt(archivo, modelo="base"):
    def format_timestamp(seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds - int(seconds)) * 1000)
        return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(archivo.name)[1]) as temp:
        temp.write(archivo.read())
        temp_path = temp.name
    model = whisper.load_model(modelo)
    result = model.transcribe(temp_path, language="es")
    os.remove(temp_path)
    segments = result.get("segments", [])
    srt_content = ""
    for i, segment in enumerate(segments, 1):
        start = format_timestamp(segment["start"])
        end = format_timestamp(segment["end"])
        text = segment["text"].strip()
        srt_content += f"{i}\n{start} --> {end}\n{text}\n\n"
    return srt_content

def generar_subtitulos_txt(archivo, modelo="base"):
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(archivo.name)[1]) as temp:
        temp.write(archivo.read())
        temp_path = temp.name
    model = whisper.load_model(modelo)
    result = model.transcribe(temp_path, language="es")
    os.remove(temp_path)
    segments = result.get("segments", [])
    txt_content = "\n".join([segment["text"].strip() for segment in segments])
    return txt_content

def format_time(seconds):
    return f"{seconds:.2f} s | {seconds/60:.2f} min | {seconds/3600:.2f} h"

def format_size(bytes_):
    kb = bytes_ / 1024
    mb = kb / 1024
    gb = mb / 1024
    return f"{bytes_:.0f} bytes | {kb:.2f} KB | {mb:.2f} MB | {gb:.4f} GB"


# Diccionario de descripciones en español para los comandos más comunes de Fabric
DESCRIPCIONES_ES = {
    # 1-50
    "agility_story": "Genera historias de usuario y criterios de aceptación en formato JSON",
    "ai": "Interpreta preguntas y proporciona respuestas concisas en formato Markdown",
    "analyze_answers": "Evalúa respuestas de cuestionarios según objetivos de aprendizaje",
    "analyze_candidates": "Compara candidatos políticos basándose en temas y políticas clave",
    "analyze_cfp_submission": "Evalúa propuestas de conferencias según claridad y relevancia",
    "analyze_threat_report_trends": "Extrae tendencias interesantes de informes de amenazas",
    "analyze_claims": "Analiza y califica afirmaciones con evidencias y contraargumentos",
    "analyze_comments": "Evalúa comentarios de internet y categoriza su sentimiento",
    "analyze_debate": "Califica debates y proporciona análisis imparcial de argumentos",
    "analyze_email_headers": "Analiza cabeceras de email para detección de amenazas",
    "analyze_incident": "Extrae detalles clave de informes de brechas de ciberseguridad",
    "analyze_interviewer_techniques": "Analiza técnicas de entrevistadores e identifica cualidades únicas",
    "analyze_logs": "Analiza archivos de registro para identificar patrones y anomalías",
    "analyze_malware": "Analiza detalles de malware y extrae indicadores clave",
    "analyze_military_strategy": "Analiza batallas históricas y ofrece perspectivas estratégicas",
    "analyze_mistakes": "Analiza errores pasados en patrones de pensamiento y mejora predicciones",
    "analyze_paper": "Analiza papers de investigación evaluando rigor y calidad",
    "analyze_patent": "Analiza patentes detallando campo, problema, solución y novedad",
    "analyze_personality": "Realiza análisis psicológico profundo de una persona",
    "analyze_presentation": "Revisa y critica presentaciones analizando contenido y objetivos",
    "analyze_product_feedback": "Analiza y organiza comentarios de usuarios por temas y prioridad",
    "analyze_proposition": "Analiza propuestas electorales identificando propósito e impacto",
    "analyze_prose": "Evalúa escritos por novedad, claridad y prosa con recomendaciones",
    "analyze_prose_json": "Evalúa escritos y proporciona calificaciones en formato JSON",
    "analyze_prose_pinker": "Evalúa prosa basándose en 'The Sense of Style' de Steven Pinker",
    "analyze_risk": "Realiza evaluación de riesgos de proveedores externos",
    "analyze_sales_call": "Califica desempeño de llamadas de ventas con feedback accionable",
    "analyze_spiritual_text": "Compara textos espirituales analizando diferencias con la Biblia",
    "analyze_tech_impact": "Analiza impacto social y consideraciones éticas de proyectos tecnológicos",
    "analyze_threat_report": "Extrae hallazgos relevantes de informes de amenazas de ciberseguridad",
    "analyse_threat_report_cmds": "Extrae comandos de ciberseguridad accionables de materiales",
    
    "answer_interview_question": "Genera respuestas concisas para preguntas de entrevistas técnicas",
    "ask_secure_by_design_questions": "Genera preguntas enfocadas en seguridad para diseño de proyectos",
    "ask_uncle_duke": "Coordina equipo para soluciones de desarrollo y revisiones de código",
    "capture_thinkers_work": "Analiza filósofos y proporciona resúmenes de sus enseñanzas",
    "check_agreement": "Analiza contratos para identificar estipulaciones importantes",
    "clean_text": "Corrige texto con formato incorrecto sin alterar contenido",
    "coding_master": "Explica conceptos de programación para principiantes con ejemplos",
    "compare_and_contrast": "Compara elementos en una tabla markdown estructurada",
    "convert_to_markdown": "Convierte contenido a formato Markdown limpio y completo",
    "create_5_sentence_summary": "Crea resúmenes concisos a diferentes niveles de profundidad",
    "create_academic_paper": "Genera papers académicos de alta calidad en formato LaTeX",
    "create_ai_jobs_analysis": "Analiza susceptibilidad de categorías laborales a la automatización",
    "create_aphorisms": "Encuentra y genera lista de declaraciones breves e ingeniosas",
    "create_art_prompt": "Genera descripciones visuales detalladas para creación artística",
    "create_better_frame": "Identifica diferentes marcos de interpretación de la realidad",
    "create_coding_project": "Genera wireframes y código inicial para ideas de programación",
    "create_command": "Ayuda a determinar parámetros correctos para herramientas de pentesting",
    "create_cyber_summary": "Resume amenazas y vulnerabilidades de ciberseguridad",
    "create_design_document": "Crea documentos de diseño detallados usando el modelo C4",
    
    # 51-100
    "create_diy": "Crea tutoriales estructurados paso a paso en formato Markdown",
    "create_formal_email": "Redacta emails profesionales analizando contexto y propósito",
    "create_git_diff_commit": "Genera comandos Git y mensajes de commit para cambios",
    "create_graph_from_input": "Genera archivo CSV con datos de progreso para programas de seguridad",
    "create_hormozi_offer": "Crea ofertas de negocio basadas en principios de Alex Hormozi",
    "create_idea_compass": "Organiza ideas explorando definición, evidencia y temas relacionados",
    "create_investigation_visualization": "Crea visualizaciones Graphviz detalladas para análisis",
    "create_keynote": "Crea presentaciones estilo TED con narrativa clara y notas",
    "create_logo": "Crea logos de empresa minimalistas sin texto",
    "create_markmap_visualization": "Transforma ideas complejas en visualizaciones usando MarkMap",
    "create_mermaid_visualization": "Crea visualizaciones detalladas usando sintaxis Mermaid",
    "create_mermaid_visualization_for_github": "Crea diagramas Mermaid optimizados para GitHub",
    "create_micro_summary": "Resume contenido en 20 palabras con puntos principales",
    "create_network_threat_landscape": "Analiza puertos y servicios para generar informe de seguridad",
    "create_newsletter_entry": "Condensa artículos en resúmenes concisos estilo newsletter",
    "create_npc": "Genera NPCs detallados para D&D 5E con trasfondo y estadísticas",
    "create_pattern": "Extrae y organiza prompts de IA en secciones estructuradas",
    "create_prd": "Crea Documentos de Requisitos de Producto precisos en Markdown",
    "create_prediction_block": "Extrae y formatea predicciones en bloques estructurados",
    "create_quiz": "Crea plan de lectura en tres fases basado en autor o tema",
    "create_reading_plan": "Genera preguntas de revisión basadas en objetivos de aprendizaje",
    "create_recursive_outline": "Descompone tareas complejas en componentes jerárquicos",
    "create_report_finding": "Crea informes detallados de hallazgos de seguridad en markdown",
    "create_rpg_summary": "Resume sesiones de juegos de rol con eventos y estadísticas clave",
    "create_security_update": "Crea actualizaciones concisas de seguridad para newsletters",
    "create_show_intro": "Crea introducciones breves y atractivas para podcasts",
    "create_sigma_rules": "Extrae TTPs de noticias de seguridad y crea reglas Sigma",
    "create_story_explanation": "Resume contenido complejo en formato narrativo accesible",
    "create_stride_threat_model": "Crea modelo de amenazas STRIDE para diseños de sistemas",
    "create_summary": "Resume contenido en una frase de 20 palabras y puntos principales",
    "create_tags": "Identifica al menos 5 etiquetas de contenido para herramientas de mapeo mental",
    "create_threat_scenarios": "Identifica métodos de ataque probables para cualquier sistema",
    "create_ttrc_graph": "Crea archivo CSV mostrando progreso en tiempos de remediación",
    "create_ttrc_narrative": "Crea narrativa resaltando progreso en métricas de remediación",
    "create_upgrade_pack": "Extrae actualizaciones de modelo y algoritmos de contenido",
    "create_user_story": "Escribe historias de usuario técnicas concisas para nuevas funciones",
    "create_video_chapters": "Extrae temas y marcas de tiempo de transcripciones de video",
    "create_visualization": "Transforma ideas complejas en visualizaciones usando ASCII art",
    "dialog_with_socrates": "Participa en diálogos profundos usando el método socrático",
    "enrich_blog_post": "Mejora archivos de blog aplicando instrucciones para estructura",
    "explain_code": "Explica código, configuraciones y responde preguntas técnicas",
    "explain_docs": "Mejora documentación técnica con estructura e instrucciones claras",
    "explain_math": "Ayuda a entender conceptos matemáticos de manera clara y atractiva",
    "explain_project": "Resume documentación de proyectos en secciones concisas",
    "explain_terms": "Produce glosario de términos avanzados con definiciones y analogías",
    "export_data_as_csv": "Extrae y formatea estructuras de datos en formato CSV",
    "extract_algorithm_update_recommendations": "Extrae recomendaciones prácticas de algoritmos",
    "extract_article_wisdom": "Extrae información sorprendente y útil categorizada por secciones",
    "extract_book_ideas": "Extrae 50-100 ideas interesantes de contenido de libros",
    "extract_book_recommendations": "Extrae 50-100 recomendaciones prácticas de libros",
    
    # 101-150
    "extract_business_ideas": "Extrae ideas de negocio y elabora las 10 mejores",
    "extract_controversial_ideas": "Extrae declaraciones controvertidas con citas de apoyo",
    "extract_core_message": "Extrae mensaje central conciso de un texto",
    "extract_ctf_writeup": "Extrae resumen de experiencias en competiciones de ciberseguridad",
    "extract_extraordinary_claims": "Extrae afirmaciones extraordinarias de conversaciones",
    "extract_ideas": "Extrae ideas clave en formato de viñetas de 15 palabras",
    "extract_insights": "Extrae ideas poderosas formateadas como viñetas de 16 palabras",
    "extract_insights_dm": "Extrae perspectivas valiosas y resumen de contenido",
    "extract_instructions": "Extrae instrucciones paso a paso de transcripciones de videos",
    "extract_jokes": "Extrae chistes de contenido presentando cada uno con su remate",
    "extract_latest_video": "Extrae URL del último video de un feed RSS de YouTube",
    "extract_main_idea": "Extrae idea principal y recomendación clave en 15 palabras",
    "extract_most_redeeming_thing": "Extrae el aspecto más meritorio en una frase de 15 palabras",
    "extract_patterns": "Extrae y analiza patrones recurrentes con consejos para creadores",
    "extract_poc": "Extrae URLs de prueba de concepto y métodos de validación",
    "extract_predictions": "Extrae predicciones incluyendo fecha y nivel de confianza",
    "extract_primary_problem": "Extrae problema principal presentado en un texto",
    "extract_primary_solution": "Extrae solución principal presentada en un texto",
    "extract_product_features": "Extrae lista de características de producto en formato de viñetas",
    "extract_questions": "Extrae todas las preguntas realizadas por el entrevistador",
    "extract_recipe": "Extrae receta con descripción, ingredientes y pasos de preparación",
    "extract_recommendations": "Extrae recomendaciones prácticas de contenido en lista",
    "extract_references": "Extrae referencias a obras, libros y otras fuentes de contenido",
    "extract_skills": "Extrae y clasifica habilidades de descripciones de trabajo",
    "extract_song_meaning": "Analiza canciones para proporcionar resumen de su significado",
    "extract_sponsors": "Extrae y lista patrocinadores oficiales y potenciales",
    "extract_videoid": "Extrae ID de video de cualquier URL dada",
    "extract_wisdom": "Extrae información valiosa sobre desarrollo humano, IA y aprendizaje",
    "extract_wisdom_agents": "Extrae perspectivas, ideas y citas valiosas de contenido",
    "extract_wisdom_dm": "Extrae información valiosa y estimulante sobre varios temas",
    "extract_wisdom_nometa": "Extrae ideas, citas y recomendaciones sin metadatos",
    "find_hidden_message": "Extrae mensajes políticos ocultos y análisis cínico de contenido",
    "find_logical_fallacies": "Identifica y analiza falacias en argumentos con razonamiento detallado",
    "get_wow_per_minute": "Determina factor de asombro de contenido por minuto",
    "get_youtube_rss": "Devuelve URL de RSS para un canal de YouTube",
    "humanize": "Reescribe texto generado por IA para que suene natural y conversacional",
    "identify_dsrp_distinctions": "Fomenta pensamiento creativo explorando distinciones",
    "identify_dsrp_perspectives": "Explora concepto de distinciones en pensamiento sistémico",
    "identify_dsrp_relationships": "Fomenta exploración de conexiones entre ideas",
    "identify_dsrp_systems": "Fomenta organización de ideas en sistemas de partes",
    "identify_job_stories": "Identifica historias de trabajo o requisitos para roles",
    "improve_academic_writing": "Refina texto académico mejorando gramática y coherencia",
    "improve_prompt": "Mejora prompts de IA aplicando estrategias expertas",
    "improve_report_finding": "Mejora hallazgos de pruebas de penetración con detalles",
    "improve_writing": "Refina texto corrigiendo gramática y mejorando estilo",
    "judge_output": "Evalúa consultas analizando efectividad y relevancia",
    "label_and_rate": "Etiqueta contenido con palabras clave y califica su calidad",
    "md_callout": "Clasifica contenido y genera señalizaciones markdown apropiadas",
    "official_pattern_template": "Plantilla para crear nuevos patrones de fabric",
    
    # 151-206
    "prepare_7s_strategy": "Prepara documento estratégico completo capturando perfil organizacional",
    "provide_guidance": "Proporciona asesoramiento psicológico y coaching de vida",
    "rate_ai_response": "Califica calidad de respuestas de IA comparando con expertos humanos",
    "rate_ai_result": "Evalúa calidad de trabajo de IA analizando contenido e instrucciones",
    "rate_content": "Etiqueta contenido con palabras clave y califica según relevancia",
    "rate_value": "Produce mejor resultado posible analizando profundamente la entrada",
    "raw_query": "Digiere y contempla la entrada para producir el mejor resultado posible",
    "raycast": "Scripts para Raycast (requiere Raycast AI Pro)",
    "recommend_artists": "Recomienda agenda personalizada de festival con artistas afines",
    "recommend_pipeline_upgrades": "Optimiza pipelines de verificación de vulnerabilidades",
    "recommend_talkpanel_topics": "Produce propuestas de charlas basadas en intereses",
    "refine_design_document": "Refina documento de diseño basado en revisiones",
    "review_design": "Revisa y analiza diseño arquitectónico enfocándose en claridad",
    "sanitize_broken_html_to_markdown": "Convierte HTML desordenado en Markdown limpio",
    "show_fabric_options_markmap": "Visualiza funcionalidad del framework Fabric",
    "solve_with_cot": "Proporciona respuestas detalladas con razonamiento paso a paso",
    "suggest_pattern": "Sugiere patrones de fabric apropiados según entrada del usuario",
    "summarize": "Resume contenido en frase de 20 palabras y puntos principales",
    "summarize_debate": "Resume debates identificando desacuerdos y argumentos principales",
    "summarize_git_changes": "Resume actualizaciones recientes de proyecto con entusiasmo",
    "summarize_git_diff": "Resume cambios de Git con mensajes de commit concisos",
    "summarize_lecture": "Extrae temas relevantes de transcripciones de conferencias",
    "summarize_legislation": "Resume propuestas políticas complejas y legislación",
    "summarize_meeting": "Analiza transcripciones de reuniones extrayendo resumen estructurado",
    "summarize_micro": "Resume contenido en frase de 20 palabras y puntos principales",
    "summarize_newsletter": "Extrae contenido significativo de newsletters en formato estructurado",
    "summarize_paper": "Resume paper académico detallando título, autores y enfoque",
    "summarize_prompt": "Resume prompts de IA describiendo función y enfoque",
    "summarize_pull-requests": "Resume pull requests para proyecto de código",
    "summarize_rpg_session": "Resume sesión de juego de rol extrayendo eventos clave",
    "t_analyse_challenge_handling": "Evalúa cómo se están abordando los desafíos",
    "t_check_metrics": "Analiza contexto y proporciona análisis basado en métricas",
    "t_create_h3_career": "Resume contexto y produce salida basada en sabiduría",
    "t_create_opening_sentences": "Describe identidad, metas y acciones en viñetas concisas",
    "t_describe_life_outlook": "Describe perspectiva de vida en viñetas concisas",
    "t_extract_intro_sentences": "Resume identidad, trabajo y proyectos en viñetas concisas",
    "t_extract_panel_topics": "Crea ideas para paneles con títulos y descripciones",
    "t_find_blindspots": "Identifica puntos ciegos en pensamiento y modelos",
    "t_find_negative_thinking": "Analiza para identificar pensamiento negativo en documentos",
    "t_find_neglected_goals": "Identifica metas o proyectos desatendidos recientemente",
    "t_give_encouragement": "Evalúa progreso, proporciona ánimo y ofrece recomendaciones",
    "t_red_team_thinking": "Evalúa críticamente pensamiento y proporciona recomendaciones",
    "t_threat_model_plans": "Crea modelos de amenazas para planes de vida",
    "t_visualize_mission_goals_projects": "Crea diagrama ASCII ilustrando relación de misiones y metas",
    "t_year_in_review": "Analiza para crear perspectivas y resumir logros anuales",
    "to_flashcards": "Crea tarjetas Anki de un texto con preguntas y respuestas concisas",
    "transcribe_minutes": "Extrae actas de reuniones identificando acciones e ideas",
    "translate": "Traduce textos al idioma especificado manteniendo formato original",
    "tweet": "Guía paso a paso para crear tweets atractivos con emojis",
    "write_essay": "Escribe ensayos concisos al estilo de Paul Graham",
    "write_hackerone_report": "Genera informes de bug bounty detallando vulnerabilidades",
    "write_latex": "Genera código LaTeX sintácticamente correcto para documentos",
    "write_micro_essay": "Escribe ensayos concisos e iluminadores al estilo Paul Graham",
    "write_nuclei_template_rule": "Genera plantillas YAML Nuclei para detectar vulnerabilidades",
    "write_pull-request": "Redacta descripciones detalladas de pull requests",
    "write_semgrep_rule": "Crea reglas Semgrep precisas basadas en entrada",
    "youtube_summary": "Crea resúmenes concisos de videos de YouTube con marcas de tiempo",
    
    # Comandos adicionales que podrían no estar en la lista pero son útiles incluir
    "analyze_code": "Analiza código y sugiere mejoras específicas",
    "analyze_interview": "Evalúa entrevistas identificando puntos fuertes y áreas de mejora",
    "create_course": "Desarrolla estructura y contenido completo para cursos educativos",
    "extract_entities": "Identifica y clasifica entidades nombradas en el texto",
    "convert_code": "Traduce código entre diferentes lenguajes de programación",
    "evaluate_security": "Evalúa configuraciones de seguridad e identifica vulnerabilidades",
    "create_infographic": "Genera estructura para infografías informativas sobre cualquier tema",
    "generate_test_cases": "Crea casos de prueba exhaustivos para software",
    "simplify": "Convierte texto complejo en explicaciones sencillas y accesibles",
    "optimize_seo": "Mejora contenido para motores de búsqueda manteniendo calidad",
}


@st.cache_data(ttl=3600)  # Cache por una hora
def get_fabric_options():
    """Obtiene las opciones de comandos de Fabric."""
    resultado = subprocess.run(["fabric", "-l"], capture_output=True, text=True)
    opciones = [line.strip() for line in resultado.stdout.split("\n") if line.strip()]
    # Filtrar para obtener solo comandos válidos (eliminar encabezados)
    opciones = [opt for opt in opciones if not opt.startswith("Available") and not opt.startswith("==")]
    return opciones


def get_fabric_options_with_descriptions():
    """Obtiene los comandos de Fabric con descripciones en español."""
    comandos = get_fabric_options()
    opciones_con_descripcion = []
    
    for cmd in comandos:
        if cmd in DESCRIPCIONES_ES:
            # Añadir comando con descripción entre paréntesis
            opciones_con_descripcion.append(f"{cmd} ({DESCRIPCIONES_ES[cmd]})")
        else:
            # Para comandos sin descripción, solo añadir el nombre
            opciones_con_descripcion.append(cmd)
    
    return opciones_con_descripcion


def extract_command(option_text):
    """Extrae el comando real (sin descripción) de la opción seleccionada."""
    if " (" in option_text:
        return option_text.split(" (")[0]
    return option_text


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

# Menú de navegación en la barra lateral
menu_opcion = st.sidebar.radio(
    "Menú Principal:",
    ["Fabric", "Trascripción"],
    index=0
)


# Mostrar contenido según la opción del menú
if menu_opcion == "Fabric":
    
    # Mostrar opciones de archivos generados en la barra lateral
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

    # Obtener opciones de Fabric con descripciones
    fabric_options_with_desc = get_fabric_options_with_descriptions()

    # Mostrar desplegable con comandos y descripciones
    selected_option = st.selectbox("Selecciona el comando de Fabric:", fabric_options_with_desc)

    # Extraer el comando real (sin la descripción)
    fabric_command = extract_command(selected_option)

    # Selección de modelo
    fabric_models = ("gpt-4o-mini", "gpt-4-0125-preview", "claude-3-5-sonnet-20240620")
    fabric_modelo = st.radio("Selecciona el Modelo de LLM:", fabric_models)

    if "] " in fabric_modelo:
        _, model_name = fabric_modelo.split("] ", 1)
    else:
        model_name = fabric_modelo

    # Entradas según tipo seleccionado
    if menu_opcion == "Fabric":
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


    st.write("📝 La respuesta siempre será en español gracias al parámetro `--language=es`")

    if st.button("Generar contenido"):
        with st.spinner("Generando contenido con Fabric... esto puede tomar un momento"):
            if input_type == "Texto":
                # Aseguramos el prompt para manejar caracteres especiales
                safe_prompt = shlex.quote(prompt)
                comando = f'echo {safe_prompt} | fabric --pattern {fabric_command} --model {model_name} --language=es'
                st.code(comando, language="bash")
                # Ejecutamos el comando usando 'bash' para interpretar el pipe
                resultado = subprocess.run(['bash', '-c', comando], capture_output=True, text=True)
            
            elif input_type == "YouTube":
                comando = f"fabric -y '{prompt}' --pattern {fabric_command} --model {model_name} --language=es"
                st.code(comando, language="bash")
                resultado = subprocess.run(["bash", "-c", comando], capture_output=True, text=True)
            
            else:  # URL
                comando = f"fabric -u '{prompt}' --pattern {fabric_command} --model {model_name} --language=es"
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
                        get_binary_file_downloader_html(filepath, filename), 
                        unsafe_allow_html=True
                    )
                with col2:
                    st.markdown(
                        get_binary_file_downloader_html(pdf_filepath, pdf_filename),
                        unsafe_allow_html=True,
                    )

# Mostrar contenido del módulo de Trascripción
if menu_opcion == "Trascripción":
    st.title("Transcriptor de Audio/Video con Whisper")

    st.write("Sube un archivo de audio o video (mp3, wav, mp4, etc.) y descarga la transcripción en texto.")

    archivo = st.file_uploader("Selecciona tu archivo", type=["mp3", "wav", "mp4", "m4a", "ogg", "flac"])

    if archivo is not None:
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Transcribir"):
                import time
                start_time = time.time()
                with st.spinner("Transcribiendo, esto puede tardar unos minutos..."):
                    texto = transcribir_archivo(archivo)
                elapsed = time.time() - start_time
                st.success("¡Transcripción completada!")
                st.text_area("Transcripción", texto, height=300)
                st.download_button(
                    label="Descargar transcripción",
                    data=texto,
                    file_name=f"{os.path.splitext(archivo.name)[0]}_transcripcion.txt",
                    mime="text/plain"
                )
                # Estadísticas
                st.markdown("**Estadísticas de transcripción:**")
                st.write(f"- Tiempo de procesamiento: {format_time(elapsed)}")
                st.write(f"- Peso del archivo de entrada: {format_size(archivo.size)}")
                st.write(f"- Tamaño del archivo de salida: {format_size(len(texto.encode('utf-8')))}")
                st.write(f"- Cantidad de líneas: {len(texto.splitlines())}")
                # Duración del audio/video
                try:
                    import whisper
                    import tempfile
                    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(archivo.name)[1]) as temp:
                        temp.write(archivo.getvalue())
                        temp_path = temp.name
                    model = whisper.load_model("base")
                    result = model.transcribe(temp_path, language="es")
                    st.write(f"- Duración del audio/video: {format_time(result['duration'])}")
                    os.remove(temp_path)
                except Exception:
                    pass

        with col2:
            if st.button("Generar subtítulos SRT"):
                import time
                start_time = time.time()
                with st.spinner("Generando subtítulos, esto puede tardar unos minutos..."):
                    srt_content = generar_srt(archivo)
                elapsed = time.time() - start_time
                st.success("¡Subtítulos SRT generados!")
                st.download_button(
                    label="Descargar subtítulos SRT",
                    data=srt_content,
                    file_name=f"{os.path.splitext(archivo.name)[0]}.srt",
                    mime="text/plain"
                )
                # Estadísticas
                st.markdown("**Estadísticas de subtítulos SRT:**")
                st.write(f"- Tiempo de procesamiento: {format_time(elapsed)}")
                st.write(f"- Peso del archivo de entrada: {format_size(archivo.size)}")
                st.write(f"- Tamaño del archivo de salida: {format_size(len(srt_content.encode('utf-8')))}")
                st.write(f"- Cantidad de líneas: {len(srt_content.splitlines())}")
                # Duración del audio/video
                try:
                    import whisper
                    import tempfile
                    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(archivo.name)[1]) as temp:
                        temp.write(archivo.getvalue())
                        temp_path = temp.name
                    model = whisper.load_model("base")
                    result = model.transcribe(temp_path, language="es")
                    st.write(f"- Duración del audio/video: {format_time(result['duration'])}")
                    os.remove(temp_path)
                except Exception:
                    pass

        with col3:
            if st.button("Generar subtítulos TXT"):
                import time
                start_time = time.time()
                with st.spinner("Generando subtítulos TXT, esto puede tardar unos minutos..."):
                    txt_content = generar_subtitulos_txt(archivo)
                elapsed = time.time() - start_time
                st.success("¡Subtítulos TXT generados!")
                st.download_button(
                    label="Descargar subtítulos TXT",
                    data=txt_content,
                    file_name=f"{os.path.splitext(archivo.name)[0]}_subtitulos.txt",
                    mime="text/plain"
                )
                # Estadísticas
                st.markdown("**Estadísticas de subtítulos TXT:**")
                st.write(f"- Tiempo de procesamiento: {format_time(elapsed)}")
                st.write(f"- Peso del archivo de entrada: {format_size(archivo.size)}")
                st.write(f"- Tamaño del archivo de salida: {format_size(len(txt_content.encode('utf-8')))}")
                st.write(f"- Cantidad de líneas: {len(txt_content.splitlines())}")
                # Duración del audio/video
                try:
                    import whisper
                    import tempfile
                    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(archivo.name)[1]) as temp:
                        temp.write(archivo.getvalue())
                        temp_path = temp.name
                    model = whisper.load_model("base")
                    result = model.transcribe(temp_path, language="es")
                    st.write(f"- Duración del audio/video: {format_time(result['duration'])}")
                    os.remove(temp_path)
                except Exception:
                    pass

# Información adicional en el pie de página
st.markdown("---")
st.markdown("**Fabric AI** es un framework de código abierto para aumentar las capacidades humanas mediante IA")