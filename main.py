import os
from dotenv import load_dotenv
load_dotenv()
import os
import re
import json
import html
import difflib
import unicodedata
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string, send_file, Response
from flask_cors import CORS
from google import genai
from google.genai import types

app = Flask(__name__)
CORS(app)

API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY, http_options={'api_version': 'v1beta'})

ARCHIVO_CONOCIMIENTO = "conocimiento_funcionario.json"
ARCHIVO_ESTADISTICAS = "estadisticas_teinco.json"
ARCHIVO_CHATS = "chats_guardados.json"
ADMIN_USER = "admin"
ADMIN_PASS = "teinco2026"
ADMIN_TOKEN = "TOKEN_TEINCO_2026_OK"

CONTEXTO_TEINCO_REAL = '''
Eres AsistIA, el asistente virtual oficial de TEINCO en Bogotá y Mosquera. Responde en máximo 3 líneas con tono amable y profesional:
- Ciclos propedéuticos: 3 títulos oficiales (Técnico Profesional Sem. 1-4, Tecnólogo Sem. 5-6, Profesional Universitario Sem. 7-9). Modalidad 95% presencial.
- Inglés por ciclo: Técnico A1, Tecnólogo A2, Profesional B1 (Módulo Carreras: carreras.modulo@teinco.edu.co).
- 4 modalidades de grado: prácticas, pasantías, validación por experiencia y proyecto de grado (Registro y Control: registro.control@teinco.edu.co).
- Tarifas semestrales 2027: Ingenierías ($1500/$2200/$3200 USD), Administrativas y Creativas ($1400/$2000/$3000 USD), Técnicos Laborales ($1500 USD, 2 semestres).
- Métodos de pago: Tarjeta o PSE. No hay financiación directa, pero pueden solicitar crédito por banco. Descuentos se tramitan con Registro y Control.
- Horario atención directa sede principal Bogotá: Lunes a viernes 8:00 a.m. a 5:00 p.m. y sábados 8:00 a.m. a 12:00 m.
'''

