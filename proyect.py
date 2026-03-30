import pandas as pd
import io
import streamlit as st
from supabase import create_client

#comand: python -m streamlit run proyect.py

# --- 1. CREDENCIALES (MODO HÍBRIDO) ---
import os

# Intentamos sacar las llaves de st.secrets (para la web)
# Si no existen, usamos el texto directo (para tu compu)
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
except:
    # PEGA AQUÍ TUS LLAVES REALES PARA QUE FUNCIONE EN TU COMPU
    url = "https://movucqjgwjnsvsyivrls.supabase.co"
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." # Tu key completa
    
    
# Mantenemos la conexión "viva" para evitar retrasos en el primer clic
@st.cache_resource
def get_supabase():
    return create_client(url, key)

supabase = get_supabase()

st.set_page_config(page_title="Base de control movilizador", layout="wide")

# --- 2. LÓGICA DE ACCESO (OPTIMIZADA PARA 1 SOLO CLIC) ---
if "auth_user" not in st.session_state:
    st.session_state.auth_user = None

if st.session_state.auth_user is None:
    st.title("Acceso al Sistema")
    
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
        st.warning("Usuario autenticado pero no vinculado en la tabla 'personas'.")
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
# --- 4. CONFIGURACIÓN DE NAVEGACIÓN ---
# Solo el Maestro (5) y el Seccional (1) tienen acceso a la pestaña de descargas
pestañas_nombres = ["Registro", "Dashboard"]
if rol_cap == 1:
    pestañas_nombres.append("⚙️ Administración")
    pestañas_nombres.append("📥 Descargas")
elif rol_cap == 5:
    pestañas_nombres.append("⚙️ Administración Staff")
    pestañas_nombres.append("📥 Descargas Globales")

tabs = st.tabs(pestañas_nombres)
tab1 = tabs[0] # Registro
tab2 = tabs[1] # Dashboard
tab3 = tabs[2] if rol_cap in [1, 5] else None # Administración
tab4 = tabs[3] if rol_cap in [1, 5] else None # Descargas

