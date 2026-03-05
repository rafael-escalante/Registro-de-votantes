import streamlit as st
from supabase import create_client

# --- 1. CREDENCIALES (Confirmadas por tus imágenes) ---
url = "https://movucqjgwjnsvsyivrls.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1vdnVjcWpnd2puc3ZzeWl2cmxzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzI2MzMwMDAsImV4cCI6MjA4ODIwOTAwMH0.DrZTwU4K1hB8kYapncLTzri-o0PXFmqFGnvI48e2mOI"

supabase = create_client(url, key)

st.set_page_config(page_title="Sistema Electoral Yucatán", layout="centered")

# --- 2. LÓGICA DE LOGIN ---
if "auth_user" not in st.session_state:
    st.title("🔐 Acceso al Sistema")
    with st.form("login_form"):
        email_input = st.text_input("Correo electrónico")
        pass_input = st.text_input("Contraseña", type="password")
        if st.form_submit_button("Entrar"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email_input, "password": pass_input})
                st.session_state.auth_user = res.user
                st.session_state.user_email = email_input
                st.rerun()
            except Exception:
                st.error("Credenciales incorrectas.")
    st.stop()

## --- RECONOCIMIENTO DE PERFIL (VERSIÓN DE DIAGNÓSTICO) ---
try:
    uid_actual = st.session_state.auth_user.id
    
    # Intento 1: Buscar por id_auth
    res = supabase.table("personas").select("*").eq("id_auth", uid_actual).execute()
    
    # Si no encuentra nada, intentamos buscar por correo (para saber si el UID es el problema)
    if not res.data:
        email_actual = st.session_state.user_email
        res = supabase.table("personas").select("*").eq("correo", email_actual).execute()
        if res.data:
            st.warning(f"⚠️ Se encontró tu correo pero el UID no coincide. Actualizando UID...")
            supabase.table("personas").update({"id_auth": uid_actual}).eq("correo", email_actual).execute()
            st.rerun()

    if res.data and len(res.data) > 0:
        perfil = res.data[0]
        nombre_usuario = perfil.get('nombre', 'Usuario')
        rol_actual = perfil.get('id_rol', 3)
        st.session_state.perfil_cargado = True 
    else:
        st.error("🚫 Supabase no devuelve ninguna fila para este usuario.")
        st.info(f"UID actual: {uid_actual}")
        if st.button("🔄 Forzar Reintento"):
            st.rerun()
        st.stop()
except Exception as e:
    st.error(f"❌ Error de conexión: {e}")
    st.stop()

# --- 4. INTERFAZ ---
st.sidebar.success(f"Bienvenido, {nombre_usuario}")
if st.sidebar.button("Cerrar Sesión"):
    supabase.auth.sign_out()
    del st.session_state.auth_user
    st.rerun()

# Si es Seccional (ID 1)
if rol_actual == 1:
    st.title("🚩 Panel Seccional")
    st.write("Descarga los reportes de tu sección aquí.")
    if st.button("Generar PDF"):
        st.write("Procesando...")
else:
    st.title("📝 Registro de Ciudadanos")
    # ... Aquí va el formulario de captura que ya tenías ...
    with st.form("registro"):
        nom = st.text_input("Nombre")
        ap = st.text_input("Apellido Paterno")
        curp = st.text_input("CURP")
        sec = st.text_input("Sección")
        if st.form_submit_button("Guardar"):
            data = {"nombre": nom, "apellido_paterno": ap, "curp": curp, "seccion": sec, "id_rol": 4, "id_capturista": uid_actual}
            supabase.table("personas").insert(data).execute()
            st.success("Guardado correctamente")