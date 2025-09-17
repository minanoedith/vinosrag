import streamlit as st
import requests
import os

PATH_API_AWS = st.secrets.get("PATH_API_AWS") or os.getenv("PATH_API_AWS")
PATH_API_AWS = "https://2unwigbq3h.execute-api.us-east-1.amazonaws.com/VinosRAG/vinos"

# ---------------------------
# Configuracion de la página
# ---------------------------
st.set_page_config(page_title="Consultas de Ventas", page_icon="📊", layout="centered")
st.title("Exportación de Vinos 🍷")
st.markdown("Haz una pregunta sobre ventas de exportación y obtén una respuesta basada en datos de ventas")

# ---------------------------------
# Estado inicial de la aplicacion
# ---------------------------------
if "pregunta" not in st.session_state:
    st.session_state.pregunta = ""

if "respuesta" not in st.session_state:
    st.session_state.respuesta = ""

# Se guarda el body completo para mostrar detalles (periodo, traza, etc.)
if "body" not in st.session_state:
    st.session_state.body = None

# bandera para limpiar antes de renderizar widgets
if "trigger_clear" not in st.session_state:
    st.session_state.trigger_clear = False

# si se activa limpiar en la corrida anterior, aplica limpieza antes de dibujar widgets
if st.session_state.trigger_clear:
    st.session_state.pregunta = ""
    st.session_state.respuesta = ""
    st.session_state.body = None
    st.session_state.trigger_clear = False

# ---------------------------
# Cliente del endpoint
# ---------------------------
def consultar_api(pregunta_usuario, incluir_trazas):
    url = PATH_API_AWS
    headers = {"Content-Type": "application/json"}
    payload = {"pregunta": pregunta_usuario}
    if incluir_trazas:
        payload["trazas"] = 1

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            # El RAG retorna {"statusCode":..., "headers":..., "body":{...}}
            body = data.get("body", {}) if isinstance(data, dict) else {}
            # Guarda todo el body para mostrar detalles
            st.session_state.body = body
            # Extrae respuesta de conveniencia
            return body.get("respuesta", "Respuesta no disponible")
        else:
            st.session_state.body = None
            return f"Error {response.status_code}: {response.text}"
    except requests.exceptions.Timeout:
        st.session_state.body = None
        return "Error de conexión: tiempo de espera agotado."
    except Exception as e:
        st.session_state.body = None
        return f"Error de conexión: {str(e)}"

# ---------------------------
# UI: pregunta y controles
# ---------------------------
st.text_area(
    "Escribe tu pregunta:",
    height=100,
    placeholder="¿Qué vendedor ha cerrado más negocios de exportación de vinos de la marca Pionero en América Norte?",
    key="pregunta"
)

# Mostrar detalle debajo de la pregunta y antes de los botones
mostrar_detalle = st.checkbox("Mostrar detalle", value=False, help="Muestra período y trazas si están disponibles")

# Botones de accion
col1, col2 = st.columns([1, 1])
with col1:
    if st.button("Consultar"):
        if st.session_state.pregunta.strip():
            with st.spinner("Obteniendo la respuesta..."):
                st.session_state.respuesta = consultar_api(st.session_state.pregunta, incluir_trazas=mostrar_detalle)
        else:
            st.warning("Por favor, escribe una pregunta antes de consultar")

with col2:
    # Se activa una bandera y rerun para que la limpieza se aplique antes de renderizar el text_area
    if st.button("Limpiar"):
        st.session_state.trigger_clear = True
        st.rerun()

# ---------------------------
# Mostrar respuesta y detalle
# ---------------------------
if st.session_state.respuesta:
    st.success("Respuesta recibida:")
    st.markdown(f"> {st.session_state.respuesta}")

    # Si el usuario activa "Mostrar detalle", se muestra periodo y traza
    if mostrar_detalle and isinstance(st.session_state.body, dict):
        periodo = st.session_state.body.get("periodo")
        traza = st.session_state.body.get("traza")

        # Periodo
        if periodo:
            st.subheader("Periodo")
            # Muestra start, end, label si existen
            c1, c2, c3 = st.columns([1, 1, 2])
            with c1:
                st.write(f"• Inicio: {periodo.get('start', '-')}")
            with c2:
                st.write(f"• Fin: {periodo.get('end', '-')}")
            with c3:
                st.write(f"• Etiqueta: {periodo.get('label', '-')}")

        # Traza
        if traza:
            st.subheader("Traza")
            st.json(traza)