# --- PESTAÑA 1: REGISTRO DE CIUDADANOS (ACTUALIZADO) ---
with tab1:
    st.subheader("Registro de Ciudadanos Promovidos")
    
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
        st.subheader("Asignación de Promotor")
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
            if nom and ap_p and curp_val and tel_val:
                # 1. LIMPIEZA: Quitamos espacios, guiones o paréntesis que el usuario pudo poner
                tel_limpio = tel_val.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
                curp_limpio = curp_val.strip().upper()
                
                # 2. VALIDACIÓN DE TELÉFONO
                if not (len(tel_limpio) == 10 and tel_limpio.isdigit()):
                    st.error("❌ **ERROR EN TELÉFONO**: Debe tener exactamente 10 números (ejemplo: 9991234567).")
                
                # 3. VALIDACIÓN DE CURP (Ya que estamos, validamos que tenga 18 caracteres)
                elif len(curp_limpio) != 18:
                    st.error("❌ **ERROR EN CURP**: Debe tener exactamente 18 caracteres.")
                else:
                
                    try:
                        # 2. VALIDACIÓN: Consultamos si ya existe alguien con ese CURP
                        # Buscamos solo el nombre y quién lo registró para informar al usuario
                        check_duplicado = supabase.table("personas").select("id").eq("curp", curp_limpio).execute()
                        
                        if check_duplicado.data:
                            # Si hay datos, significa que YA EXISTE
                            persona_ya_esta = check_duplicado.data[0]
                            st.error(f"⚠️ **ERROR: CIUDADANO YA REGISTRADO**")
                            st.info(f"Esta persona ya fue dada de alta como: **{persona_ya_esta['nombre']} {persona_ya_esta['apellido_paterno']}**")
                            
                        else:
                            # 3. SI NO EXISTE, PROCEDEMOS AL GUARDADO NORMAL
                            id_promotor_dueño = dict_promotores[promotor_asignado]
                            
                            data_insert = {
                                "nombre": nom.strip(),
                                "apellido_paterno": ap_p.strip(),
                                "apellido_materno": ap_m.strip(),
                                "curp": curp_limpio,
                                "telefono": tel_val,
                                "calle": calle_val,
                                "cruzamiento_1": cr1,
                                "cruzamiento_2": cr2,
                                "numero_casa": n_casa,
                                "fraccionamiento_comisaria": zona_val,
                                "referencias": ref_val,
                                "seccion": sec_val,
                                "id_rol": 4,
                                "id_capturista": uid_actual,
                                "id_superior": id_promotor_dueño
                            }
                            supabase.table("personas").insert(data_insert).execute()
                            st.success(f"✅ ¡Registro exitoso! {nom} ha sido añadido a la base de datos.")
                    
                    except Exception as e:
                        st.error(f"Error técnico: {e}")
            else:
                st.warning("⚠️ El Nombre, Apellido Paterno y CURP son obligatorios.")

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
            with col_n: nombre_s = st.text_input("Nombre Staff")
            with col_a: ap_s = st.text_input("Apellido Paterno Staff")
            with col_z: am_s = st.text_input("Apellido Materno Staff")
            
            col_fg, col_fg2 = st.columns(2)
            with col_fg: curp_s = st.text_input("CURP Staff")
            with col_fg2: num_tel = st.text_input("Teléfono Staff")
            
            st.divider()
            st.subheader("📍 Ubicación Staff")
            c6, c7, c8, c9 = st.columns([2, 1, 1, 1])
            with c6: calle_s = st.text_input("Calle Staff")
            with c7: cr1s = st.text_input("Cruzamiento 1 Staff")
            with c8: cr2s = st.text_input("Cruzamiento 2 Staff")
            with c9: n_casa_s = st.text_input("No. Casa Staff")
            
            zona_val_s = st.text_input("Fraccionamiento o Comisaría Staff")
            ref_val_S = st.text_area("Referencias Staff")
            
            col_r, col_j, col_s = st.columns(3)
            with col_r: rol_sel = st.selectbox("Rol Staff", options=list(roles_dict.keys()))
            with col_j: jefe_sel = st.selectbox("Jefe Directo Staff", options=list(jefes_opciones.keys()))
            with col_s: sec_s = st.selectbox("Asignar Sección Staff", options=SECCIONES_YUCATAN)

            if st.form_submit_button("VINCULAR AL EQUIPO"):
                # VALIDAMOS CON LAS VARIABLES DE ESTE FORMULARIO
                if nombre_s and ap_s and curp_s and num_tel:
                    tel_limpio_s = num_tel.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
                    curp_limpio_s = curp_s.strip().upper()
                
                    if not (len(tel_limpio_s) == 10 and tel_limpio_s.isdigit()):
                        st.error("❌ El teléfono debe tener 10 dígitos.")
                    elif len(curp_limpio_s) != 18:
                        st.error("❌ El CURP debe tener 18 caracteres.")
                    else:
                        try:
                            # Checamos duplicado de staff
                            check_dup = supabase.table("personas").select("id").eq("curp", curp_limpio_s).execute()
                            if check_dup.data:
                                st.error("⚠️ Este integrante de staff ya está registrado.")
                            else:
                                nuevo_staff = {
                                    "nombre": nombre_s.strip(),
                                    "apellido_paterno": ap_s.strip(),
                                    "apellido_materno": am_s.strip(),
                                    "curp": curp_limpio_s,
                                    "telefono": tel_limpio_s,
                                    "calle": calle_s,
                                    "cruzamiento_1": cr1s,
                                    "cruzamiento_2": cr2s,
                                    "numero_casa": n_casa_s,
                                    "fraccionamiento_comisaria": zona_val_s,
                                    "referencias": ref_val_S,
                                    "id_rol": roles_dict[rol_sel],
                                    "id_superior": jefes_opciones[jefe_sel],
                                    "id_capturista": uid_actual,
                                    "seccion": sec_s
                                }
                                supabase.table("personas").insert(nuevo_staff).execute()
                                st.success(f"✅ Staff {nombre_s} vinculado a la sección {sec_s}.")
                        except Exception as e:
                            st.error(f"Error técnico: {e}")
                else:
                    st.warning("⚠️ Llene los campos obligatorios del Staff.")
                    
                    