CARRERAS_INFO = {
    "sistemas": {
        "nombre": "Profesional en Ingeniería de Sistemas", "sedes": "Bogotá – Mosquera", "duracion": "9 Semestres", "precios": ["$1500 USD", "$2200 USD", "$3200 USD"],
        "descripcion": "Formación integral en desarrollo de software multiplataforma, bases de datos, arquitectura de sistemas, redes, nube y ciberseguridad bajo ciclos propedéuticos (95% presencial).",
        "logros": "Desde los primeros semestres como Técnico y Tecnólogo podrás vincularte rápidamente a la industria tecnológica como desarrollador junior o analista de soporte. Al culminar tu ciclo Profesional, tendrás la capacidad de diseñar arquitecturas de software escalables, liderar equipos de desarrollo web y móvil, gestionar infraestructura en la nube e implementar soluciones de inteligencia artificial y ciberseguridad en empresas nacionales e internacionales, o fundar tu propia startup."
    },
    "mecatronica": {
        "nombre": "Profesional en Ingeniería Mecatrónica", "sedes": "Bogotá", "duracion": "9 Semestres", "precios": ["$1600 USD", "$2300 USD", "$3300 USD"],
        "descripcion": "Integra mecánica de precisión, electrónica, control automático, robótica e informática industrial bajo ciclos propedéuticos (95% presencial).",
        "logros": "A medida que avanzas en tus ciclos Técnico y Tecnólogo podrás desempeñarte en mantenimiento electrónico y automatización de plantas. Como Profesional en Ingeniería Mecatrónica diseñarás sistemas robóticos inteligentes, optimizarás líneas de producción industrial, programarás maquinaria CNC y liderarás proyectos de innovación tecnológica e industria 4.0 en el sector manufacturero y energético."
    },
    "marketing": {
        "nombre": "Profesional en Marketing y Negocios Digitales", "sedes": "Bogotá", "duracion": "8 Semestres", "precios": ["$1400 USD", "$2000 USD", "$2900 USD"],
        "descripcion": "Estrategias comerciales digitales, analítica de mercados, posicionamiento de marca y comercio electrónico bajo ciclos propedéuticos (95% presencial).",
        "logros": "Desde tu etapa Técnica y Tecnológica podrás gestionar campañas en redes sociales, tráfico digital y tiendas virtuales. Al graduarte como Profesional dirigirás estrategias globales de crecimiento comercial, liderarás departamentos de e-commerce y analítica de datos, gestionarás grandes marcas y desarrollarás modelos de negocio digitales de alto impacto."
    },
    "administracion": {
        "nombre": "Profesional en Administración de Empresas", "sedes": "Bogotá – Mosquera", "duracion": "9 Semestres", "precios": ["$1400 USD", "$2000 USD", "$3000 USD"],
        "descripcion": "Desarrollo de habilidades gerenciales, financieras, de talento humano, logística y emprendimiento bajo ciclos propedéuticos (95% presencial).",
        "logros": "Durante tus ciclos Técnico y Tecnólogo podrás coordinar procesos administrativos, operativos y de talento humano en organizaciones de cualquier sector. Al alcanzar tu título Profesional estarás preparado para gerenciar compañías, liderar proyectos de inversión y expansión, optimizar recursos financieros y consolidar tu propia empresa con visión estratégica."
    },
    "contaduria": {
        "nombre": "Profesional en Contaduría Pública", "sedes": "Bogotá – Mosquera", "duracion": "9 Semestres", "precios": ["$1400 USD", "$2000 USD", "$3000 USD"],
        "descripcion": "Dominio de Normas Internacionales (NIIF), auditoría financiera, planeación tributaria y control fiscal bajo ciclos propedéuticos (95% presencial).",
        "logros": "En tus etapas Técnica y Tecnológica podrás desempeñarte como asistente contable, analista tributario y gestor de nómina o costos. Como Contador Público Profesional ejercerás como revisor fiscal, auditor externo, consultor financiero y tributario o director contable de grandes corporaciones, garantizando la transparencia y solidez económica de las empresas."
    },
    "diseno": {
        "nombre": "Profesional en Diseño Digital Publicitario", "sedes": "Bogotá", "duracion": "8 Semestres", "precios": ["$1400 USD", "$2000 USD", "$2950 USD"],
        "descripcion": "Comunicación visual estratégica, ilustración digital, animación multimedia y diseño de experiencias digitales bajo ciclos propedéuticos (95% presencial).",
        "logros": "Desde tus ciclos Técnico y Tecnólogo podrás trabajar en agencias creativas desarrollando piezas gráficas, contenido audiovisual e identidad visual. Al culminar tu ciclo Profesional liderarás dirección de arte, diseñarás interfaces digitales UX/UI, producirás campañas publicitarias transmedia y dirigirás estudios de comunicación visual."
    }
}
def cargar_chats():
    if not os.path.exists(ARCHIVO_CHATS):
        datos = {"bot_activo": True, "sesiones": {}}
        guardar_chats(datos)
        return datos
    with open(ARCHIVO_CHATS, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_chats(datos):
    with open(ARCHIVO_CHATS, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)

def agregar_mensaje_sesion(session_id, rol, autor, texto, modulo="", chips=None):
    datos = cargar_chats()
    sesiones = datos.setdefault("sesiones", {})
    if session_id not in sesiones:
        sesiones[session_id] = {
            "id": session_id,
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "mensajes": []
        }
    sesiones[session_id]["mensajes"].append({
        "rol": rol,
        "autor": autor,
        "texto": texto,
        "modulo": modulo,
        "chips": chips or [],
        "hora": datetime.now().strftime("%H:%M")
    })
    guardar_chats(datos)

def cargar_estadisticas():
    if not os.path.exists(ARCHIVO_ESTADISTICAS):
        est = {"total_preguntas": 0, "no_contestadas": 0, "preguntas_frecuentes": {}, "lista_desconocidas": []}
        guardar_estadisticas(est)
        return est
    with open(ARCHIVO_ESTADISTICAS, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_estadisticas(est):
    with open(ARCHIVO_ESTADISTICAS, "w", encoding="utf-8") as f:
        json.dump(est, f, ensure_ascii=False, indent=4)

def registrar_evento_estadistica(tipo, modulo="", pregunta=""):
    if tipo != "pregunta" or not pregunta:
        return
    est = cargar_estadisticas()
    est["total_preguntas"] += 1
    clave_p = pregunta.lower().strip()[:70]
    est.setdefault("preguntas_frecuentes", {})
    est["preguntas_frecuentes"][clave_p] = est["preguntas_frecuentes"].get(clave_p, 0) + 1

    if "Contingencia" in modulo:
        est["no_contestadas"] += 1
        est.setdefault("lista_desconocidas", []).insert(0, pregunta[:90])
        est["lista_desconocidas"] = est["lista_desconocidas"][:10]
    guardar_estadisticas(est)

def cargar_conocimiento_extra():
    if not os.path.exists(ARCHIVO_CONOCIMIENTO):
        datos_iniciales = [
            {"pregunta": "que niveles de ingles cursos idioma extranjero exigen", "respuesta": "Dentro de tu formación académica en cada ciclo debes cursar o acreditar suficiencia en inglés según el MCER:<br>• <b>Ciclo Técnico Profesional (Sem. 1-4):</b> Nivel <b>A1</b><br>• <b>Ciclo Tecnólogo (Sem. 5-6):</b> Nivel <b>A2</b><br>• <b>Ciclo Profesional Universitario (Sem. 7-9):</b> Nivel <b>B1</b><br><br>Si pierdes un nivel de inglés, debes presentar y aprobar su recuperación ya que es un requisito obligatorio de grado. Consulta en: <b>carreras.modulo@teinco.edu.co</b>"},
            {"pregunta": "pensum plan de estudios malla curricular materias modalidad presencial", "respuesta": "Nuestros programas se dictan en <b>modalidad 95% presencial</b> (con apoyo de plataforma digital EduVirtual). El pensum reúne las materias por ciclos propedéuticos; solicita la malla detallada de tu carrera en: <b>carreras.modulo@teinco.edu.co</b>"},
            {"pregunta": "que tecnicos laborales auxiliares ofrecen", "respuesta": "Ofrecemos programas Técnicos Laborales Auxiliares (2 semestres, tarifa vigente 2027 de <b>$1500 USD</b>) en Mercadeo Social Media, Administrativo, Sistemas de Información y Automatización Industrial. Info en: <b>carreras.modulo@teinco.edu.co</b>"}
        ]
        with open(ARCHIVO_CONOCIMIENTO, "w", encoding="utf-8") as f:
            json.dump(datos_iniciales, f, ensure_ascii=False, indent=4)
        return datos_iniciales
    with open(ARCHIVO_CONOCIMIENTO, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_conocimiento_extra(pregunta, respuesta, indice_editar=None):
    datos = cargar_conocimiento_extra()
    if indice_editar is not None and 0 <= indice_editar < len(datos):
        datos[indice_editar] = {"pregunta": pregunta.lower().strip(), "respuesta": respuesta.strip()}
    else:
        datos.append({"pregunta": pregunta.lower().strip(), "respuesta": respuesta.strip()})
    with open(ARCHIVO_CONOCIMIENTO, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)

def eliminar_conocimiento_extra(indice):
    datos = cargar_conocimiento_extra()
    if 0 <= indice < len(datos):
        datos.pop(indice)
        with open(ARCHIVO_CONOCIMIENTO, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=4)
def obtener_prefijo_cortesia(es_primer_mensaje, indice_rotacion):
    if es_primer_mensaje:
        return "¡Qué bueno tenerte por aquí! Nos alegra mucho tu interés en <b>TEINCO</b>. Con mucho gusto te ayudo:<br><br>"
    return ""

def normalizar_fonetica(texto):
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto.lower()) if unicodedata.category(c) != 'Mn')
    texto = (texto
             .replace('ce', 'se').replace('ci', 'si').replace('z', 's')
             .replace('v', 'b')
             .replace('ll', 'y')
             .replace('qu', 'c').replace('k', 'c')
             .replace('h', ''))
    texto = re.sub(r'(.)\1+', r'\1', texto)
    return texto

def contiene_intencion(texto, palabras_clave):
    texto_norm = normalizar_fonetica(texto)
    palabras_norm = [normalizar_fonetica(p) for p in palabras_clave]
    for palabra in texto_norm.split():
        if len(palabra) >= 4 and difflib.get_close_matches(palabra, palabras_norm, n=1, cutoff=0.84):
            return True
    return False

def detectar_carrera(texto):
    texto_norm = normalizar_fonetica(texto)
    frases_carreras = {
        "sistemas": ["ingenieria de sistemas", "ingenieria en sistemas", "desarrollo de software"],
        "mecatronica": ["ingenieria mecatronica", "ingenieria en mecatronica", "automatizacion industrial"],
        "marketing": ["marketing y negocios digitales", "marketing digital", "negocios digitales"],
        "administracion": ["administracion de empresas", "gestion empresarial"],
        "contaduria": ["contaduria publica", "contabilidad y finanzas"],
        "diseno": ["diseno digital publicitario", "diseno digital", "diseno grafico"]
    }
    for clave, lista_frases in frases_carreras.items():
        for frase in lista_frases:
            if normalizar_fonetica(frase) in texto_norm:
                return clave

    sinonimos = {
        "sistemas": ["sistemas", "software", "programacion", "programar", "computacion", "desarrollo", "codigo", "informatica", "ciberseguridad"],
        "mecatronica": ["mecatronica", "robots", "robotica", "automatizacion", "electronica", "mecanica", "maquinaria", "cnc"],
        "marketing": ["marketing", "mercadeo", "ecommerce", "ventas", "redes", "comercial", "publicidad"],
        "administracion": ["administracion", "empresas", "gerencia", "gerenciar", "negocio", "emprendimiento", "finanzas"],
        "contaduria": ["contaduria", "contabilidad", "contador", "impuestos", "auditoria", "fiscal", "niif", "tributaria"],
        "diseno": ["diseno", "publicitario", "grafico", "multimedia", "ilustracion", "animacion", "marca"]
    }
    for clave, variantes in sinonimos.items():
        if contiene_intencion(texto, variantes):
            return clave
    return None

def detectar_semestre_y_ciclo(texto):
    mapa_palabras = {
        "primer": 1, "primero": 1, "segundo": 2, "tercer": 3, "tercero": 3,
        "cuarto": 4, "quinto": 5, "sexto": 6, "septimo": 7, "séptimo": 7,
        "octavo": 8, "noveno": 9
    }
    num_semestre = None
    for palabra, numero in mapa_palabras.items():
        if palabra in texto:
            num_semestre = numero
            break
    if not num_semestre:
        match = re.search(r'\b([1-9])\b', texto)
        if match:
            num_semestre = int(match.group(1))

    if num_semestre in (1, 2, 3, 4) or contiene_intencion(texto, ["tecnico", "técnico"]):
        etiqueta = f"Semestre {num_semestre} (Ciclo Técnico Profesional)" if num_semestre else "Ciclo Técnico Profesional"
        return 0, etiqueta, num_semestre
    if num_semestre in (5, 6) or contiene_intencion(texto, ["tecnologo", "tecnólogo"]):
        etiqueta = f"Semestre {num_semestre} (Ciclo Tecnólogo)" if num_semestre else "Ciclo Tecnólogo"
        return 1, etiqueta, num_semestre
    if num_semestre in (7, 8, 9) or contiene_intencion(texto, ["profesional", "universitario"]):
        etiqueta = f"Semestre {num_semestre} (Ciclo Profesional Universitario)" if num_semestre else "Ciclo Profesional Universitario"
        return 2, etiqueta, num_semestre
    return None, None, None
def tabla_precios(clave=None, texto_original=""):
    indice_ciclo, nombre_semestre, num_semestre = detectar_semestre_y_ciclo(texto_original)

    if clave in ("marketing", "diseno") and num_semestre == 9:
        c = CARRERAS_INFO[clave]
        return f"La carrera <b>{c['nombre']}</b> tiene una duración total de <b>8 semestres</b>, por lo que no cuenta con noveno semestre.<br><br>Más info en: <b>carreras.modulo@teinco.edu.co</b>", ["Precios de esta carrera", "Otras carreras", "⬅️ Volver al menú"]

    if clave and clave in CARRERAS_INFO and indice_ciclo is not None:
        c = CARRERAS_INFO[clave]
        return f"Tarifas semestrales vigentes para 2027: para <b>{c['nombre']}</b>, el <b>{nombre_semestre}</b> tiene un valor de <b>{c['precios'][indice_ciclo]}</b>.<br><br>Más info en: <b>carreras.modulo@teinco.edu.co</b>", [f"De qué trata {c['nombre']}", "Horarios de estudio", "Métodos de pago", "⬅️ Volver al menú"]

    if clave and clave in CARRERAS_INFO:
        c = CARRERAS_INFO[clave]
        p_tec, p_tecnol, p_prof = c['precios']
        msg = (
            f"<b>{c['nombre']}</b> maneja las siguientes tarifas semestrales vigentes para 2027 según el ciclo propedéutico:<br>"
            f"• <b>Ciclo Técnico Profesional (Sem. 1 al 4):</b> {p_tec}<br>"
            f"• <b>Ciclo Tecnólogo (Sem. 5 al 6):</b> {p_tecnol}<br>"
            f"• <b>Ciclo Profesional Universitario (Sem. 7 al 9):</b> {p_prof}<br><br>"
            "Más info en: <b>carreras.modulo@teinco.edu.co</b>"
        )
        return msg, [f"De qué trata {c['nombre']}", "Horarios de estudio", "Métodos de pago", "⬅️ Volver al menú"]

    filas = ""
    for c in CARRERAS_INFO.values():
        p_tec, p_tecnol, p_prof = c['precios']
        filas += f"<tr><td>{c['nombre']}</td><td>{p_tec}</td><td>{p_tecnol}</td><td>{p_prof}</td></tr>"
    filas += "<tr><td>Técnicos Laborales Auxiliares (2 Sem.)</td><td>$1500 USD</td><td>N/A</td><td>N/A</td></tr>"
    msg = f"<p>Aquí tienes la tabla de <b>tarifas semestrales vigentes para 2027</b> de todas nuestras carreras:</p><table class='tabla-precios'><thead><tr><th>Programa</th><th>Técnico (1-4)</th><th>Tecnólogo (5-6)</th><th>Profesional (7-9)</th></tr></thead><tbody>{filas}</tbody></table><p style='margin-top:8px;'>Más info en: <b>carreras.modulo@teinco.edu.co</b></p>"
    return msg, ["Métodos de pago", "Descuentos y financiación", "Horarios de estudio", "⬅️ Volver al menú"]

def contar_puntos(texto_fon, frases, palabras):
    puntos = 0
    for f in frases:
        if normalizar_fonetica(f) in texto_fon:
            puntos += 3
    palabras_norm = [normalizar_fonetica(p) for p in palabras]
    for palabra_u in texto_fon.split():
        if len(palabra_u) >= 4 and difflib.get_close_matches(palabra_u, palabras_norm, n=1, cutoff=0.84):
            puntos += 1
    return puntos

MSG_OFERTA_CARRERAS = (
    "En TEINCO nuestras carreras funcionan por <b>Ciclos Propedéuticos</b> (modalidad <b>95% presencial</b>), lo que significa que a medida que avanzas obtienes <b>3 títulos oficiales</b> en una misma carrera:<br>"
    "1️⃣ <b>Técnico Profesional</b> (Semestres 1 al 4)<br>"
    "2️⃣ <b>Tecnólogo</b> (Semestres 5 al 6)<br>"
    "3️⃣ <b>Profesional Universitario</b> (Semestres 7 al 9)<br><br>"
    "<b>Programas Disponibles (Sedes Bogotá y Mosquera):</b><br>"
    "• Ingeniería de Sistemas (9 semestres)<br>"
    "• Ingeniería Mecatrónica (9 semestres)<br>"
    "• Administración de Empresas (9 semestres)<br>"
    "• Contaduría Pública (9 semestres)<br>"
    "• Marketing y Negocios Digitales (8 semestres)<br>"
    "• Diseño Digital Publicitario (8 semestres)<br><br>"
    "Además, contamos con programas <b>Técnicos Laborales Auxiliares</b> (2 semestres). "
    "Pregúntame por cualquiera para ver de qué trata, sus salidas laborales y precios, o escribe a: <b>carreras.modulo@teinco.edu.co</b>"
)
def procesar_mensaje(mensaje, carrera_contexto=None, es_primer_mensaje=False, indice_rotacion=0):
    texto = mensaje.lower().strip()
    texto_fon = normalizar_fonetica(texto)
    prefijo = obtener_prefijo_cortesia(es_primer_mensaje, indice_rotacion)

    if (any(p in texto_fon for p in ["ola", "buenos dias", "buenas tardes", "buenas noces"]) and len(texto.split()) <= 4) or any(m in texto_fon for m in ["menu", "ayuda", "bolber al menu", "todas las areas"]):
        msg = (
            "¡Hola! Bienvenido a <b>TEINCO</b>. Qué gusto saludarte hoy. Tenemos para ti las siguientes áreas disponibles:<br><br>"
            "1. Admisiones (Requisitos y Fechas 2027) 📋<br>"
            "2. Carreras (Oferta, Precios y Horarios) 📚<br>"
            "3. Notas (Sistema Académico) 📑<br>"
            "4. PQRS (Peticiones, Quejas y Sugerencias) 🛠️<br>"
            "5. Registro y Control (Cuentas y Grados) 👤<br><br>"
            "Cuéntame en qué te puedo ayudar hoy o selecciona una opción en los botones rápidos."
        )
        return {"respuesta": msg, "modulo": "Asistente General", "carrera_ctx": None, "chips": ["Oferta académica", "Precios de carreras", "Fechas de ingreso 2027", "Modalidades de grado"]}

    palabras_consulta = ["precio", "costo", "vale", "carrera", "horario", "nota", "pqrs", "fecha", "requisito", "ingles", "grado", "clave", "contraseña", "semestre", "pago", "beca"]
    if any(p in texto_fon for p in ["grasias", "te agradesco", "mil grasias", "muchas grasias", "chao", "adios", "asta luego"]) and not contiene_intencion(texto, palabras_consulta):
        msg_desp = "¡Con mucho gusto! 😊 Me alegra haberte ayudado. Estoy aquí para todo lo que necesites sobre <b>TEINCO</b>.<br><br>Si más adelante tienes otra duda sobre carreras, precios, horarios o trámites, escríbeme cuando quieras. ¡Muchos éxitos!"
        return {"respuesta": msg_desp, "modulo": "Asistente General", "carrera_ctx": carrera_contexto, "chips": ["⬅️ Volver al menú", "Oferta académica"]}

    if texto == "1":
        return {"respuesta": prefijo + "Para formalizar tu inscripción en TEINCO necesitas documento de identidad al 150%, diploma o acta de bachiller, resultados Saber 11 y formulario.<br><br>Más info en: <b>admisiones.modulo@teinco.edu.co</b>", "modulo": "Módulo Admisiones", "carrera_ctx": carrera_contexto, "chips": ["Fechas de ingreso 2027", "Métodos de pago", "Descuentos y financiación", "⬅️ Volver al menú"]}
    if texto == "2":
        return {"respuesta": prefijo + MSG_OFERTA_CARRERAS, "modulo": "Módulo Carreras", "carrera_ctx": None, "chips": ["Precios de carreras", "Horarios de estudio", "Homologación SENA", "⬅️ Volver al menú"]}
    if texto == "3":
        return {"respuesta": prefijo + "Por seguridad académica, las calificaciones se consultan iniciando sesión en el portal:<br><br><a href='#login' onclick=\"alert('Abriendo Login Académico...')\" class='btn-accion'>🔐 Iniciar Sesión (Sistema Académico)</a><br><br>Soporte académico: <b>registro.notas@teinco.edu.co</b>", "modulo": "Módulo Notas", "carrera_ctx": carrera_contexto, "chips": ["Certificado de notas", "Recuperar contraseña", "⬅️ Volver al menú"]}
    if texto == "4":
        return {"respuesta": prefijo + "Aquí podrás colocar tus peticiones, quejas, reclamos, sugerencias o felicitaciones para que podamos brindarte un mejor servicio (<b>soporte.pqrs@teinco.edu.co</b>):<br><br><div class='pqrs-form'><input type='text' id='pqrsNombre' placeholder='Nombre o ID' class='pqrs-input'><textarea id='pqrsTexto' placeholder='Escribe tu solicitud...' class='pqrs-textarea'></textarea><button type='button' onclick='enviarPQRS(this)' class='btn-accion'>Enviar PQRS</button></div>", "modulo": "Módulo PQRS", "carrera_ctx": carrera_contexto, "chips": ["⬅️ Volver al menú"]}
    if texto == "5":
        return {"respuesta": prefijo + "Para atención personalizada con un funcionario de Registro y Control (Lunes a viernes 8:00 a.m. – 5:00 p.m. y sábados 8:00 a.m. – 12:00 m. en sede principal Bogotá), escribe a: <b>registro.control@teinco.edu.co</b>", "modulo": "Módulo Registro y Control", "carrera_ctx": carrera_contexto, "chips": ["Modalidades de grado", "Recuperar contraseña", "Cambio de sede", "⬅️ Volver al menú"]}

    if contiene_intencion(texto, ["horario", "horarios", "jornada", "jornadas", "diurna", "nocturna", "sabados", "hora", "horas", "turno", "turnos"]):
        msg_horarios = (
            "En TEINCO manejamos tres jornadas flexibles para nuestros programas (modalidad 95% presencial):<br><br>"
            "• <b>Diurna:</b> Lunes a viernes de 7:00 a.m. a 1:00 p.m.<br>"
            "• <b>Nocturna:</b> Lunes a viernes de 6:00 p.m. a 10:00 p.m.<br>"
            "• <b>Sábados:</b> Sábados de 7:00 a.m. a 5:00 p.m.<br><br>"
            "Consulta disponibilidad de cupos en: <b>carreras.modulo@teinco.edu.co</b>"
        )
        return {"respuesta": prefijo + msg_horarios, "modulo": "Módulo Carreras (Horarios)", "carrera_ctx": carrera_contexto, "chips": ["Oferta de carreras", "Precios de carreras", "Parqueaderos cercanos", "⬅️ Volver al menú"]}

    if contiene_intencion(texto, ["requisito", "requisitos", "requerimiento", "requerimientos", "documento", "documentos", "papeles", "matricula", "matrica"]):
        msg_req = (
            "Para formalizar tu inscripción y matrícula en TEINCO necesitas tener listos estos documentos:<br><br>"
            "• <b>Documento de identidad</b> ampliado al 150%<br>"
            "• <b>Diploma de bachiller</b> o acta de grado<br>"
            "• <b>Resultados de las Pruebas Saber 11 (ICFES)</b><br>"
            "• <b>Formulario de inscripción</b> institucional y foto 3x4 fondo blanco<br><br>"
            "Más info en: <b>admisiones.modulo@teinco.edu.co</b>"
        )
        return {"respuesta": prefijo + msg_req, "modulo": "Módulo Admisiones", "carrera_ctx": carrera_contexto, "chips": ["Fechas de ingreso 2027", "Métodos de pago", "Homologación SENA", "⬅️ Volver al menú"]}

    if any(f in texto_fon for f in ["fecha", "calendario", "2027", "cuando abren", "cuando empiesan", "cuando inisian"]):
        msg_fechas = (
            "Estas son nuestras fechas oficiales de <b>inscripción, matrícula y calendario académico 2027</b>:<br><br>"
            "• <b>Primer Semestre (2027-1):</b> Inscripciones abiertas de octubre a enero. Clases del 1 de febrero al 30 de mayo de 2027.<br>"
            "• <b>Segundo Semestre (2027-2):</b> Inscripciones abiertas en junio y julio. Clases del 1 de agosto al 30 de noviembre de 2027.<br><br>"
            "Más info en: <b>admisiones.modulo@teinco.edu.co</b>"
        )
        return {"respuesta": prefijo + msg_fechas, "modulo": "Módulo Admisiones", "carrera_ctx": carrera_contexto, "chips": ["Requisitos de inscripción", "Precios de carreras", "Descuentos y financiación", "⬅️ Volver al menú"]}

    if any(f in texto_fon for f in ["metodo de pago", "metodos de pago", "formas de pago", "como pagar", "tarjeta", "pse", "pago"]):
        msg_pago = (
            "En TEINCO puedes realizar el pago de tu matrícula de manera segura mediante <b>tarjeta débito/crédito o PSE</b>.<br><br>"
            "Si necesitas información sobre financiación bancaria o descuentos, escribe a: <b>admisiones.modulo@teinco.edu.co</b>"
        )
        return {"respuesta": prefijo + msg_pago, "modulo": "Módulo Admisiones", "carrera_ctx": carrera_contexto, "chips": ["Descuentos y financiación", "Precios de carreras", "⬅️ Volver al menú"]}

    if contiene_intencion(texto, ["beca", "becas", "descuento", "descuentos", "financiacion", "credito", "banco", "convenio"]):
        msg_beca = (
            "Sobre <b>descuentos y financiación</b> en TEINCO ten en cuenta lo siguiente:<br><br>"
            "• <b>Descuentos y convenios:</b> Sí contamos con descuentos institucionales, pero se gestionan directamente con <b>Registro y Control</b> en <b>registro.control@teinco.edu.co</b>.<br>"
            "• <b>Financiación:</b> TEINCO no maneja financiación directa, pero puedes solicitar tu crédito educativo a través de una <b>entidad bancaria</b>."
        )
        return {"respuesta": prefijo + msg_beca, "modulo": "Módulo Admisiones", "carrera_ctx": carrera_contexto, "chips": ["Métodos de pago", "Requisitos de inscripción", "⬅️ Volver al menú"]}
    if any(f in texto_fon for f in ["parceadero", "parceaderos", "moto", "bisicleta"]):
        return {"respuesta": prefijo + "Alrededor de nuestras sedes de Bogotá y Mosquera contamos con <b>parqueaderos aliados cercanos</b> donde te cobran una tarifa preferencial más económica presentando tu carné estudiantil de TEINCO.", "modulo": "Módulo Bienestar / Sedes", "carrera_ctx": carrera_contexto, "chips": ["Horarios de estudio", "Cambio de sede", "⬅️ Volver al menú"]}

    if any(f in texto_fon for f in ["omologasion", "omologar", "sena"]):
        return {"respuesta": prefijo + "Sí puedes homologar tus estudios previos (como un técnico del SENA). Debes traer el <b>diploma y el certificado de notas/grado del último ciclo propedéutico</b> o programa cursado ante Registro y Control: <b>registro.control@teinco.edu.co</b>", "modulo": "Módulo Registro y Control", "carrera_ctx": carrera_contexto, "chips": ["Requisitos de inscripción", "Fechas de ingreso 2027", "⬅️ Volver al menú"]}

    if any(f in texto_fon for f in ["cambio de sede", "traslado", "mosgera", "pausar", "posponer", "aplasar"]):
        return {"respuesta": prefijo + "Sí es posible solicitar traslado entre sedes (Bogotá / Mosquera) o posponer tu semestre entre ciclos propedéuticos sin perder tus materias aprobadas; solo debes enviar un correo formal a Registro y Control: <b>registro.control@teinco.edu.co</b>", "modulo": "Módulo Registro y Control", "carrera_ctx": carrera_contexto, "chips": ["Modalidades de grado", "Recuperar contraseña", "⬅️ Volver al menú"]}

    if any(f in texto_fon for f in ["sertificado de notas", "sertificado", "constansia", "rebision"]):
        return {"respuesta": prefijo + "Los certificados oficiales de calificaciones, constancias de estudio y revisiones de notas en sistema se solicitan ante el área académica en: <b>registro.notas@teinco.edu.co</b>", "modulo": "Módulo Notas", "carrera_ctx": carrera_contexto, "chips": ["Recuperar contraseña", "⬅️ Volver al menú"]}

    if any(f in texto_fon for f in ["ingles", "idioma", "abilitasion", "abilitasiones", "recuperasion"]):
        return {"respuesta": prefijo + "En cada ciclo debes acreditar inglés según el MCER: <b>Técnico A1</b>, <b>Tecnólogo A2</b> y <b>Profesional B1</b>. Si pierdes un nivel o materia, debes presentar su recuperación según el calendario académico (<b>carreras.modulo@teinco.edu.co</b>).", "modulo": "Módulo Carreras", "carrera_ctx": carrera_contexto, "chips": ["Oferta de carreras", "Horarios de estudio", "⬅️ Volver al menú"]}

    if any(f in texto_fon for f in ["modalidad de grado", "modalidades de grado", "opciones de grado", "como me graduo", "graduarme", "pasantia", "practicas empresariales"]):
        msg_grado = (
            "En TEINCO contamos con <b>4 modalidades de grado</b> para que culmines tu formación profesional:<br><br>"
            "• <b>Prácticas empresariales</b><br>"
            "• <b>Pasantías</b><br>"
            "• <b>Validación por experiencia</b> (laboral en tu área)<br>"
            "• <b>Proyecto de grado</b><br><br>"
            "Gestiona tu opción ante Registro y Control: <b>registro.control@teinco.edu.co</b>"
        )
        return {"respuesta": prefijo + msg_grado, "modulo": "Módulo Registro y Control", "carrera_ctx": carrera_contexto, "chips": ["Cambio de sede", "Recuperar contraseña", "⬅️ Volver al menú"]}

    if any(f in texto_fon for f in ["contraseña", "contrasena", "olbide mi clabe", "recuperar clabe", "usuario bloceado", "no puedo entrar"]):
        msg_clave = (
            "Para recuperar tu contraseña o desbloquear tu cuenta institucional:<br><br>"
            "• Haz clic en <b>'¿Olvidaste tu contraseña?'</b> en la pantalla de inicio de sesión.<br>"
            "• Si el bloqueo persiste, envía tu nombre completo e ID estudiantil a Registro y Control: <b>registro.control@teinco.edu.co</b>"
        )
        return {"respuesta": prefijo + msg_clave, "modulo": "Módulo Registro y Control", "carrera_ctx": carrera_contexto, "chips": ["Modalidades de grado", "⬅️ Volver al menú"]}

    if any(f in texto_fon for f in ["otras careras", "demas careras", "todas las careras", "ce mas careras", "oferta academica"]):
        return {"respuesta": prefijo + MSG_OFERTA_CARRERAS, "modulo": "Módulo Carreras", "carrera_ctx": None, "chips": ["Precios de carreras", "Horarios de estudio", "Homologación SENA", "⬅️ Volver al menú"]}

    carrera_detectada = detectar_carrera(texto)
    carrera_activa = carrera_detectada if carrera_detectada else carrera_contexto

    if any(f in texto_fon for f in ["cuantos semestres", "cantos semestres", "cuanto dura", "durasion"]):
        if carrera_activa and carrera_activa in CARRERAS_INFO:
            c = CARRERAS_INFO[carrera_activa]
            return {"respuesta": prefijo + f"La carrera <b>{c['nombre']}</b> tiene una duración total de <b>{c['duracion']}</b> bajo el modelo de ciclos propedéuticos (Técnico Sem. 1-4, Tecnólogo Sem. 5-6 y Profesional Sem. 7-9).<br><br>Más info en: <b>carreras.modulo@teinco.edu.co</b>", "modulo": "Módulo Carreras", "carrera_ctx": carrera_activa, "chips": [f"Precio de {c['nombre']}", "Horarios de estudio", "⬅️ Volver al menú"]}
        return {"respuesta": prefijo + "Nuestras ingenierías, Administración y Contaduría tienen una duración de <b>9 semestres</b>, mientras que Marketing y Diseño Digital duran <b>8 semestres</b> (todos por ciclos propedéuticos).<br><br>Más info en: <b>carreras.modulo@teinco.edu.co</b>", "modulo": "Módulo Carreras", "carrera_ctx": carrera_activa, "chips": ["Otras carreras", "Precios de carreras", "⬅️ Volver al menú"]}
    mejor_frase_faq = None
    max_ratio = 0.0
    for item in reversed(cargar_conocimiento_extra()):
        preg_fon = normalizar_fonetica(item["pregunta"])
        if preg_fon == texto_fon or (len(texto_fon) >= 6 and texto_fon in preg_fon):
            return {"respuesta": prefijo + item["respuesta"], "modulo": "Base Institucional / Funcionario", "carrera_ctx": carrera_activa, "chips": ["Otras carreras", "Precios de carreras", "⬅️ Volver al menú"]}
        ratio = difflib.SequenceMatcher(None, texto_fon, preg_fon).ratio()
        if ratio > max_ratio:
            max_ratio = ratio
            mejor_frase_faq = item["respuesta"]

    if mejor_frase_faq and max_ratio >= 0.68:
        return {"respuesta": prefijo + mejor_frase_faq, "modulo": "Base Institucional / Funcionario", "carrera_ctx": carrera_activa, "chips": ["Otras carreras", "Precios de carreras", "⬅️ Volver al menú"]}

    puntajes = {
        "admisiones": contar_puntos(texto_fon, ["como inscribirme", "informasion de admisiones"], ["admisiones", "inscribirme", "inscribirse", "ingreso"]),
        "carreras": contar_puntos(texto_fon,
            ["cuanto bale", "cuanto cuesta", "ce presio", "presio de", "presio del", "balor del", "balor de", "ce careras", "ce se aprende", "de ce trata", "salida laboral", "salidas laborales", "en ce puedo trabajar", "ce puedo lograr"],
            ["precio", "precios", "costo", "vale", "valor", "tarifa", "tarifas", "semestre", "carrera", "carreras", "programa", "estudiar", "oferta", "tecnico", "tecnologo", "profesional", "lograr", "trabajar", "salida", "salidas", "pensum", "materias", "presencial"]) + (3 if carrera_detectada else 0),
        "notas": contar_puntos(texto_fon,
            ["ber mis notas", "mirar notas", "rebisar notas", "consultar notas"],
            ["nota", "notas", "calificacion", "calificaciones", "boletin", "promedio", "corte", "cortes", "parcial"]),
        "pqrs": contar_puntos(texto_fon,
            ["poner una ceja", "colocar una ceja", "aser un reclamo", "radicar pqrs", "dar una sugerencia", "ciero felisitar"],
            ["pqrs", "pqr", "queja", "quejas", "reclamo", "reclamos", "sugerencia", "sugerencias", "felicitacion", "felicitar"]),
        "registro": contar_puntos(texto_fon,
            ["ablar con un asesor", "atencion directa", "registro y control"],
            ["registro", "control", "asesor", "funcionario", "humano", "persona", "reintegro", "bienestar", "sede"])
    }

    ganador = max(puntajes, key=puntajes.get)
    if puntajes[ganador] > 0:
        if ganador == "admisiones":
            return {"respuesta": prefijo + "En el área de <b>Admisiones</b> gestionamos tu ingreso a TEINCO. Puedes consultar sobre requisitos de inscripción, fechas 2027, métodos de pago (tarjeta o PSE) y descuentos. Escribe a: <b>admisiones.modulo@teinco.edu.co</b>", "modulo": "Módulo Admisiones", "carrera_ctx": carrera_activa, "chips": ["Requisitos de inscripción", "Fechas de ingreso 2027", "Métodos de pago", "⬅️ Volver al menú"]}
        if ganador == "carreras":
            if contiene_intencion(texto, ["precio", "precios", "costo", "vale", "valor", "tarifa", "tarifas", "cuanto"]):
                msg_p, chips_p = tabla_precios(carrera_activa, texto)
                return {"respuesta": prefijo + msg_p, "modulo": "Módulo Carreras (Tarifas)", "carrera_ctx": carrera_activa, "chips": chips_p}
            if carrera_activa and carrera_activa in CARRERAS_INFO:
                c = CARRERAS_INFO[carrera_activa]
                msg = f"<b>{c['nombre']}</b> ({c['duracion']} - {c['sedes']})<br><br><b>De qué trata y qué aprenderás:</b><br>{c['descripcion']}<br><br><b>Qué puedes lograr y salidas laborales:</b><br>{c['logros']}<br><br>Más info en: <b>carreras.modulo@teinco.edu.co</b>"
                return {"respuesta": prefijo + msg, "modulo": "Módulo Carreras", "carrera_ctx": carrera_activa, "chips": [f"Precio de {c['nombre']}", "Horarios de estudio", "Otras carreras", "⬅️ Volver al menú"]}
            return {"respuesta": prefijo + MSG_OFERTA_CARRERAS, "modulo": "Módulo Carreras", "carrera_ctx": None, "chips": ["Precios de carreras", "Horarios de estudio", "Homologación SENA", "⬅️ Volver al menú"]}
        if ganador == "notas":
            return {"respuesta": prefijo + "Por seguridad académica, las calificaciones se consultan iniciando sesión en el portal:<br><br><a href='#login' onclick=\"alert('Abriendo Login Académico...')\" class='btn-accion'>🔐 Iniciar Sesión (Sistema Académico)</a><br><br>Soporte: <b>registro.notas@teinco.edu.co</b>", "modulo": "Módulo Notas", "carrera_ctx": carrera_activa, "chips": ["Certificado de notas", "Recuperar contraseña", "⬅️ Volver al menú"]}
        if ganador == "pqrs":
            return {"respuesta": prefijo + "Aquí podrás colocar tus peticiones, quejas, reclamos, sugerencias o felicitaciones para brindarte un mejor servicio (<b>soporte.pqrs@teinco.edu.co</b>):<br><br><div class='pqrs-form'><input type='text' id='pqrsNombre' placeholder='Nombre o ID' class='pqrs-input'><textarea id='pqrsTexto' placeholder='Escribe tu solicitud...' class='pqrs-textarea'></textarea><button type='button' onclick='enviarPQRS(this)' class='btn-accion'>Enviar PQRS</button></div>", "modulo": "Módulo PQRS", "carrera_ctx": carrera_contexto, "chips": ["⬅️ Volver al menú"]}
        if ganador == "registro":
            return {"respuesta": prefijo + "Para atención personalizada con un funcionario de Registro y Control (Lunes a viernes 8:00 a.m. – 5:00 p.m. y sábados 8:00 a.m. – 12:00 m. en sede principal Bogotá), escribe a: <b>registro.control@teinco.edu.co</b>", "modulo": "Módulo Registro y Control", "carrera_ctx": carrera_activa, "chips": ["Modalidades de grado", "Cambio de sede", "Homologación SENA", "⬅️ Volver al menú"]}

    try:
        res = client.models.generate_content(model='gemini-2.5-flash', contents=mensaje, config=types.GenerateContentConfig(system_instruction=CONTEXTO_TEINCO_REAL, temperature=0.2))
        return {"respuesta": prefijo + res.text, "modulo": "AsistIA Gemini", "carrera_ctx": carrera_activa, "chips": ["⬅️ Volver al menú", "Registro y Control"]}
    except Exception:
        return {"respuesta": "Lo sentimos.<br><br>Esta información no se encuentra disponible en este momento, comunícate con <b>Registro y Control</b>: <b>registro.control@teinco.edu.co</b> donde un funcionario atenderá tu caso.", "modulo": "Contingencia Registro y Control", "carrera_ctx": carrera_activa, "chips": ["⬅️ Volver al menú"]}
CSS_1 = r"""<style>
:root { --azul: #004691; --azul-oscuro: #002855; --amarillo: #f59e0b; --gris: #f4f6f9; --texto: #1e293b; }
* { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
body { background: var(--gris); color: var(--texto); display: flex; flex-direction: column; min-height: 100vh; }
.teinco-header { background: var(--azul-oscuro); color: #fff; padding: 14px 40px; display: flex; justify-content: space-between; align-items: center; border-bottom: 4px solid var(--amarillo); box-shadow: 0 2px 10px rgba(0,0,0,0.12); position: sticky; top: 0; z-index: 100; }
.logo-box { display: flex; align-items: center; gap: 12px; }
.logo-badge { background: var(--amarillo); color: var(--azul-oscuro); font-weight: 900; padding: 6px 14px; border-radius: 6px; font-size: 22px; letter-spacing: 1px; }
.logo-text strong { display: block; color: #fff; font-size: 16px; }
.logo-text small { color: #cbd5e1; font-size: 12px; }
.btn-admin-nav { background: var(--amarillo); color: var(--azul-oscuro); border: none; padding: 9px 16px; border-radius: 6px; cursor: pointer; font-weight: 700; font-size: 13px; }
.hero-students { background: linear-gradient(115deg, #002855 0%, #004691 100%); color: #fff; padding: 42px 40px; border-bottom: 3px solid #cbd5e1; }
.hero-inner { max-width: 1150px; margin: 0 auto; display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 30px; align-items: center; }
.hero-badge { display: inline-block; background: rgba(245,158,11,0.22); border: 1px solid var(--amarillo); color: #fde68a; padding: 4px 12px; border-radius: 20px; font-size: 11.5px; font-weight: bold; margin-bottom: 12px; }
.hero-inner h1 { font-size: 29px; line-height: 1.25; margin-bottom: 12px; }
.hero-inner p { font-size: 14.5px; color: #e2e8f0; line-height: 1.55; margin-bottom: 18px; }
.hero-photo-card { border-radius: 12px; overflow: hidden; border: 4px solid rgba(255,255,255,0.25); box-shadow: 0 12px 25px rgba(0,0,0,0.3); background: #001f44; }
.hero-photo-card img { width: 100%; height: 220px; object-fit: cover; display: block; }
.main-portal { flex: 1; max-width: 1150px; width: 100%; margin: 32px auto; padding: 0 20px; }
.modulos-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(205px, 1fr)); gap: 16px; }
.modulo-card { background: #fff; padding: 20px 16px; border-radius: 10px; border: 1px solid #cbd5e1; border-top: 5px solid var(--azul); cursor: pointer; transition: 0.2s; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 3px 10px rgba(0,0,0,0.04); }
.modulo-card:hover, .modulo-card.activo { transform: translateY(-4px); box-shadow: 0 10px 22px rgba(0,0,0,0.1); border-top-color: var(--amarillo); background: #f8fbff; }
.modulo-icon { font-size: 28px; margin-bottom: 10px; }
.modulo-card h3 { color: var(--azul-oscuro); font-size: 16px; margin-bottom: 7px; }
.modulo-card p { font-size: 12.5px; color: #475569; line-height: 1.45; margin-bottom: 12px; }
.modulo-card span { font-size: 12px; font-weight: bold; color: var(--azul); }"""
CSS_2 = r"""
.visor-modulo { margin-top: 26px; background: #fff; border-radius: 12px; border: 1px solid #cbd5e1; border-left: 6px solid var(--amarillo); padding: 26px; box-shadow: 0 8px 24px rgba(0,0,0,0.07); }
.visor-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #e2e8f0; padding-bottom: 12px; margin-bottom: 18px; }
.visor-header h2 { color: var(--azul-oscuro); font-size: 21px; }
.visor-body { font-size: 14px; line-height: 1.6; color: #334155; }
.visor-grid-2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin-top: 12px; }
.info-box { background: #f8fafc; border: 1px solid #e2e8f0; padding: 15px; border-radius: 8px; }
.info-box h4 { color: var(--azul); margin-bottom: 6px; font-size: 15px; }
.teinco-footer { background: var(--azul-oscuro); color: #cbd5e1; padding: 20px 40px; margin-top: auto; border-top: 3px solid var(--azul); }
.footer-grid { max-width: 1150px; margin: 0 auto; display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 18px; font-size: 11px; line-height: 1.5; }
.teinco-footer h4 { color: #fff; font-size: 12px; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.5px; }
.chat-fab { position: fixed; bottom: 24px; right: 24px; background: var(--azul); color: #fff; border: 3px solid var(--amarillo); padding: 14px 22px; border-radius: 50px; font-size: 15px; font-weight: bold; cursor: pointer; box-shadow: 0 6px 20px rgba(0,0,0,0.28); z-index: 999; }
.chat-widget { position: fixed; bottom: 88px; right: 24px; width: 395px; max-width: calc(100vw - 32px); height: 520px; max-height: calc(100vh - 110px); background: #fff; border-radius: 14px; box-shadow: 0 10px 30px rgba(0,0,0,0.28); border: 1px solid #cbd5e1; display: flex; flex-direction: column; overflow: hidden; z-index: 1000; }
.widget-header { background: var(--azul-oscuro); color: #fff; padding: 12px 16px; display: flex; justify-content: space-between; align-items: center; }
.widget-header small { display: block; font-size: 11px; color: #a7f3d0; }
.widget-controls button { background: rgba(255,255,255,0.15); border: none; color: #fff; padding: 5px 8px; border-radius: 5px; cursor: pointer; margin-left: 5px; }
.chat-messages-box { flex: 1; padding: 14px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; background: #f4f6f9; }
.message { max-width: 86%; padding: 10px 13px; border-radius: 12px; font-size: 13px; line-height: 1.45; }
.message.bot { background: #fff; align-self: flex-start; border-left: 4px solid var(--azul); box-shadow: 0 1px 2px rgba(0,0,0,0.06); }
.message.humano { background: #eff6ff; align-self: flex-start; border-left: 4px solid #16a34a; box-shadow: 0 1px 2px rgba(0,0,0,0.06); }
.message.user { background: #d9fdd3; align-self: flex-end; }
.msg-tag { font-size: 10px; font-weight: bold; color: var(--azul); margin-bottom: 3px; text-transform: uppercase; }
.msg-time { font-size: 10px; color: #777; text-align: right; margin-top: 4px; }
.chips-row { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 7px; }
.chip-btn { background: #eef4fc; color: var(--azul); border: 1px solid #b8d0f0; padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; cursor: pointer; }
.chat-input-box { padding: 10px; background: #fff; border-top: 1px solid #ddd; display: flex; gap: 8px; }
textarea#userInput { flex: 1; height: 40px; padding: 8px; border: 1px solid #ccc; border-radius: 6px; resize: none; font-size: 13px; }
button#sendBtn, .btn-accion { background: var(--azul); color: #fff; border: none; padding: 8px 14px; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 12.5px; text-decoration: none; display: inline-block; }
.tabla-precios { width: 100%; border-collapse: collapse; margin-top: 8px; font-size: 12.5px; }
.tabla-precios th, .tabla-precios td { border: 1px solid #ccc; padding: 7px; text-align: left; }
.tabla-precios th { background: var(--azul); color: #fff; }
.pqrs-form { display: flex; flex-direction: column; gap: 7px; margin-top: 6px; }
.pqrs-input, .pqrs-textarea { padding: 8px; border: 1px solid #ccc; border-radius: 5px; font-size: 13px; width: 100%; }
.admin-wrapper { max-width: 1200px; margin: 25px auto; padding: 0 20px; flex: 1; width: 100%; }
.login-card { max-width: 380px; margin: 50px auto; background: #fff; padding: 28px; border-radius: 12px; border: 1px solid #cbd5e1; border-top: 5px solid var(--azul); box-shadow: 0 8px 25px rgba(0,0,0,0.08); display: flex; flex-direction: column; gap: 12px; }
.stats-bar { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; margin-bottom: 18px; }
.stat-card { background: #fff; padding: 14px; border-radius: 8px; border: 1px solid #cbd5e1; border-left: 4px solid var(--azul); }
.stat-card strong { font-size: 22px; color: var(--azul-oscuro); display: block; }
.stat-card span { font-size: 11.5px; color: #64748b; }
.admin-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.admin-col { background: #fff; padding: 20px; border-radius: 8px; border: 1px solid #ddd; display: flex; flex-direction: column; gap: 10px; max-height: 78vh; overflow-y: auto; }
.acordeon-item { border: 1px solid #cbd5e1; border-radius: 8px; background: #f8fafc; overflow: hidden; margin-bottom: 6px; }
.acordeon-head { display: flex; justify-content: space-between; align-items: center; padding: 8px 10px; cursor: pointer; background: #eef2f6; font-size: 12.5px; }
.acordeon-head.abierto { background: #dbeafe; border-bottom: 1px solid #bfdbfe; }
.acordeon-body { padding: 10px; background: #fff; max-height: 190px; overflow-y: auto; display: flex; flex-direction: column; gap: 6px; font-size: 12px; }
.faq-item { background: #f9fafb; padding: 9px; border-radius: 6px; border: 1px solid #ddd; display: flex; justify-content: space-between; align-items: center; gap: 8px; font-size: 12.5px; }
.btn-clear { padding: 6px 10px; border-radius: 5px; border: 1px solid #bbb; background: #fff; cursor: pointer; font-size: 12px; }
@media (max-width: 850px) { .hero-inner, .admin-grid { grid-template-columns: 1fr; } }
</style>"""
BODY_BOT = r"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><title>TEINCO - Portal Institucional</title>""" + CSS_1 + CSS_2 + r"""</head><body>
<header class="teinco-header">
    <div class="logo-box">
        <span class="logo-badge">TEINCO</span>
        <div class="logo-text">
            <strong>Corporación Tecnológica Industrial Colombiana</strong>
            <small>Educación Superior por Ciclos Propedéuticos • Bogotá – Mosquera</small>
        </div>
    </div>
    <button type="button" class="btn-admin-nav" id="btnToggleAdmin" onclick="alternarPanelAdmin()">⚙️ Panel Funcionario</button>
</header>

<main id="vistaPortal">
    <section class="hero-students">
        <div class="hero-inner">
            <div>
                <span class="hero-badge">ADMISIONES ABIERTAS 2027 • 3 TÍTULOS PROFESIONALES</span>
                <h1>Fórmate como Técnico, Tecnólogo y Profesional Universitario</h1>
                <p>Explora nuestros 5 módulos de atención interactivos haciendo clic en las tarjetas de abajo, o conversa con nuestro asistente virtual <b>AsistIA TEINCO</b> desde la esquina inferior derecha.</p>
            </div>
            <div class="hero-photo-card">
                <img src="/imagen-estudiantes" alt="Estudiantes Universitarios TEINCO">
            </div>
        </div>
    </section>

    <div class="main-portal">
        <div class="modulos-grid">
            <div class="modulo-card" id="card-1" onclick="mostrarModuloVisual(1)">
                <div><div class="modulo-icon">📋</div><h3>1. Admisiones y Matrículas</h3><p>Requisitos de inscripción, calendario académico 2027, métodos de pago y descuentos.</p></div>
                <span>Ver información →</span>
            </div>
            <div class="modulo-card" id="card-2" onclick="mostrarModuloVisual(2)">
                <div><div class="modulo-icon">📚</div><h3>2. Carreras, Precios y Horarios</h3><p>Oferta por ciclos propedéuticos, tarifas 2027 por semestre, horarios e inglés.</p></div>
                <span>Ver información →</span>
            </div>
            <div class="modulo-card" id="card-3" onclick="mostrarModuloVisual(3)">
                <div><div class="modulo-icon">📑</div><h3>3. Sistema de Notas</h3><p>Acceso seguro a calificaciones, revisión de notas y certificados de estudio.</p></div>
                <span>Ver información →</span>
            </div>
            <div class="modulo-card" id="card-4" onclick="mostrarModuloVisual(4)">
                <div><div class="modulo-icon">🛠️</div><h3>4. Radicación PQRS</h3><p>Canal oficial para peticiones, quejas, reclamos, sugerencias y felicitaciones.</p></div>
                <span>Ver información →</span>
            </div>
            <div class="modulo-card" id="card-5" onclick="mostrarModuloVisual(5)">
                <div><div class="modulo-icon">👤</div><h3>5. Registro y Control</h3><p>Recuperación de contraseñas, modalidades de grado y atención con funcionarios.</p></div>
                <span>Ver información →</span>
            </div>
        </div>

        <div id="visorModulo" class="visor-modulo" style="display:none;">
            <div class="visor-header">
                <h2 id="visorTitulo">Módulo</h2>
                <button type="button" class="btn-clear" onclick="cerrarVisor()">✖ Cerrar vista</button>
            </div>
            <div id="visorContenido" class="visor-body"></div>
        </div>
    </div>
</main>

<main id="vistaLoginAdmin" class="admin-wrapper" style="display:none;">
    <div class="login-card">
        <h2 style="color:var(--azul-oscuro);text-align:center;">🔐 Acceso Panel Funcionario</h2>
        <p style="font-size:12.5px;color:#64748b;text-align:center;">Ingresa tus credenciales institucionales para gestionar chats guardados, estadísticas y base de conocimiento.</p>
        <input type="text" id="loginUser" class="pqrs-input" autocomplete="off" placeholder="Usuario institucional">
        <input type="password" id="loginPass" class="pqrs-input" autocomplete="new-password" placeholder="Contraseña">
        <button type="button" class="btn-accion" onclick="iniciarSesionAdmin()">Ingresar al Panel</button>
        <p id="loginError" style="color:#dc2626;font-size:12.5px;text-align:center;font-weight:bold;"></p>
    </div>
</main>

<main id="vistaFuncionario" class="admin-wrapper" style="display:none;">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;flex-wrap:wrap;gap:10px;">
        <h2 style="color:var(--azul-oscuro);">📊 Panel de Control Administrativo TEINCO</h2>
        <button type="button" class="btn-clear" onclick="cerrarSesionAdmin()">🔒 Cerrar Sesión</button>
    </div>

    <div class="stats-bar" id="panelEstadisticas"></div>

    <div class="admin-grid">
        <div class="admin-col">
            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
                <h3 style="color:var(--azul)">🟢 Chats Guardados y En Vivo</h3>
                <div style="display:flex;gap:6px;">
                    <button type="button" class="btn-clear" onclick="refrescarTodoAdmin(this)">🔄 Refresh</button>
                    <button type="button" id="btnSwitchBot" class="btn-accion" style="background:#16a34a;" onclick="alternarEstadoBot()">🤖 Bot Activo</button>
                </div>
            </div>
            <button type="button" id="btnToggleSesiones" class="btn-clear" style="text-align:left;font-weight:bold;display:flex;justify-content:space-between;align-items:center;" onclick="alternarListaSesiones()">
                <span>📂 Chats Guardados ▼</span><span id="badgeNuevos" style="display:none;background:#dc2626;color:#fff;border-radius:50%;padding:2px 7px;font-size:11px;font-weight:bold;">0</span>
            </button>
            <div id="listaSesiones" style="display:none;flex-direction:column;gap:4px;"></div>
            <textarea id="textoIntervencion" class="pqrs-textarea" style="height:65px" placeholder="Abre un chat arriba y escribe aquí tu respuesta directa..."></textarea>
            <div style="display:flex;gap:8px;flex-wrap:wrap">
                <button type="button" class="btn-accion" onclick="enviarIntervencion(false)">Enviar a Chat Abierto</button>
                <button type="button" class="btn-accion" style="background:#0f766e" onclick="enviarIntervencion(true)">Enviar y Guardar Permanente</button>
            </div>
            <p id="estadoIntervencion" style="color:green;font-weight:bold;font-size:12.5px"></p>
        </div>

        <div class="admin-col">
            <h3 style="color:var(--azul)">📚 Base de Conocimiento (JSON)</h3>
            <input type="hidden" id="editIndex" value="">
            <input type="text" id="adminPregunta" class="pqrs-input" placeholder="Frase o palabras clave...">
            <textarea id="adminRespuesta" class="pqrs-textarea" style="height:75px" placeholder="Respuesta oficial..."></textarea>
            <div style="display:flex;gap:8px"><button type="button" class="btn-accion" onclick="guardarDato()">Guardar Información</button><button type="button" class="btn-clear" onclick="cancelarEdicion()">Cancelar Edición</button></div>
            <p id="adminEstado" style="color:green;font-weight:bold;font-size:13px"></p>
            <h4 style="color:var(--azul);font-size:13.5px">Respuestas Guardadas:</h4>
            <div id="listaFaq" style="display:flex;flex-direction:column;gap:8px"></div>
        </div>
    </div>
</main>

<footer class="teinco-footer">
    <div class="footer-grid">
        <div><h4>Direcciones Institucionales</h4><p>• Sede Principal Bogotá: Carrera 16 # 39A - 65, Teusaquillo, Bogotá D.C.<br>• Sede Regional Mosquera: Calle 3 # 2 - 45, Centro, Mosquera, Cundinamarca.</p></div>
        <div><h4>Teléfonos y Horarios</h4><p>• PBX Bogotá: (601) 340 1555 | WhatsApp Admisiones: +57 310 555 0199<br>• Atención Sede Principal: Lunes a viernes 8:00 a.m. – 5:00 p.m. | Sábados 8:00 a.m. – 12:00 m.</p></div>
        <div><h4>Correos Institucionales</h4><p>• admisiones.modulo@teinco.edu.co | carreras.modulo@teinco.edu.co<br>• registro.notas@teinco.edu.co | registro.control@teinco.edu.co | soporte.pqrs@teinco.edu.co</p></div>
    </div>
</footer>

<button type="button" id="chatFab" class="chat-fab" onclick="toggleChat()">💬 AsistIA TEINCO</button>
<div id="chatWidget" class="chat-widget" style="display:none;">
    <div class="widget-header"><div><strong>AsistIA TEINCO</strong><small id="subtituloChat">🟢 En línea • Soporte Institucional</small></div><div class="widget-controls"><button type="button" title="Nuevo Chat" onclick="limpiarChat()">🧹</button><button type="button" title="Cerrar" onclick="toggleChat()">✖</button></div></div>
    <div class="chat-messages-box" id="chatBox"></div>
    <div class="chat-input-box"><textarea id="userInput" placeholder="Escribe tu consulta aquí..."></textarea><button type="button" id="sendBtn" onclick="enviarMensaje()">Enviar</button></div>
</div>"""
JS_1 = chr(60) + "script>" + r"""
const chatBox = document.getElementById('chatBox'), userInput = document.getElementById('userInput');
let carreraContexto = null, ultimaPreguntaUsuario = "", tokenAdmin = "", enVistaAdmin = false, totalMensajesSesion = 0;
let miSesionId = localStorage.getItem('teinco_chat_id');
if (!miSesionId) { miSesionId = 'Chat-' + Math.floor(1000 + Math.random() * 9000); localStorage.setItem('teinco_chat_id', miSesionId); }
let sesionAbiertaAdmin = null, cantidadMensajesVista = 0, vistosPorAdmin = {};

const DATOS_VISOR = {
    1: {
        titulo: "1. Admisiones y Matrículas",
        html: `<p style="margin-bottom:14px;"><b>Bienvenido al módulo de Admisiones y Matrículas.</b> En este módulo encontrarás los documentos necesarios para tu inscripción, nuestro calendario académico 2027 y los métodos de pago disponibles:</p>
        <div class="visor-grid-2">
            <div class="info-box"><h4>📄 Requisitos de Inscripción</h4><p>• Documento de identidad ampliado al 150%.<br>• Diploma de bachiller o acta de grado.<br>• Resultados Pruebas Saber 11 (ICFES).<br>• Formulario institucional y foto 3x4 fondo blanco.</p></div>
            <div class="info-box"><h4>📅 Fechas de Matrícula y Clases 2027</h4><p>• <b>2027-1:</b> Inscripciones octubre–enero. Clases del 1 de febrero al 30 de mayo.<br>• <b>2027-2:</b> Inscripciones junio–julio. Clases del 1 de agosto al 30 de noviembre.</p></div>
            <div class="info-box"><h4>💳 Pagos, Descuentos y Financiación</h4><p>• <b>Métodos de pago:</b> Tarjeta débito/crédito o PSE.<br>• <b>Descuentos:</b> Tramitados con Registro y Control.<br>• <b>Financiación:</b> A través de entidad bancaria.<br>Contacto: <b>admisiones.modulo@teinco.edu.co</b></p></div>
        </div>`
    },
    2: {
        titulo: "2. Carreras, Precios y Horarios",
        html: `<p style="margin-bottom:14px;"><b>Bienvenido al módulo de Carreras, Precios y Horarios.</b> En este módulo encontrarás nuestra oferta por ciclos propedéuticos (<b>Técnico Sem. 1-4, Tecnólogo Sem. 5-6 y Profesional Sem. 7-9</b>, modalidad <b>95% presencial</b>), <b>tarifas semestrales vigentes para 2027</b>, jornadas de estudio y cursos de inglés:</p>
        <table class="tabla-precios"><thead><tr><th>Programa Profesional</th><th>Técnico (1-4)</th><th>Tecnólogo (5-6)</th><th>Profesional (7-9)</th></tr></thead>
        <tbody>
            <tr><td>Ingeniería de Sistemas (Bogotá – Mosquera)</td><td>$1500 USD</td><td>$2200 USD</td><td>$3200 USD</td></tr>
            <tr><td>Ingeniería Mecatrónica (Bogotá)</td><td>$1600 USD</td><td>$2300 USD</td><td>$3300 USD</td></tr>
            <tr><td>Marketing y Negocios Digitales (Bogotá - 8 Sem.)</td><td>$1400 USD</td><td>$2000 USD</td><td>$2900 USD</td></tr>
            <tr><td>Administración de Empresas (Bogotá – Mosquera)</td><td>$1400 USD</td><td>$2000 USD</td><td>$3000 USD</td></tr>
            <tr><td>Contaduría Pública (Bogotá – Mosquera)</td><td>$1400 USD</td><td>$2000 USD</td><td>$3000 USD</td></tr>
            <tr><td>Diseño Digital Publicitario (Bogotá - 8 Sem.)</td><td>$1400 USD</td><td>$2000 USD</td><td>$2950 USD</td></tr>
            <tr><td>Técnicos Laborales Auxiliares (2 Sem.)</td><td>$1500 USD</td><td>N/A</td><td>N/A</td></tr>
        </tbody></table>
        <div class="visor-grid-2">
            <div class="info-box"><h4>🕒 Jornadas y Horarios</h4><p>• <b>Diurna:</b> Lunes a viernes 7:00 a.m. – 1:00 p.m.<br>• <b>Nocturna:</b> Lunes a viernes 6:00 p.m. – 10:00 p.m.<br>• <b>Sábados:</b> Sábados 7:00 a.m. – 5:00 p.m.</p></div>
            <div class="info-box"><h4>🌐 Cursos de Inglés y Habilitaciones</h4><p>• <b>Inglés por ciclo:</b> Técnico <b>A1</b>, Tecnólogo <b>A2</b>, Profesional <b>B1</b>.<br>• Habilitaciones y recuperaciones según calendario.<br>Contacto: <b>carreras.modulo@teinco.edu.co</b></p></div>
        </div>`
    },
    3: {
        titulo: "3. Sistema Académico y Consulta de Notas",
        html: `<p style="margin-bottom:14px;"><b>Bienvenido al módulo de Sistema Académico y Consulta de Notas.</b> En este módulo encontrarás el acceso seguro a tus calificaciones por corte, revisión de notas y certificados de estudio:</p>
        <a href="#login" onclick="alert('Redirigiendo al Portal de Inicio de Sesión Académico TEINCO...')" class="btn-accion">🔐 Iniciar Sesión en Sistema Académico</a>
        <div class="visor-grid-2" style="margin-top:16px;">
            <div class="info-box"><h4>📝 Revisión de Calificaciones</h4><p>Para corrección de notas en sistema, valida primero con tu docente y radica soporte en <b>registro.notas@teinco.edu.co</b>.</p></div>
            <div class="info-box"><h4>📄 Certificados de Notas</h4><p>Solicita certificados oficiales de calificaciones y constancias de estudio en <b>registro.notas@teinco.edu.co</b>.</p></div>
        </div>`
    },
    4: {
        titulo: "4. Radicación de PQRS",
        html: `<p style="margin-bottom:12px;"><b>Bienvenido al módulo de Radicación PQRS.</b> Aquí podrás colocar tus peticiones, quejas, reclamos, sugerencias o felicitaciones para que nosotros podamos tener conocimiento y brindarte un mejor servicio cada día:</p>
        <div class="pqrs-form" style="max-width:550px;">
            <input type="text" id="pqrsNombreVisor" placeholder="Tu Nombre Completo o ID Estudiantil" class="pqrs-input">
            <textarea id="pqrsTextoVisor" style="height:90px;" placeholder="Escribe aquí tu petición, queja, reclamo, sugerencia o felicitación..." class="pqrs-textarea"></textarea>
            <button type="button" onclick="enviarPQRSVisor(this)" class="btn-accion">📩 Radicar PQRS Oficial</button>
        </div>`
    },
    5: {
        titulo: "5. Registro y Control",
        html: `<p style="margin-bottom:14px;"><b>Bienvenido al módulo de Registro y Control.</b> En este módulo encontrarás soporte para recuperación de contraseñas, nuestras 4 modalidades de grado y atención directa con nuestros funcionarios (<b>registro.control@teinco.edu.co</b>):</p>
        <div class="visor-grid-2">
            <div class="info-box"><h4>🔑 Recuperación de Contraseñas</h4><p>Si olvidaste tu clave o tu cuenta está bloqueada, usa <b>'¿Olvidaste tu contraseña?'</b> en el portal o envía tu ID a <b>registro.control@teinco.edu.co</b>.</p></div>
            <div class="info-box"><h4>🎓 4 Modalidades de Grado</h4><p>• <b>Prácticas empresariales</b><br>• <b>Pasantías</b><br>• <b>Validación por experiencia</b><br>• <b>Proyecto de grado</b></p></div>
            <div class="info-box"><h4>👤 Atención Directa Sede Principal</h4><p>Horario sede principal Bogotá: <b>Lunes a viernes 8:00 a.m. – 5:00 p.m. | Sábados 8:00 a.m. – 12:00 m.</b><br><br><button type="button" class="btn-accion" onclick="toggleChat()">💬 Abrir Chat de Atención</button></p></div>
        </div>`
    }
};

function mostrarModuloVisual(num) {
    document.querySelectorAll('.modulo-card').forEach(c => c.classList.remove('activo'));
    document.getElementById('card-' + num).classList.add('activo');
    const visor = document.getElementById('visorModulo');
    document.getElementById('visorTitulo').innerText = DATOS_VISOR[num].titulo;
    document.getElementById('visorContenido').innerHTML = DATOS_VISOR[num].html;
    visor.style.display = 'block';
    visor.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function cerrarVisor() { document.getElementById('visorModulo').style.display = 'none'; document.querySelectorAll('.modulo-card').forEach(c => c.classList.remove('activo')); }

function enviarPQRSVisor(btn) {
    const box = btn.parentElement, nom = box.querySelector('#pqrsNombreVisor').value.trim(), det = box.querySelector('#pqrsTextoVisor').value.trim();
    if (!nom || !det) return alert('Por favor completa tu nombre/ID y tu mensaje.');
    box.innerHTML = '<div style="background:#dcfce7;border:1px solid #16a34a;padding:14px;border-radius:8px;color:#14532d;">✅ <b>PQRS Radicada Exitosamente</b><br>Número de seguimiento: <b>PQRS-2026-' + Math.floor(100 + Math.random() * 900) + '</b><br>Copia enviada a: <b>soporte.pqrs@teinco.edu.co</b></div>';
}
"""
JS_2 = r"""
function toggleChat() {
    const w = document.getElementById('chatWidget');
    w.style.display = (w.style.display === 'none' || w.style.display === '') ? 'flex' : 'none';
    if (w.style.display === 'flex') { sincronizarMiChat(); userInput.focus(); }
}

function alternarPanelAdmin() {
    enVistaAdmin = !enVistaAdmin;
    document.getElementById('vistaPortal').style.display = enVistaAdmin ? 'none' : 'block';
    document.getElementById('loginUser').value = '';
    document.getElementById('loginPass').value = '';
    document.getElementById('loginError').innerText = '';
    if (!enVistaAdmin) {
        document.getElementById('vistaLoginAdmin').style.display = 'none';
        document.getElementById('vistaFuncionario').style.display = 'none';
        document.getElementById('btnToggleAdmin').innerText = '⚙️ Panel Funcionario';
    } else {
        document.getElementById('btnToggleAdmin').innerText = '🌐 Volver al Portal TEINCO';
        if (tokenAdmin) {
            document.getElementById('vistaFuncionario').style.display = 'block';
            cargarPanelCompleto();
        } else {
            document.getElementById('vistaLoginAdmin').style.display = 'block';
        }
    }
}

async function iniciarSesionAdmin() {
    const u = document.getElementById('loginUser').value.trim(), p = document.getElementById('loginPass').value.trim();
    const res = await fetch('/api/admin/login', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({usuario: u, password: p}) });
    const data = await res.json();
    document.getElementById('loginUser').value = '';
    document.getElementById('loginPass').value = '';
    if (data.ok) {
        tokenAdmin = data.token;
        document.getElementById('loginError').innerText = '';
        document.getElementById('vistaLoginAdmin').style.display = 'none';
        document.getElementById('vistaFuncionario').style.display = 'block';
        cargarPanelCompleto();
    } else {
        document.getElementById('loginError').innerText = '❌ Usuario o contraseña incorrectos.';
    }
}

function cerrarSesionAdmin() {
    tokenAdmin = '';
    document.getElementById('loginUser').value = '';
    document.getElementById('loginPass').value = '';
    alternarPanelAdmin();
}

function bajarScroll() { requestAnimationFrame(function() { chatBox.scrollTop = chatBox.scrollHeight; }); }
function enviarRapido(op) { userInput.value = op; enviarMensaje(); }

function limpiarChat() {
    miSesionId = 'Chat-' + Math.floor(1000 + Math.random() * 9000);
    localStorage.setItem('teinco_chat_id', miSesionId);
    chatBox.innerHTML = ''; carreraContexto = null; totalMensajesSesion = 0; cantidadMensajesVista = 0;
}

function renderizarBurbujaChat(m) {
    const div = document.createElement('div');
    if (m.rol === 'user') {
        div.className = 'message user';
        div.innerHTML = m.texto + '<div class="msg-time">' + m.hora + '</div>';
    } else if (m.rol === 'humano') {
        div.className = 'message humano';
        div.innerHTML = '<div class="msg-tag" style="color:#15803d;">👤 ' + m.autor + '</div><div class="msg-body">' + m.texto + '</div><div class="msg-time">' + m.hora + '</div>';
    } else {
        let chipsHTML = (m.chips && m.chips.length > 0) ? '<div class="chips-row">' + m.chips.map(ch => '<button type="button" class="chip-btn" onclick="enviarRapido(this.innerText)">' + ch + '</button>').join('') + '</div>' : '';
        div.className = 'message bot';
        div.innerHTML = '<div class="msg-tag">' + m.modulo + '</div><div class="msg-body">' + m.texto + '</div>' + chipsHTML + '<div class="msg-time">' + m.hora + '</div>';
    }
    chatBox.appendChild(div);
}

async function sincronizarMiChat() {
    const res = await fetch('/api/chat/historial/' + miSesionId + '?t=' + Date.now());
    const data = await res.json();
    document.getElementById('subtituloChat').innerText = data.bot_activo ? '🟢 En línea • Soporte Institucional' : '👤 Atendido en vivo por Funcionario TEINCO';
    if (data.mensajes && data.mensajes.length !== cantidadMensajesVista) {
        chatBox.innerHTML = '';
        data.mensajes.forEach(renderizarBurbujaChat);
        cantidadMensajesVista = data.mensajes.length;
        totalMensajesSesion = data.mensajes.filter(x => x.rol === 'user').length;
        bajarScroll();
    }
}

async function enviarMensaje() {
    const texto = userInput.value.trim(); if (!texto) return;
    ultimaPreguntaUsuario = texto;
    const esPrimero = (totalMensajesSesion === 0);
    const rotacion = totalMensajesSesion;
    userInput.value = '';
    const res = await fetch('/api/chat', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({session_id: miSesionId, mensaje: texto, carrera_ctx: carreraContexto, es_primero: esPrimero, rotacion: rotacion}) });
    const data = await res.json();
    if (data.carrera_ctx !== undefined) carreraContexto = data.carrera_ctx;
    await sincronizarMiChat();
}

async function refrescarTodoAdmin(btn) {
    if (btn) btn.innerText = '⏳ Actualizando...';
    await cargarPanelCompleto();
    if (btn) { btn.innerText = '✅ Actualizado'; setTimeout(() => btn.innerText = '🔄 Refresh', 1200); }
}

async function cargarPanelCompleto() {
    const resEst = await fetch('/api/admin/estadisticas?t=' + Date.now()); const est = await resEst.json();
    const total = est.total_preguntas || 0;
    const pctNoResp = total > 0 ? Math.round((est.no_contestadas / total) * 100) : 0;

    let topPregHTML = "<span style='color:#64748b;font-size:12px;'>Aún no hay consultas registradas</span>";
    const entradas = Object.entries(est.preguntas_frecuentes || {}).sort((a, b) => b.at(1) - a.at(1));

    if (entradas.length > 0 && total > 0) {
        topPregHTML = '<div style="max-height:92px;overflow-y:auto;margin-top:4px;padding-right:4px;">' +
            entradas.map(([q, c]) => {
                const qSegura = q.replace(/'/g, "\\'");
                return `<div style="display:flex;justify-content:space-between;align-items:center;font-size:12px;margin-bottom:4px;border-bottom:1px solid #f1f5f9;padding-bottom:2px;">
                    <span>• <b>"${q}"</b> — ${Math.round((c / total) * 100)}% (${c})</span>
                    <button type="button" title="Borrar pregunta" style="border:none;background:transparent;cursor:pointer;font-size:11px;color:#dc2626;" onclick="borrarPreguntaFrecuente('${qSegura}')">🗑️</button>
                </div>`;
            }).join("") + '</div>';
    }

    const descList = (est.lista_desconocidas && est.lista_desconocidas.length > 0)
        ? est.lista_desconocidas.map(q => `<span style="display:inline-block;background:#fee2e2;color:#991b1b;padding:3px 8px;border-radius:4px;margin:2px;font-size:11.5px;cursor:pointer;" title="Clic para enseñar esta respuesta" onclick="document.getElementById('adminPregunta').value=this.innerText.replace('❓ ','')">❓ ${q}</span>`).join("")
        : "<span style='color:#64748b;font-size:12px;'>Ninguna pregunta pendiente</span>";

    document.getElementById('panelEstadisticas').innerHTML =
        '<div class="stat-card"><strong>' + total + '</strong><span>💬 Consultas en Chats</span><br><strong>' + pctNoResp + '%</strong><span>⚠️ Preguntas aún no resueltas (' + est.no_contestadas + ')</span><div style="margin-top:8px;"><button type="button" class="btn-clear" style="font-size:11px;" onclick="restaurarEstadisticas()">🔄 Restaurar Estadísticas</button></div></div>' +
        '<div class="stat-card"><span>🔥 <b>Preguntas Más Frecuentes (%):</b></span>' + topPregHTML + '</div>' +
        '<div class="stat-card"><span>🔍 <b>Preguntas aún no resueltas</b> (clic para enseñar al bot):</span><div style="margin-top:5px;">' + descList + '</div></div>';
    cargarChatsAdmin(); cargarListaFaq();
}

async function restaurarEstadisticas() {
    if (!confirm('¿Seguro que deseas reiniciar todas las estadísticas a 0?')) return;
    await fetch('/api/admin/estadisticas/reset', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({token: tokenAdmin}) });
    cargarPanelCompleto();
}

async function borrarPreguntaFrecuente(clave) {
    await fetch('/api/admin/estadisticas/borrar_frecuente', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({token: tokenAdmin, clave: clave})
    });
    cargarPanelCompleto();
}
"""
JS_3 = r"""
function alternarListaSesiones() {
    const div = document.getElementById('listaSesiones');
    div.style.display = (div.style.display === 'flex') ? 'none' : 'flex';
}

async function cargarChatsAdmin() {
    const res = await fetch('/api/admin/chats?t=' + Date.now()); const st = await res.json();
    const btn = document.getElementById('btnSwitchBot');
    btn.innerText = st.bot_activo ? '🤖 Bot Activo' : '👤 Modo Humano Activo';
    btn.style.background = st.bot_activo ? '#16a34a' : '#dc2626';

    const ids = Object.keys(st.sesiones || {}).reverse();
    const listaDiv = document.getElementById('listaSesiones');
    const badge = document.getElementById('badgeNuevos');
    if (ids.length === 0) {
        listaDiv.innerHTML = '<span style="color:#64748b;font-size:12px;">No hay chats guardados todavía.</span>';
        badge.style.display = 'none';
        sesionAbiertaAdmin = null;
        return;
    }

    if (sesionAbiertaAdmin && st.sesiones[sesionAbiertaAdmin]) {
        vistosPorAdmin[sesionAbiertaAdmin] = st.sesiones[sesionAbiertaAdmin].mensajes.length;
    }

    let totalNuevos = 0;
    listaDiv.innerHTML = ids.map(id => {
        const s = st.sesiones[id];
        const totalM = s.mensajes.length;
        const noLeidos = Math.max(0, totalM - (vistosPorAdmin[id] || 0));
        if (noLeidos > 0) totalNuevos++;
        const abierto = (sesionAbiertaAdmin === id);
        const globo = noLeidos > 0 ? `<span style="background:#dc2626;color:#fff;border-radius:10px;padding:1px 6px;font-size:10px;margin-left:5px;">+${noLeidos}</span>` : '';
        const cuerpo = abierto ? `<div class="acordeon-body">${s.mensajes.map(m => `<div><b>[${m.hora}] ${m.autor}:</b> ${m.texto.replace(/<[^>]*>?/gm, ' ').substring(0, 180)}</div>`).join('')}</div>` : '';
        return `<div class="acordeon-item">
            <div class="acordeon-head ${abierto ? 'abierto' : ''}" onclick="toggleAcordeonChat('${id}', ${totalM})">
                <span><b>${id}</b> <small style="color:#64748b;">(${s.fecha})</small>${globo}</span>
                <div style="display:flex;gap:6px;align-items:center;">
                    <button type="button" class="btn-clear" style="padding:2px 6px;color:#dc2626;" title="Borrar chat" onclick="event.stopPropagation(); borrarChatGuardado('${id}')">🗑️</button>
                    <span>${abierto ? '▲' : '▼'}</span>
                </div>
            </div>${cuerpo}
        </div>`;
    }).join('');

    badge.innerText = totalNuevos;
    badge.style.display = totalNuevos > 0 ? 'inline-block' : 'none';
}

function toggleAcordeonChat(id, totalM) {
    sesionAbiertaAdmin = (sesionAbiertaAdmin === id) ? null : id;
    if (sesionAbiertaAdmin) vistosPorAdmin[id] = totalM;
    cargarChatsAdmin();
}

async function borrarChatGuardado(id) {
    if (!confirm('¿Eliminar permanentemente ' + id + '?')) return;
    await fetch('/api/admin/chats/borrar', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({token: tokenAdmin, session_id: id}) });
    delete vistosPorAdmin[id];
    if (sesionAbiertaAdmin === id) sesionAbiertaAdmin = null;
    cargarChatsAdmin();
}

async function alternarEstadoBot() {
    await fetch('/api/admin/switch_bot', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({token: tokenAdmin}) });
    cargarChatsAdmin();
}

async function enviarIntervencion(permanente) {
    if (!sesionAbiertaAdmin) return alert('Primero despliega con la flechita ▼ el chat al que deseas responder.');
    const nota = document.getElementById('textoIntervencion').value.trim(); if (!nota) return alert('Escribe primero tu mensaje.');
    await fetch('/api/admin/intervenir', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({token: tokenAdmin, session_id: sesionAbiertaAdmin, mensaje: nota, permanente: permanente, pregunta_ref: ultimaPreguntaUsuario}) });
    document.getElementById('textoIntervencion').value = '';
    document.getElementById('estadoIntervencion').innerText = permanente ? '✅ Enviado al chat y guardado en JSON.' : '✅ Mensaje directo enviado a ' + sesionAbiertaAdmin;
    cargarChatsAdmin(); sincronizarMiChat(); if (permanente) cargarListaFaq();
}

function enviarPQRS(btn) {
    const box = btn.parentElement, nom = box.querySelector('#pqrsNombre').value.trim(), det = box.querySelector('#pqrsTexto').value.trim();
    if (!nom || !det) return alert('Completa los campos.');
    box.innerHTML = '✅ Radicado: <b>PQRS-2026-' + Math.floor(100 + Math.random() * 900) + '</b> enviado a <b>soporte.pqrs@teinco.edu.co</b>';
}

async function cargarListaFaq() {
    const res = await fetch('/api/admin/listar?t=' + Date.now()); const lista = await res.json();
    document.getElementById('listaFaq').innerHTML = lista.map((item, idx) => '<div class="faq-item"><div><b>' + item.pregunta + '</b><br><span style="color:#555">' + item.respuesta.replace(/<[^>]*>?/gm, '').substring(0, 70) + '...</span></div><div style="display:flex;gap:5px;flex-shrink:0"><button type="button" class="btn-accion" onclick="editarFaq(' + idx + ')">✏️</button><button type="button" class="btn-clear" onclick="borrarFaq(' + idx + ')">🗑️</button></div></div>').join('');
    window.faqCache = lista;
}

function editarFaq(idx) { const item = window.faqCache[idx]; document.getElementById('editIndex').value = idx; document.getElementById('adminPregunta').value = item.pregunta; document.getElementById('adminRespuesta').value = item.respuesta; document.getElementById('adminEstado').innerText = 'Editando #' + (idx + 1); }
function cancelarEdicion() { document.getElementById('editIndex').value = ''; document.getElementById('adminPregunta').value = ''; document.getElementById('adminRespuesta').value = ''; document.getElementById('adminEstado').innerText = ''; }

async function guardarDato() {
    const pregunta = document.getElementById('adminPregunta').value.trim(), respuesta = document.getElementById('adminRespuesta').value.trim(), idxVal = document.getElementById('editIndex').value;
    if (!pregunta || !respuesta) return alert('Completa ambos campos.');
    await fetch('/api/admin/agregar', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({token: tokenAdmin, pregunta: pregunta, respuesta: respuesta, indice: idxVal === '' ? null : parseInt(idxVal)}) });
    cancelarEdicion(); document.getElementById('adminEstado').innerText = '✅ Guardado.'; cargarListaFaq();
}

async function borrarFaq(idx) { await fetch('/api/admin/borrar', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({token: tokenAdmin, indice: idx}) }); cargarListaFaq(); }
userInput.addEventListener('keydown', function(e) { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); enviarMensaje(); } });
setInterval(function() { if (enVistaAdmin && tokenAdmin) cargarChatsAdmin(); const w = document.getElementById('chatWidget'); if (w && w.style.display === 'flex') sincronizarMiChat(); }, 4000);
""" + chr(60) + "/" + "script>" + "</body></html>"

PAGINA_HTML = BODY_BOT + JS_1 + JS_2 + JS_3

@app.route('/')
def index():
    return render_template_string(PAGINA_HTML)

@app.route('/imagen-estudiantes')
def imagen_estudiantes():
    for nombre in ["estudiantes.jpg", "estudiantes.png", "estudiantes.jpeg"]:
        if os.path.exists(nombre):
            return send_file(nombre)
    svg = '''<svg xmlns="http://w3.org" viewBox="0 0 600 320"><rect width="600" height="320" fill="#003570"/><circle cx="480" cy="70" r="90" fill="rgba(245,158,11,0.22)"/><g transform="translate(135, 65)"><circle cx="70" cy="55" r="28" fill="#ffd1b3"/><path d="M25,165 C25,115 115,115 115,165 Z" fill="#f59e0b"/><circle cx="165" cy="48" r="30" fill="#f1c27d"/><path d="M115,165 C115,110 215,110 215,165 Z" fill="#ffffff"/><circle cx="260" cy="55" r="28" fill="#e0ac69"/><path d="M215,165 C215,115 305,115 305,165 Z" fill="#38bdf8"/></g><rect x="0" y="230" width="600" height="90" fill="rgba(0,25,55,0.8)"/><text x="300" y="268" fill="#ffffff" font-family="Segoe UI, sans-serif" font-size="20" font-weight="bold" text-anchor="middle">Comunidad Estudiantil TEINCO</text><text x="300" y="294" fill="#fde68a" font-family="Segoe UI, sans-serif" font-size="14" text-anchor="middle">Bogotá D.C. • Mosquera | Ciclos Propedéuticos</text></svg>'''
    return Response(svg, mimetype='image/svg+xml')

@app.route('/api/chat', methods=['POST'])
def api_chat():
    d = request.get_json()
    sid = d.get('session_id', 'Chat-General')
    msg_limpio = html.escape(d.get('mensaje', '')[:500])
    agregar_mensaje_sesion(sid, "user", "Estudiante", msg_limpio)
    datos_chats = cargar_chats()
    if not datos_chats.get("bot_activo", True):
        registrar_evento_estadistica("pregunta", "Registro y Control", msg_limpio)
        return jsonify({"modo_humano": True})
    res = procesar_mensaje(d.get('mensaje', '')[:500], d.get('carrera_ctx'), d.get('es_primero', False), d.get('rotacion', 0))
    agregar_mensaje_sesion(sid, "bot", "AsistIA TEINCO", res['respuesta'], res['modulo'], res.get('chips', []))
    registrar_evento_estadistica("pregunta", res["modulo"], msg_limpio)
    return jsonify(res)

@app.route('/api/chat/historial/<session_id>', methods=['GET'])
def api_chat_historial(session_id):
    datos = cargar_chats()
    sesion = datos.get("sesiones", {}).get(session_id, {"mensajes": []})
    return jsonify({"bot_activo": datos.get("bot_activo", True), "mensajes": sesion.get("mensajes", [])})

@app.route('/api/admin/chats', methods=['GET'])
def api_admin_chats():
    return jsonify(cargar_chats())

@app.route('/api/admin/chats/borrar', methods=['POST'])
def api_admin_chats_borrar():
    d = request.get_json()
    if d.get('token') != ADMIN_TOKEN: return jsonify({"ok": False}), 403
    datos = cargar_chats()
    datos.get("sesiones", {}).pop(d.get('session_id'), None)    
    guardar_chats(datos)
    return jsonify({"ok": True})

@app.route('/api/admin/login', methods=['POST'])
def api_admin_login():
    d = request.get_json()
    if d.get('usuario') == ADMIN_USER and d.get('password') == ADMIN_PASS:
        return jsonify({"ok": True, "token": ADMIN_TOKEN})
    return jsonify({"ok": False})

@app.route('/api/admin/estadisticas', methods=['GET'])
def api_admin_estadisticas(): return jsonify(cargar_estadisticas())

@app.route('/api/admin/estadisticas/reset', methods=['POST'])
def api_admin_estadisticas_reset():
    if request.get_json().get('token') != ADMIN_TOKEN: return jsonify({"ok": False}), 403
    guardar_estadisticas({"total_preguntas": 0, "no_contestadas": 0, "preguntas_frecuentes": {}, "lista_desconocidas": []})
    return jsonify({"ok": True})

@app.route('/api/admin/estadisticas/borrar_frecuente', methods=['POST'])
def api_admin_estadisticas_borrar_frecuente():
    d = request.get_json()
    if d.get('token') != ADMIN_TOKEN: return jsonify({"ok": False}), 403
    est = cargar_estadisticas()
    clave = d.get('clave', '')
    cant = est.get("preguntas_frecuentes", {}).pop(clave, 0)
    est["total_preguntas"] = max(0, est.get("total_preguntas", 0) - cant)
    guardar_estadisticas(est)
    return jsonify({"ok": True})

@app.route('/api/admin/switch_bot', methods=['POST'])
def api_switch_bot():
    if request.get_json().get('token') != ADMIN_TOKEN: return jsonify({"ok": False}), 403
    datos = cargar_chats()
    datos["bot_activo"] = not datos.get("bot_activo", True)
    guardar_chats(datos)
    return jsonify({"ok": True, "bot_activo": datos["bot_activo"]})

@app.route('/api/admin/intervenir', methods=['POST'])
def api_intervenir():
    d = request.get_json()
    if d.get('token') != ADMIN_TOKEN: return jsonify({"ok": False}), 403
    sid = d.get('session_id', 'Chat-General')
    msg = html.escape(d.get('mensaje', ''))
    agregar_mensaje_sesion(sid, "humano", "Funcionario TEINCO", msg, "Atención Directa")
    if d.get('permanente') and d.get('pregunta_ref'):
        guardar_conocimiento_extra(d.get('pregunta_ref'), msg)
    return jsonify({"ok": True})

@app.route('/api/admin/listar', methods=['GET'])
def api_listar(): return jsonify(cargar_conocimiento_extra())

@app.route('/api/admin/agregar', methods=['POST'])
def api_admin():
    d = request.get_json()
    if d.get('token') != ADMIN_TOKEN: return jsonify({"ok": False}), 403
    guardar_conocimiento_extra(d.get('pregunta', ''), d.get('respuesta', ''), d.get('indice'))
    return jsonify({"status": "ok"})

@app.route('/api/admin/borrar', methods=['POST'])
def api_borrar():
    d = request.get_json()
    if d.get('token') != ADMIN_TOKEN: return jsonify({"ok": False}), 403
    eliminar_conocimiento_extra(d.get('indice'))
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    puerto = int(os.environ.get("PORT", 3000))
    print(f"Iniciando AsistIA TEINCO en puerto {puerto}")
    app.run(host='0.0.0.0', port=puerto, debug=False)

