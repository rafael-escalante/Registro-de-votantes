import streamlit as st
from supabase import create_client

#comand: python -m streamlit run proyect.py

# --- 1. CREDENCIALES ---
url = "https://movucqjgwjnsvsyivrls.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1vdnVjcWpnd2puc3ZzeWl2cmxzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzI2MzMwMDAsImV4cCI6MjA4ODIwOTAwMH0.DrZTwU4K1hB8kYapncLTzri-o0PXFmqFGnvI48e2mOI"

# Mantenemos la conexión "viva" para evitar retrasos en el primer clic
@st.cache_resource
def get_supabase():
    return create_client(url, key)

supabase = get_supabase()

st.set_page_config(page_title="Sistema Electoral Yucatán", layout="wide")

# --- 2. LÓGICA DE ACCESO (OPTIMIZADA PARA 1 SOLO CLIC) ---
if "auth_user" not in st.session_state:
    st.session_state.auth_user = None

if st.session_state.auth_user is None:
    st.title("🔐 Acceso al Sistema")
    
    # Usamos un formulario limpio para el login
    with st.form("login_form"):
        email = st.text_input("Correo electrónico")
        password = st.text_input("Contraseña", type="password")
        submit = st.form_submit_button("Entrar")
        
        if submit:
            try:
                # Intentamos la autenticación
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                if res.user:
                    st.session_state.auth_user = res.user
                    # El rerun inmediato es la clave para evitar el segundo clic
                    st.rerun()
            except Exception:
                st.error("Credenciales incorrectas. Verifique su correo y contraseña.")
    st.stop()

# --- 3. RECONOCIMIENTO DE PERFIL ---
uid_actual = st.session_state.auth_user.id
try:
    res_perfil = supabase.table("personas").select("*").eq("id_auth", uid_actual).execute()
    if res_perfil.data:
        perfil = res_perfil.data[0]
        nombre_usuario = perfil['nombre']
        rol_cap = perfil['id_rol']  # <--- IMPORTANTE: Definimos el rol aquí
    else:
        st.warning("⚠️ Usuario autenticado pero no vinculado en la tabla 'personas'.")
        st.info(f"ID: {uid_actual}")
        if st.button("Cerrar Sesión"):
            st.session_state.auth_user = None
            st.rerun()
        st.stop()
except Exception as e:
    st.error(f"Error de base de datos: {e}")
    st.stop()

# --- LISTA DE SECCIONES VÁLIDAS ---
# Excluimos la 1000 como solicitaste
SECCIONES_YUCATAN = [
    "990", "991", "992", "993", "994", "995", "996", "997", "998", "999", 
    "1001", "1002", "1003", "1004", "1005", "1006", "1007", "1008", "1009"
]

# --- 4. INTERFAZ Y NAVEGACIÓN (TABS) ---
st.sidebar.success(f"Conectado: {nombre_usuario}")
# Mostramos la sección a la que pertenece el capturista
st.sidebar.info(f"📍 Sección: {perfil.get('seccion', 'N/A')}")

if st.sidebar.button("Cerrar Sesión"):
    st.session_state.auth_user = None
    st.rerun()

# Navegación por pestañas
if rol_cap == 1:
    tab1, tab2, tab3 = st.tabs(["📝 Registro Ciudadano", "📊 Dashboard", "⚙️ Administración"])
else:
    tab1, tab2 = st.tabs(["📝 Registro Ciudadano", "📊 Mis Números"])
    tab3 = None

# --- PESTAÑA 1: REGISTRO DE CIUDADANOS (ACTUALIZADO) ---
with tab1:
    st.subheader("📝 Registro de Ciudadanos Promovidos")
    
    # 1. Cargamos la lista de promotores disponibles (Rol 3) para asignar el crédito
    # Filtramos por sección para que sea más fácil encontrar al promotor adecuado
    res_promotores = supabase.table("personas").select("id, nombre, apellido_paterno, seccion").eq("id_rol", 3).execute()
    
    # Creamos un diccionario para el selectbox: "Nombre Apellido (Sección)" -> ID
    dict_promotores = {
        f"{p['nombre']} {p['apellido_paterno']} - Sec. {p['seccion']}": p['id'] 
        for p in res_promotores.data
    }
    
    with st.form("registro_promovido", clear_on_submit=True):
        st.subheader("Datos del Ciudadano")
        c1, c2, c3 = st.columns(3)
        with c1: nom = st.text_input("Nombre(s)")
        with c2: ap_p = st.text_input("Apellido Paterno")
        with c3: ap_m = st.text_input("Apellido Materno")
        
        c4, c5 = st.columns(2)
        with c4: curp_val = st.text_input("CURP (18 dígitos)")
        with c5: tel_val = st.text_input("Teléfono")

        st.divider()
        st.subheader("🚀 Asignación de Promotor")
        # Aquí es donde el Seccional elige a qué promotor le corresponde
        promotor_asignado = st.selectbox(
            "¿A qué promotor le corresponde este registro?", 
            options=list(dict_promotores.keys()),
            help="Seleccione el promotor que consiguió a este ciudadano."
        )

        st.divider()
        st.subheader("📍 Ubicación")
        c6, c7, c8, c9 = st.columns([2, 1, 1, 1])
        with c6: calle_val = st.text_input("Calle")
        with c7: cr1 = st.text_input("Cruzamiento 1")
        with c8: cr2 = st.text_input("Cruzamiento 2")
        with c9: n_casa = st.text_input("No. Casa")

        c10, c11 = st.columns(2)
        with c10: zona_val = st.text_input("Fraccionamiento o Comisaría")
        with c11: sec_val = st.selectbox("Sección Electoral del Ciudadano", options=SECCIONES_YUCATAN)

        ref_val = st.text_area("Referencias")

        if st.form_submit_button("✅ GUARDAR REGISTRO"):
            if nom and ap_p and curp_val:
                try:
                    # El ID del promotor seleccionado
                    id_promotor_dueño = dict_promotores[promotor_asignado]
                    
                    data_insert = {
                        "nombre": nom,
                        "apellido_paterno": ap_p,
                        "apellido_materno": ap_m,
                        "curp": curp_val,
                        "telefono": tel_val,
                        "calle": calle_val,
                        "cruzamiento_1": cr1,
                        "cruzamiento_2": cr2,
                        "numero_casa": n_casa,
                        "fraccionamiento_comisaria": zona_val,
                        "referencias": ref_val,
                        "seccion": sec_val,
                        "id_rol": 4, # Es un promovido
                        "id_capturista": uid_actual, # Quién lo tecleó (Rafael)
                        "id_superior": id_promotor_dueño # A quién le pertenece (El Promotor)
                    }
                    supabase.table("personas").insert(data_insert).execute()
                    st.success(f"¡Registro guardado! Asignado correctamente a {promotor_asignado}.")
                except Exception as e:
                    st.error(f"Error al guardar: {e}")
            else:
                st.warning("⚠️ Nombre, Apellido Paterno y CURP son obligatorios.")