# --- PESTAÑA 4: CENTRO DE DESCARGAS (LOGICA MAESTRO VS SECCIONAL) ---
if tab4:
    with tab4:
        st.header("Exportar Base de Datos a Excel")
        st.info("El sistema generará un reporte con la información completa de ciudadanos y staff.")

        if st.button("Generar Reporte para Descarga"):
            with st.spinner("Procesando datos de Supabase..."):
                try:
                    if rol_cap == 5:
                        # EL MAESTRO DESCARGA ABSOLUTAMENTE TODO
                        res = supabase.table("personas").select("*").execute()
                        nombre_archivo = "BASE_DATOS_TOTAL_YUCATAN.xlsx"
                        desc_msg = "Reporte Global (Todas las secciones)"
                    else:
                        # EL SECCIONAL SOLO SU SECCION
                        mi_seccion = perfil.get('seccion')
                        res = supabase.table("personas").select("*").eq("seccion", mi_seccion).execute()
                        nombre_archivo = f"REPORTE_SECCION_{mi_seccion}.xlsx"
                        desc_msg = f"Reporte exclusivo de la Sección {mi_seccion}"

                    if res.data:
                        # Convertimos a Pandas para manipularlo
                        df = pd.DataFrame(res.data)

                        # 1. LIMPIEZA DE COLUMNAS (Para que el cliente vea un Excel limpio)
                        columnas_borrar = ['id', 'id_auth', 'id_superior', 'id_capturista']
                        df = df.drop(columns=[c for c in columnas_borrar if c in df.columns])

                        # 2. TRADUCCIÓN DE ROLES (Opcional, para que no salgan números 1, 2, 3...)
                        mapa_roles = {1: "Seccional", 2: "Territorial", 3: "Promotor", 4: "Promovido", 5: "Administrador"}
                        df['id_rol'] = df['id_rol'].map(mapa_roles)

                        # 3. REORDENAR COLUMNAS PARA EL CLIENTE
                        orden = [
                            'nombre', 'apellido_paterno', 'apellido_materno', 'curp', 
                            'telefono', 'id_rol', 'seccion', 'fraccionamiento_comisaria', 
                            'calle', 'numero_casa', 'fecha_registro'
                        ]
                        df = df[[c for c in orden if c in df.columns]]

                        # 4. CREAR EXCEL EN MEMORIA
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            df.to_excel(writer, index=False, sheet_name='Base_Datos')
                        
                        excel_data = output.getvalue()

                        st.success(f"✅ {desc_msg} generado con {len(df)} registros.")
                        
                        # BOTÓN DE DESCARGA FINAL
                        st.download_button(
                            label="💾 GUARDAR ARCHIVO EXCEL",
                            data=excel_data,
                            file_name=nombre_archivo,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    else:
                        st.warning("No se encontraron datos disponibles para descargar.")
                        
                except Exception as e:
                    st.error(f"Error al procesar el Excel: {e}")
                        

# --- 5. VISTA DE CAPTURAS RECIENTES (AL FINAL) ---
st.divider()
st.subheader("📋 Mis capturas recientes")
try:
    mis_datos = supabase.table("personas").select("nombre, apellido_paterno, seccion").eq("id_capturista", uid_actual).limit(5).execute()
    if mis_datos.data:
        st.table(mis_datos.data)
except:
    st.info("No hay registros previos.")