# --- PESTAÑA 3: ADMINISTRACIÓN (STAFF) ---
if tab3:
    with tab3:
        st.header("⚙️ Gestión de Staff Operativo")
        
        # 1. Obtener roles (1, 2, 3)
        res_roles = supabase.table("roles").select("*").lt("id", 4).execute()
        roles_dict = {r['nombre_rol']: r['id'] for r in res_roles.data}

        # 2. Obtener posibles jefes
        res_jefes = supabase.table("personas").select("id, nombre, apellido_paterno, curp").lt("id_rol", 4).execute()
        jefes_opciones = {f"{j['nombre']} {j['apellido_paterno']} ({j['curp']})": j['id'] for j in res_jefes.data}
        jefes_opciones["--- Sin Superior (Seccional) ---"] = None

        with st.form("alta_staff", clear_on_submit=True):
            st.subheader("Nuevo Integrante")
            col_n, col_a, col_z = st.columns(3)
            with col_n: nombre_s = st.text_input("Nombre")
            with col_a: ap_s = st.text_input("Apellido Paterno")
            with col_z: am_s = st.text_input("Apellido Materno")
            
            col_fg, col_fg2 = st.columns(2)
            with col_fg: curp_s = st.text_input("CURP")
            with col_fg2: num_tel = st.text_input("Teléfono")
            
            st.divider()
            st.subheader("📍 Ubicación")
            c6, c7, c8, c9 = st.columns([2, 1, 1, 1])
            with c6: calle_s = st.text_input("Calle")
            with c7: cr1s = st.text_input("Cruzamiento 1")
            with c8: cr2s = st.text_input("Cruzamiento 2")
            with c9: n_casa_s = st.text_input("No. Casa")
            
            zona_val_s = st.text_input("Fraccionamiento o Comisaría")
            ref_val_S = st.text_area("Referencias")
            

            col_r, col_j, col_s = st.columns(3)
            with col_r: rol_sel = st.selectbox("Rol", options=list(roles_dict.keys()))
            with col_j: jefe_sel = st.selectbox("Jefe Directo", options=list(jefes_opciones.keys()))
            with col_s: 
                # TAMBIÉN AQUÍ USAMOS LA LISTA DESPLEGABLE
                sec_s = st.selectbox("Asignar Sección", options=SECCIONES_YUCATAN)

            if st.form_submit_button("🚀 VINCULAR AL EQUIPO"):
                try:
                    nuevo_staff = {
                        "nombre": nombre_s, "apellido_paterno": ap_s, "apellido_materno":am_s, "curp": curp_s,
                        "telefono":num_tel, "calle":calle_s, "cruzamiento_1": cr1s, "cruzamiento_2": cr2s,
                        "numero_casa": n_casa_s, "fraccionamiento_comisaria": zona_val_s, "referencias":ref_val_S,
                        "id_rol": roles_dict[rol_sel],
                        "id_superior": jefes_opciones[jefe_sel], "id_capturista": uid_actual,
                        "seccion": sec_s, "apellido_materno": "", "telefono": "0", 
                        "calle": "", "cruzamiento_1": "", "cruzamiento_2": "", 
                        "numero_casa": "", "fraccionamiento_comisaria": "", "referencias": ""
                    }
                    supabase.table("personas").insert(nuevo_staff).execute()
                    st.success(f"Staff vinculado a la sección {sec_s}.")
                except Exception as e:
                    st.error(f"Error: {e}")

# --- 5. VISTA DE CAPTURAS RECIENTES (AL FINAL) ---
st.divider()
st.subheader("📋 Mis capturas recientes")
try:
    mis_datos = supabase.table("personas").select("nombre, apellido_paterno, seccion").eq("id_capturista", uid_actual).limit(5).execute()
    if mis_datos.data:
        st.table(mis_datos.data)
except:
    st.info("No hay registros previos.")