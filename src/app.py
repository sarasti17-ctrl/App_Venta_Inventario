import streamlit as st
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import hashlib
import pandas as pd
from utils_pdf import TicketGenerator
import io
import os
import plotly.express as px
import plotly.graph_objects as go
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
import extra_streamlit_components as stc

# Configuración de la página
st.set_page_config(
    page_title="Sarasti - Gestión de Inventario",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos dinámicos según el modo (Light/Dark)
dark_mode = st.session_state.get('dark_mode', False)

if dark_mode:
    # DARK MODE CSS
    bg_gradient = "linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%)"
    card_bg = "rgba(30, 30, 50, 0.8)"
    text_color = "#ffffff"
    sidebar_bg = "#1e1e2f"
    form_bg = "#2d2d44"
    border_color = "rgba(255, 255, 255, 0.1)"
    metric_text = "#00d4ff"
else:
    # LIGHT MODE CSS
    bg_gradient = "linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)"
    card_bg = "rgba(255, 255, 255, 0.7)"
    text_color = "#1a1a1a"
    sidebar_bg = "#ffffff"
    form_bg = "#ffffff"
    border_color = "rgba(255, 255, 255, 0.3)"
    metric_text = "#1a2a6c"

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&display=swap');
    
    html, body, [class*="css"], .stMarkdown, p, h1, h2, h3, h4, h5, h6, label, span, div {{
        font-family: 'Outfit', sans-serif;
        color: {text_color} !important;
    }}
    
    /* Fondo global de la aplicación */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
        background: {bg_gradient} !important;
    }}
    
    .main {{
        background: transparent !important;
    }}
    
    /* Glassmorphism Metrics */
    div[data-testid="stVerticalBlock"] > div:has(div.stMetric) {{
        background: {card_bg};
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 20px;
        border: 1px solid {border_color};
        transition: transform 0.3s ease;
    }}
    
    div[data-testid="stVerticalBlock"] > div:has(div.stMetric):hover {{
        transform: translateY(-5px);
    }}

    div[data-testid="stMetricValue"] > div {{
        color: {metric_text} !important;
    }}
    
    /* Botones Premium */
    .stButton>button {{
        width: 100%;
        border-radius: 12px;
        height: 3.5em;
        background: linear-gradient(45deg, #1a2a6c, #b21f1f, #fdbb2d);
        background-size: 200% 200%;
        color: white !important;
        font-weight: 600;
        border: none;
        transition: all 0.4s ease;
        animation: Gradient 5s ease infinite;
    }}
    
    @keyframes Gradient {{
        0% {{background-position: 0% 50%}}
        50% {{background-position: 100% 50%}}
        100% {{background-position: 0% 50%}}
    }}
    
    .stButton>button:hover {{
        transform: scale(1.02);
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
    }}
    
    /* Sidebar */
    section[data-testid="stSidebar"] {{
        background-color: {sidebar_bg};
        border-right: 1px solid {border_color};
    }}

    section[data-testid="stSidebar"] .stMarkdown p {{
        color: {text_color} !important;
    }}
    
    /* Form */
    div[data-testid="stForm"] {{
        background: {form_bg};
        padding: 30px;
        border-radius: 20px;
        box-shadow: 0 15px 35px rgba(0,0,0,0.1);
        border: 1px solid {border_color};
    }}

    /* Inputs y Selects en Dark Mode */
    {' div[data-baseweb="input"], div[data-baseweb="select"], textarea { background-color: #3d3d5c !important; color: white !important; }' if dark_mode else ''}
    
    /* Corregir visibilidad de Dataframes en Dark Mode */
    {'.stDataFrame div { color: white !important; }' if dark_mode else ''}
    
    /* Alertas menos brillantes */
    .stAlert {{
        background-color: {card_bg} !important;
        color: {text_color} !important;
        border: 1px solid {border_color} !important;
    }}
    </style>
""", unsafe_allow_html=True)

# Manejo de conexión a BD
def get_db_connection():
    try:
        if "mysql" not in st.secrets:
            st.error("❌ Error: No se encontró la sección [mysql] en los secretos (Secrets).")
            return None
            
        config = st.secrets["mysql"]
        conn = mysql.connector.connect(
            host=config["host"],
            port=config["port"],
            user=config["user"],
            password=config["password"],
            database=config["database"],
            connect_timeout=10
        )
        return conn
    except Error as e:
        host_tried = st.secrets.get("mysql", {}).get("host", "N/A")
        st.error(f"❌ Error de conexión (Host: {host_tried}): {e}")
        return None
    except Exception as e:
        st.error(f"❌ Error inesperado: {e}")
        return None

# Inicialización de CookieManager
def get_cookie_manager():
    return stc.CookieManager()

cookie_manager = get_cookie_manager()

# Funciones de Autenticación
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_login(username, password):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        # Usamos SHA2 de MySQL para validar el password de forma segura
        query = """
            SELECT id, username, rol, nombre_completo 
            FROM usuarios 
            WHERE username = %s 
            AND password_hash = SHA2(%s, 256) 
            AND activo = 1
        """
        cursor.execute(query, (username, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        return user
    return None

def check_auto_login():
    """Verifica si existe una cookie de sesión válida para auto-login."""
    if st.session_state.authenticated:
        return

    # Usar get_all() que suele ser más reactivo en Streamlit
    cookies = cookie_manager.get_all()
    
    # Si no hay cookies aún, el componente podría estar cargando
    if not cookies:
        return

    session_user = cookies.get("sarasti_session")
    
    if session_user:
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                query = "SELECT id, username, rol, nombre_completo FROM usuarios WHERE username = %s AND activo = 1"
                cursor.execute(query, (session_user,))
                user = cursor.fetchone()
                cursor.close()
                conn.close()
                
                if user:
                    st.session_state.authenticated = True
                    st.session_state.user = user
                    # Importante: rerun para refrescar la UI con el nuevo estado
                    st.rerun()
            except Exception:
                pass

# Inicialización de estado de sesión
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user' not in st.session_state:
    st.session_state.user = None
if 'basket' not in st.session_state:
    st.session_state.basket = []
if 'last_ticket' not in st.session_state:
    st.session_state.last_ticket = None
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False

# UI de Login
def login_page():
    st.markdown("<div style='height: 100px'></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h1 style='text-align: center;'>📦 Sarasti</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #666;'>Gestión de Inventario Collec</p>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            remember_me = st.checkbox("Recordarme", value=True)
            submit = st.form_submit_button("Iniciar Sesión")
            
            if submit:
                # Caso especial para desarrollo inicial o validación real
                user = check_login(username, password)
                if user:
                    st.session_state.authenticated = True
                    st.session_state.user = user
                    
                    if remember_me:
                        # Guardar cookie por 30 días
                        cookie_manager.set(
                            cookie="sarasti_session", 
                            val=username, 
                            expires_at=datetime.now() + pd.Timedelta(days=30)
                        )
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos")
        
        # Diagnóstico para la nube
        with st.expander("🛠️ Diagnóstico del Sistema (Soporte)"):
            st.write(f"**Entorno:** {'Nube' if os.path.exists('/mount/src') else 'Local'}")
            if "mysql" in st.secrets:
                host = st.secrets["mysql"]["host"]
                st.write(f"**Base de Datos (Host):** `{host[:5]}...{host[-5:] if len(host) > 10 else ''}`")
                if st.button("Probar Conexión Ahora"):
                    c = get_db_connection()
                    if c:
                        st.success("✅ Conexión exitosa a la base de datos")
                        c.close()
                    else:
                        st.error("❌ Falló la conexión")
            else:
                st.error("❌ Sección [mysql] NO encontrada en st.secrets")

# Dashboard Principal
def main_dashboard():
    # Sidebar con navegación y perfil
    with st.sidebar:
        logo_path = os.path.join("data", "LogoCollec.jpg")
        if os.path.exists(logo_path):
            st.image(logo_path, use_container_width=True)
        else:
            st.title("🛡️ Sarasti")
            
        st.write(f"**Usuario:** {st.session_state.user['nombre_completo']}")
        st.write(f"**Rol:** {st.session_state.user['rol']}")
        st.divider()
        
        # Toggle de Modo Oscuro (Streamlit maneja el rerun automático con la key)
        st.toggle("🌙 Modo Oscuro", key="dark_mode")
        
        st.divider()
        
        if st.session_state.user['rol'] == 'CLIENTE':
            menu = ["🔍 Consulta de Inventario"]
        else:
            menu = ["📊 Dashboard", "🔍 Consulta de Inventario", "💰 Registrar Venta", "📝 Gestión de Ventas"]
            if st.session_state.user['rol'] == 'ADMIN':
                menu.append("👥 Gestión de Usuarios")
                menu.append("📈 Reportes")
                menu.append("🔄 Sincronización Espejo")
                menu.append("📤 Carga Masiva (Excel)")
                menu.append("✏️ Editar Materiales")
                menu.append("📋 Edición Masiva (Tabla)")
        
        menu.append("❓ Ayuda / Tutorial")
            
        choice = st.radio("Navegación", menu)
        
        if st.button("Cerrar Sesión"):
            # Eliminar cookie de sesión (con manejo de error si no existe)
            try:
                cookie_manager.delete(cookie="sarasti_session")
            except Exception:
                pass
            st.session_state.authenticated = False
            st.session_state.user = None
            st.rerun()

    # Contenido según elección
    if choice == "📊 Dashboard":
        show_stats()
    elif choice == "🔍 Consulta de Inventario":
        show_inventory()
    elif choice == "💰 Registrar Venta":
        show_sales_form()
    elif choice == "📝 Gestión de Ventas":
        show_sales_management()
    elif choice == "👥 Gestión de Usuarios":
        show_user_management()
    elif choice == "📈 Reportes":
        show_reports()
    elif choice == "🔄 Sincronización Espejo":
        show_sync_page()
    elif choice == "📤 Carga Masiva (Excel)":
        show_inventory_upload()
    elif choice == "✏️ Editar Materiales":
        show_inventory_edit()
    elif choice == "📋 Edición Masiva (Tabla)":
        show_inventory_bulk_edit()
    elif choice == "❓ Ayuda / Tutorial":
        show_help_page()

def show_help_page():
    st.title("❓ Centro de Ayuda")
    try:
        with open("GUIA_USUARIO.md", "r", encoding="utf-8") as f:
            content = f.read()
            st.markdown(content)
    except FileNotFoundError:
        st.error("Manual no encontrado. Por favor contacte al administrador.")

def show_reports():
    st.title("📈 Reportes y Análisis")
    
    conn = get_db_connection()
    if not conn:
        return

    # 1. KPIs Rápidos
    query_stats = """
        SELECT 
            COUNT(*) AS total_items,
            SUM(monto_total) AS monto_total,
            SUM(monto_total) AS monto_recuperado
        FROM v_progreso_liquidacion
    """
    # Nota: v_progreso_liquidacion ya debería estar filtrando, pero recargamos datos para KPIS específicos si es necesario
    query_stats = """
        SELECT 
            COUNT(*) AS total_items,
            SUM(cantidad_actual * precio_unitario) AS valor_inventario_actual,
            (SELECT SUM(monto_total) FROM ventas WHERE estado = 'COMPLETADA') AS monto_recuperado,
            (SELECT COUNT(*) FROM ventas WHERE estado = 'COMPLETADA') AS ventas_completadas
        FROM materiales
        WHERE cantidad_actual > 0
    """
    df_stats = pd.read_sql(query_stats, conn)
    
    if not df_stats.empty:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Ítems en Liquidación", df_stats['total_items'][0])
        with c2:
            st.metric("Ventas Totales", df_stats['ventas_completadas'][0])
        with c3:
            recuperado = df_stats['monto_recuperado'][0] or 0
            st.metric("Monto Recuperado", f"${recuperado:,.2f}")

    st.divider()

    # 2. Gráficas
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("📊 Ventas por Categoría")
        query_cat = """
            SELECT m.categoria_hoja, SUM(vd.subtotal) as total 
            FROM ventas_detalle vd 
            JOIN materiales m ON vd.id_material = m.id 
            GROUP BY m.categoria_hoja
        """
        df_cat = pd.read_sql(query_cat, conn)
        if not df_cat.empty:
            fig = px.pie(df_cat, values='total', names='categoria_hoja', hole=.3,
                        color_discrete_sequence=px.colors.sequential.RdBu,
                        template='plotly_dark' if dark_mode else 'plotly_white')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sin datos de ventas aún.")

    with col_b:
        st.subheader("📅 Tendencia de Ventas (Diario)")
        query_trend = """
            SELECT DATE(fecha_venta) as fecha, SUM(monto_total) as total 
            FROM ventas 
            GROUP BY DATE(fecha_venta)
            ORDER BY fecha ASC
        """
        df_trend = pd.read_sql(query_trend, conn)
        if not df_trend.empty:
            fig = px.line(df_trend, x='fecha', y='total', markers=True,
                         line_shape='spline', render_mode='svg',
                         template='plotly_dark' if dark_mode else 'plotly_white')
            fig.update_traces(line_color='#007bff')
            fig.update_xaxes(tickformat="%d-%m-%y")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sin datos históricos aún.")

    st.divider()

    # 3. Materiales de Alto Valor (Top 100)
    st.subheader("💎 Top 100 Materiales de Mayor Valor")
    st.write("Lista de materiales con mayor inversión en inventario (Stock x Precio), ordenados de mayor a menor.")
    query_alto_valor = """
        SELECT 
            codigo_interno, 
            descripcion, 
            categoria_hoja, 
            medida,
            marca,
            color,
            cantidad_actual, 
            unidad_medida,
            precio_unitario,
            (cantidad_actual * precio_unitario) as valor_total
        FROM materiales 
        WHERE cantidad_actual > 0
        ORDER BY valor_total DESC 
        LIMIT 100
    """
    df_valor = pd.read_sql(query_alto_valor, conn)
    if not df_valor.empty:
        # Formatear para visualización
        st.dataframe(
            df_valor, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "codigo_interno": "Código",
                "descripcion": "Descripción",
                "categoria_hoja": "Categoría",
                "medida": "Medida",
                "marca": "Marca",
                "color": "Color",
                "cantidad_actual": st.column_config.NumberColumn("Stock", format="%.1f"),
                "precio_unitario": st.column_config.NumberColumn("Precio U.", format="$%.2f"),
                "valor_total": st.column_config.NumberColumn("Valor Inventario", format="$%.0f")
            }
        )
    else:
        st.info("No hay materiales con stock actualmente.")

    conn.close()

def show_user_management():
    st.title("👥 Gestión de Usuarios")
    
    tab1, tab2 = st.tabs(["📋 Lista de Usuarios", "➕ Crear Usuario"])
    
    with tab1:
        conn = get_db_connection()
        if conn:
            query = "SELECT id, username, nombre_completo, rol, activo FROM usuarios"
            df = pd.read_sql(query, conn)
            
            st.dataframe(
                df, 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "activo": st.column_config.CheckboxColumn("Activo")
                }
            )
            
            st.divider()
            st.subheader("🔑 Cambiar Contraseña / Gestionar")
            col1, col2 = st.columns(2)
            with col1:
                user_to_mod = st.selectbox("Seleccionar Usuario", df['username'])
                new_pass = st.text_input("Nueva Contraseña", type="password")
            with col2:
                new_status = st.toggle("Cuenta Activa", value=True)
                if st.button("Actualizar Usuario"):
                    try:
                        cursor = conn.cursor()
                        if new_pass:
                            cursor.execute("UPDATE usuarios SET password_hash = SHA2(%s, 256), activo = %s WHERE username = %s", 
                                         (new_pass, 1 if new_status else 0, user_to_mod))
                        else:
                            cursor.execute("UPDATE usuarios SET activo = %s WHERE username = %s", 
                                         (1 if new_status else 0, user_to_mod))
                        conn.commit()
                        st.success(f"Usuario {user_to_mod} actualizado")
                        st.rerun()
                    except Error as e:
                        st.error(f"Error: {e}")
            conn.close()

    with tab2:
        with st.form("new_user_form"):
            st.subheader("Datos del Nuevo Usuario")
            u_name = st.text_input("Username")
            u_full = st.text_input("Nombre Completo")
            u_rol = st.selectbox("Rol", ["VENDEDOR", "ADMIN", "CLIENTE"])
            u_pass = st.text_input("Contraseña Inicial", type="password")
            
            if st.form_submit_button("Guardar Usuario"):
                if u_name and u_pass:
                    conn = get_db_connection()
                    if conn:
                        try:
                            cursor = conn.cursor()
                            query = """
                                INSERT INTO usuarios (username, password_hash, nombre_completo, rol, activo) 
                                VALUES (%s, SHA2(%s, 256), %s, %s, 1)
                            """
                            cursor.execute(query, (u_name, u_pass, u_full, u_rol))
                            conn.commit()
                            st.success(f"Usuario {u_name} creado exitosamente")
                        except Error as e:
                            st.error(f"Error al crear usuario: {e}")
                        finally:
                            conn.close()
                else:
                    st.warning("Username y Contraseña son obligatorios")

def show_stats():
    st.title("Resumen General")
    conn = get_db_connection()
    if conn:
        query = """
            SELECT 
                COUNT(*) AS total_items,
                SUM(cantidad_actual * precio_unitario) AS valor_inventario_actual,
                (SELECT SUM(monto_total) FROM ventas WHERE estado = 'COMPLETADA') AS monto_recuperado,
                (SELECT COUNT(*) FROM ventas WHERE estado = 'COMPLETADA') AS ventas_completadas
            FROM materiales
            WHERE cantidad_actual > 0
        """
        df = pd.read_sql(query, conn)
        conn.close()
        
        if not df.empty:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📦 Total de Ítems", f"{df['total_items'][0]:,}")
            with col2:
                monto = df['monto_recuperado'][0] or 0
                st.metric("💰 Monto Recuperado", f"${monto:,.2f}", 
                         delta=f"{monto/1000:,.1f}k", 
                         delta_color="normal" if not dark_mode else "inverse")
            with col3:
                st.metric("🚀 Ventas Realizadas", df['ventas_completadas'][0])

def show_sync_page():
    st.title("🔄 Sincronización de Base de Datos")
    st.markdown("""
    Esta herramienta permite copiar todos los datos desde **Clever Cloud** (Nube) hacia tu **PC Local** (Espejo).
    
    > [!IMPORTANT]
    > Al sincronizar, la base de datos de tu computadora será sobreescrita con la información actual de la nube.
    """)
    
    # Verificar si estamos en la nube
    is_cloud = os.path.exists("/mount/src")
    
    if is_cloud:
        st.error("🚫 **Sincronización Deshabilitada en la Nube**")
        st.warning("Esta herramienta solo puede ejecutarse cuando usas la App **en tu PC local**. Los servidores de la nube no tienen permiso para entrar a tu red privada y escribir en tu base de datos local.")
        st.info("Para sincronizar, abre una terminal en tu PC y corre: `streamlit run src/app.py`")
        return
    
    try:
        from sync_mirror import MirrorSync
    except ImportError:
        st.error("❌ No se encontró el módulo de sincronización. Asegúrate de que `sqlalchemy` esté instalado.")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.info("💡 La aplicación principal ya está trabajando con Clever Cloud. Usa esto solo para tener un respaldo local actualizado.")
        
        if st.button("🚀 Iniciar Sincronización a PC Local"):
            try:
                cloud_cfg = st.secrets["mysql"]
                local_cfg = st.secrets["mysql_local"]
                
                with st.status("Sincronizando mundos...", expanded=True) as status:
                    st.write("🔗 Conectando a ambos servidores...")
                    syncer = MirrorSync(cloud_cfg, local_cfg)
                    
                    st.write("📑 Procesando tablas y transfiriendo datos...")
                    success, results = syncer.run_sync()
                    
                    if success:
                        status.update(label="✅ Sincronización Completa", state="complete", expanded=False)
                        st.success("¡Tu PC local ahora es un espejo exacto de la nube!")
                        
                        # Mostrar resumen
                        st.subheader("📊 Datos transferidos:")
                        for table, count in results.items():
                            st.write(f"- **{table}**: {count} registros")
                    else:
                        status.update(label="❌ Falló la Sincronización", state="error")
                        st.error(f"Error técnico: {results}")
            except Exception as e:
                st.error(f"Error de configuración: {e}")
    
    with col2:
        st.subheader("Estado de Conexión")
        st.write("🌐 **Maestra:** Clever Cloud (Activa)")
        st.write("💻 **Espejo:** MySQL Local")
        
        if st.button("🔌 Probar Conexiones"):
            try:
                # Probar Cloud
                mysql.connector.connect(**st.secrets["mysql"]).close()
                st.success("Cloud: OK")
                # Probar Local
                mysql.connector.connect(**st.secrets["mysql_local"]).close()
                st.success("Local: OK")
            except Exception as e:
                st.error(f"Error: {e}")

def show_inventory():
    st.title("📦 Consulta de Inventario")
    
    conn = get_db_connection()
    if conn:
        # Filtros base
        query_cats = "SELECT DISTINCT categoria_hoja FROM materiales WHERE cantidad_actual > 0"
        cats_df = pd.read_sql(query_cats, conn)
        
        col1, col2 = st.columns([1, 2])
        with col1:
            categoria = st.selectbox("Categoría", ["Todas"] + list(cats_df['categoria_hoja']))
        with col2:
            search = st.text_input("Buscar por código o descripción")
        
        # --- BÚSQUEDA AVANZADA ---
        with st.expander("🔍 Filtros Avanzados (Marca, Color, Medida, Rangos)"):
            c1, c2, c3, c4 = st.columns(4)
            
            # Obtener listas únicas para los selectores (de forma eficiente)
            with c1:
                marcas = pd.read_sql("SELECT DISTINCT marca FROM materiales WHERE marca IS NOT NULL AND marca != '' AND cantidad_actual > 0", conn)
                marca_sel = st.selectbox("Marca", ["Todas"] + list(marcas['marca']))
            with c2:
                colores = pd.read_sql("SELECT DISTINCT color FROM materiales WHERE color IS NOT NULL AND color != '' AND cantidad_actual > 0", conn)
                color_sel = st.selectbox("Color", ["Todas"] + list(colores['color']))
            with c3:
                medidas = pd.read_sql("SELECT DISTINCT medida FROM materiales WHERE medida IS NOT NULL AND medida != '' AND cantidad_actual > 0", conn)
                medida_sel = st.selectbox("Medida", ["Todas"] + list(medidas['medida']))
            with c4:
                propiedades = pd.read_sql("SELECT DISTINCT propiedad FROM materiales WHERE propiedad IS NOT NULL AND propiedad != '' AND cantidad_actual > 0", conn)
                prop_sel = st.selectbox("Propiedad", ["Todas"] + list(propiedades['propiedad']))
            
            st.divider()
            c_p1, c_p2, c_s1, c_s2 = st.columns(4)
            with c_p1:
                p_min = st.number_input("Precio Mín ($)", min_value=0.0, value=0.0, step=10.0)
            with c_p2:
                p_max = st.number_input("Precio Máx ($)", min_value=0.0, value=1000000.0, step=10.0)
            with c_s1:
                s_min = st.number_input("Stock Mín", min_value=0.0, value=0.0, step=1.0)
            with c_s2:
                s_max = st.number_input("Stock Máx", min_value=0.0, value=1000000.0, step=1.0)

        # Construir query dinámica
        query = """
            SELECT 
                id,
                codigo_interno,
                descripcion, 
                categoria_hoja, 
                medida,
                marca,
                color,
                propiedad,
                cantidad_actual, 
                unidad_medida, 
                precio_unitario,
                (cantidad_actual * precio_unitario) as importe
            FROM materiales 
            WHERE cantidad_actual > 0
        """
        params = []
        
        # Aplicar filtros
        if categoria != "Todas":
            query += " AND categoria_hoja = %s"
            params.append(categoria)
        
        if search:
            query += " AND (codigo_interno LIKE %s OR descripcion LIKE %s)"
            params.append(f"%{search}%")
            params.append(f"%{search}%")

        if marca_sel != "Todas":
            query += " AND marca = %s"
            params.append(marca_sel)
            
        if color_sel != "Todas":
            query += " AND color = %s"
            params.append(color_sel)
            
        if medida_sel != "Todas":
            query += " AND medida = %s"
            params.append(medida_sel)

        if prop_sel != "Todas":
            query += " AND propiedad = %s"
            params.append(prop_sel)

        # Filtros de rangos
        if p_min > 0:
            query += " AND precio_unitario >= %s"
            params.append(p_min)
        if p_max < 1000000:
            query += " AND precio_unitario <= %s"
            params.append(p_max)
        if s_min > 0:
            query += " AND cantidad_actual >= %s"
            params.append(s_min)
        if s_max < 1000000:
            query += " AND cantidad_actual <= %s"
            params.append(s_max)
            
        query += " ORDER BY descripcion ASC"
            
        # Ejecutar usando motor de pandas para visualización
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params)
        data = cursor.fetchall()
        df = pd.DataFrame(data)
        conn.close()
        
        if not df.empty:
            # Convertir decimales a flotantes para evitar errores de renderizado
            for col in ['cantidad_actual', 'precio_unitario', 'importe']:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            # --- CONFIGURACIÓN DE AGGRID ---
            gb = GridOptionsBuilder.from_dataframe(df)
            gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=20)
            gb.configure_side_bar() # Agrega filtros laterales también
            gb.configure_default_column(
                resizable=True,
                filter=True,
                sortable=True,
                editable=False,
            )
            
            # Formateo de columnas en AgGrid
            gb.configure_column("id", hide=True)
            gb.configure_column("codigo_interno", hide=True)
            gb.configure_column("propiedad", hide=True)
            
            gb.configure_column("descripcion", headerName="Descripción", minWidth=300, pinned='left')
            gb.configure_column("categoria_hoja", headerName="Categoría")
            gb.configure_column("medida", headerName="Medida")
            gb.configure_column("marca", headerName="Marca")
            gb.configure_column("color", headerName="Color")
            gb.configure_column("cantidad_actual", headerName="Cantidad", type=["numericColumn", "numberColumnFilter"], valueFormatter="x.toLocaleString()")
            gb.configure_column("unidad_medida", headerName="Unidad")
            gb.configure_column("precio_unitario", headerName="Precio U.", type=["numericColumn", "numberColumnFilter"], valueFormatter="'$' + x.toLocaleString()")
            gb.configure_column("importe", headerName="Importe Total", type=["numericColumn", "numberColumnFilter"], valueFormatter="'$' + x.toLocaleString()")
            
            gridOptions = gb.build()
            
            # Renderizar AgGrid
            grid_response = AgGrid(
                df,
                gridOptions=gridOptions,
                data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
                update_mode=GridUpdateMode.MODEL_CHANGED,
                fit_columns_on_grid_load=True,
                theme='alpine' if not dark_mode else 'balham', 
                enable_enterprise_modules=False,
                height=500,
                width='100%'
            )

            # Obtener el dataframe filtrado/ordenado
            df_filtered = grid_response['data']

            # Botón de exportación a CSV
            if df_filtered is not None and not df_filtered.empty:
                csv_data = df_filtered.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button(
                    label="📥 Exportar a CSV (Vista Actual)",
                    data=csv_data,
                    file_name=f"inventario_sarasti_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    key="export_csv_btn"
                )

            # Mostrar Totales
            st.divider()
            
            t_col1, t_col2, t_col3 = st.columns([1, 1, 1])
            with t_col1:
                st.metric("Total Registros", len(df_filtered) if df_filtered is not None else 0)
            with t_col2:
                total_cant = df_filtered['cantidad_actual'].sum() if df_filtered is not None else 0
                st.metric("Total Cantidad", f"{total_cant:,.1f}")
            with t_col3:
                total_imp = df_filtered['importe'].sum() if df_filtered is not None else 0
                st.metric("Total Importe", f"${total_imp:,.0f}")
        else:
            st.warning("No se encontraron resultados")

# Función para registrar venta multi-artículo
def register_sale(client_data, items):
    conn = get_db_connection()
    if not conn:
        return "Error de conexión"
    
    try:
        cursor = conn.cursor()
        conn.start_transaction()
        
        # 1. Calcular Totales
        subtotal_venta = sum(item['subtotal'] for item in items)
        descuento_global = float(client_data.get('descuento', 0))
        total_final = subtotal_venta * (1 - descuento_global/100)
        
        # 2. Insertar Cabecera (ventas)
        query_header = """
            INSERT INTO ventas (cliente, telefono_cliente, email_cliente, condiciones, forma_pago, responsable_id, monto_total, descuento_global)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query_header, (
            client_data['cliente'],
            client_data['telefono'],
            client_data['email'],
            client_data['condiciones'],
            client_data['forma_pago'],
            st.session_state.user['id'],
            total_final,
            descuento_global
        ))
        id_venta = cursor.lastrowid
        
        # 3. Procesar cada ítem
        for item in items:
            # Bloquear material para evitar sobreventa (SELECT FOR UPDATE)
            cursor.execute("SELECT cantidad_actual FROM materiales WHERE id = %s FOR UPDATE", (item['id_material'],))
            res = cursor.fetchone()
            if not res or res[0] < item['cantidad']:
                conn.rollback()
                material_desc = item.get('descripcion', f"ID {item['id_material']}")
                return f"Stock insuficiente para: {material_desc}"
            
            # Insertar Detalle
            query_detail = """
                INSERT INTO ventas_detalle (id_venta, id_material, cantidad, precio_unitario, subtotal)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query_detail, (
                id_venta,
                item['id_material'],
                item['cantidad'],
                item['precio_unitario'],
                item['subtotal']
            ))
            
            # Actualizar Stock
            cursor.execute("UPDATE materiales SET cantidad_actual = cantidad_actual - %s WHERE id = %s",
                         (item['cantidad'], item['id_material']))
            
        # 4. Registrar en Log
        cursor.execute("INSERT INTO log_actividad (usuario_id, accion, tabla_afectada, registro_id, descripcion) VALUES (%s, %s, %s, %s, %s)",
                     (st.session_state.user['id'], 'VENTA', 'ventas', id_venta, f"Venta multi-item a {client_data['cliente']}"))
        
        conn.commit()
        return "EXITO"
        
    except Error as e:
        if conn: conn.rollback()
        return f"Error SQL: {e}"
    finally:
        if 'cursor' in locals(): cursor.close()
        conn.close()

def show_sales_form():
    st.title("💰 Registro de Venta (Múltiples Artículos)")
    
    # 1. Búsqueda y Selección
    col_sel, col_cart = st.columns([1, 1])
    
    with col_sel:
        st.subheader("🛒 Agregar al Carrito")
        search_q = st.text_input("Buscar material (Código o Descripción)", key="sale_search")
        
        if search_q:
            conn = get_db_connection()
            if conn:
                query = """
                    SELECT id, codigo_interno, descripcion, cantidad_actual, unidad_medida, precio_unitario 
                    FROM materiales 
                    WHERE (codigo_interno LIKE %s OR descripcion LIKE %s)
                    AND cantidad_actual > 0
                    LIMIT 20
                """
                search_val = f"%{search_q}%"
                cursor = conn.cursor(dictionary=True)
                cursor.execute(query, (search_val, search_val))
                results = cursor.fetchall()
                conn.close()
                
                if results:
                    # Crear lista de opciones legibles
                    options = {f"[{r['codigo_interno']}] {r['descripcion']} (Stock: {r['cantidad_actual']} {r['unidad_medida']})": r for r in results}
                    
                    selection = st.selectbox("Seleccione el material específico", options.keys())
                    selected_item = options[selection]
                    
                    # Formulario de adición para el ítem seleccionado
                    col_q, col_p = st.columns(2)
                    with col_q:
                        # Valor por defecto seguro: 1.0 o el máximo si el stock es < 1
                        default_q = min(1.0, float(selected_item['cantidad_actual']))
                        cant = st.number_input(f"Cantidad ({selected_item['unidad_medida']})", 
                                             min_value=0.001, 
                                             max_value=float(selected_item['cantidad_actual']), 
                                             value=default_q,
                                             format="%.3f",
                                             step=0.001)
                    with col_p:
                        prec = st.number_input("Precio ($)", min_value=0.0, 
                                             value=float(selected_item['precio_unitario']),
                                             format="%.2f",
                                             step=0.01)
                    
                    if st.button("➕ Añadir al Carrito"):
                        item_cart = {
                            'id_material': selected_item['id'],
                            'codigo_interno': selected_item['codigo_interno'],
                            'descripcion': selected_item['descripcion'],
                            'unidad_medida': selected_item['unidad_medida'],
                            'cantidad': cant,
                            'precio_unitario': prec,
                            'subtotal': cant * prec
                        }
                        st.session_state.basket.append(item_cart)
                        st.success(f"{selected_item['codigo_interno']} añadido al carrito")
                        st.rerun()
                else:
                    st.warning("No se encontraron materiales con stock disponible")

    with col_cart:
        st.subheader("📋 Resumen del Carrito")
        if st.session_state.basket:
            total_basket = 0
            for i, item in enumerate(st.session_state.basket):
                col1, col2, col3 = st.columns([3, 1, 1])
                col1.write(f"**{item['codigo_interno']}** - {item['descripcion']}")
                col2.write(f"{item['cantidad']} x ${item['precio_unitario']:.2f}")
                if col3.button("🗑️", key=f"rem_{i}"):
                    st.session_state.basket.pop(i)
                    st.rerun()
                total_basket += item['subtotal']
            
            st.divider()
            st.markdown(f"### Subtotal: :blue[${total_basket:,.2f}]")
            
            if st.button("🔴 Vaciar Carrito"):
                st.session_state.basket = []
                st.rerun()
        else:
            st.info("El carrito está vacío")

    # 2. Datos del Cliente y Finalización
    if st.session_state.basket:
        st.divider()
        st.subheader("3. Confirmar Venta")
        
        with st.form("confirm_sale_form"):
            col1, col2 = st.columns(2)
            with col1:
                cliente = st.text_input("Nombre del Cliente")
                telefono = st.text_input("Teléfono")
                email = st.text_input("Email")
            with col2:
                forma_pago = st.selectbox("Forma de Pago", ["EFECTIVO", "TRANSFERENCIA", "TARJETA", "DEVOLUCIÓN"])
                descuento = st.slider("Descuento Global (%)", 0, 100, 0)
                condiciones = st.text_area("Condiciones / Observaciones")
            
            if st.form_submit_button("🚀 Finalizar y Generar Ticket"):
                if not cliente:
                    st.error("Nombre del cliente obligatorio")
                else:
                    # Limpiar ticket previo
                    st.session_state.last_ticket = None
                    
                    client_data = {
                        'cliente': cliente,
                        'telefono': telefono,
                        'email': email,
                        'forma_pago': forma_pago,
                        'descuento': descuento,
                        'condiciones': condiciones
                    }
                    
                    result = register_sale(client_data, st.session_state.basket)
                    
                    if result == "EXITO":
                        st.balloons()
                        # Generar PDF y guardar en sesión para mostrar fuera del form
                        try:
                            generator = TicketGenerator()
                            pdf_bytes = generator.generate_ticket(client_data, st.session_state.basket)
                            st.session_state.last_ticket = {
                                "data": pdf_bytes,
                                "filename": f"Ticket_{cliente.replace(' ', '_')}.pdf"
                            }
                            # Limpiar carrito
                            st.session_state.basket = []
                            st.success("¡Venta procesada con éxito! Descargue su ticket abajo.")
                        except Exception as e:
                            st.error(f"Error generando PDF: {e}")
                    else:
                        st.error(result)

        # Mostrar botón de descarga FUERA del formulario
        if st.session_state.last_ticket:
            st.divider()
            st.download_button(
                label="📄 Descargar Ticket de Venta",
                data=st.session_state.last_ticket["data"],
                file_name=st.session_state.last_ticket["filename"],
                mime="application/pdf",
                icon="🎫",
                key="btn_download_ticket"
            )
            if st.button("🔄 Nueva Venta"):
                st.session_state.last_ticket = None
                st.rerun()

def generate_internal_code(category):
    import uuid
    prefix_map = {
        'Hulera': 'HUL',
        'Caja Individual': 'CJ',
        'Suela Mov': 'SUE',
        'carga hule': 'CH',
        'Almacén_MateriaPrima': 'AMP',
        'suela sin mov': 'SUE-SM',
        'Etiquetas': 'ETI',
        'Caja_Embarque': 'CJE',
        'Inv_TelaVirgenMov': 'TEL',
        'Inv_TelaVirgen_SinMov': 'TEL-SM',
        'TelaNoUtilizable': 'TEL-NU',
        'Agujeta': 'AGU'
    }
    prefix = prefix_map.get(category, 'MAT')
    return f"{prefix}-{uuid.uuid4().hex[:6].upper()}"
def show_sales_management():
    st.title("📝 Gestión y Consulta de Ventas")
    
    conn = get_db_connection()
    if not conn: return

    # 1. Filtros de Búsqueda
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        fecha_inicio = st.date_input("Fecha Inicio", datetime.now().replace(day=1))
    with col2:
        fecha_fin = st.date_input("Fecha Fin", datetime.now())
    with col3:
        filtro_cliente = st.text_input("Buscar por Cliente", placeholder="Nombre del cliente...")

    # 2. Obtención de Datos
    query_sales = """
        SELECT 
            v.id_venta, 
            v.fecha_venta, 
            v.cliente, 
            v.monto_total, 
            v.forma_pago, 
            v.estado,
            u.nombre_completo as vendedor
        FROM ventas v
        JOIN usuarios u ON v.responsable_id = u.id
        WHERE DATE(v.fecha_venta) BETWEEN %s AND %s
    """
    params = [fecha_inicio, fecha_fin]
    if filtro_cliente:
        query_sales += " AND v.cliente LIKE %s"
        params.append(f"%{filtro_cliente}%")
    
    query_sales += " ORDER BY v.fecha_venta DESC"
    
    # Usar cursor para ejecutar query con parámetros y luego pasar a DataFrame
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query_sales, params)
    data = cursor.fetchall()
    df_sales = pd.DataFrame(data)
    cursor.close()

    if df_sales.empty:
        st.info("No se encontraron ventas en el rango seleccionado.")
        conn.close()
        return

    # Convertir decimales a flotantes para evitar errores de renderizado
    df_sales['monto_total'] = pd.to_numeric(df_sales['monto_total'], errors='coerce')

    # 3. Visualización con AgGrid
    st.subheader("📋 Listado de Ventas")
    
    # Formatear fecha para AgGrid
    df_sales['fecha_venta'] = pd.to_datetime(df_sales['fecha_venta']).dt.strftime('%d/%m/%Y %H:%M')

    gb = GridOptionsBuilder.from_dataframe(df_sales)
    gb.configure_selection('single', use_checkbox=True)
    gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=15)
    gb.configure_column("id_venta", headerName="ID", width=70)
    gb.configure_column("fecha_venta", headerName="Fecha")
    gb.configure_column("monto_total", headerName="Total", type=["numericColumn"], valueFormatter="'$' + x.toLocaleString()")
    
    gridOptions = gb.build()
    
    grid_response = AgGrid(
        df_sales,
        gridOptions=gridOptions,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        fit_columns_on_grid_load=True,
        theme='alpine' if not dark_mode else 'balham',
        height=400,
        width='100%'
    )

    selected_rows = grid_response['selected_rows']
    
    if selected_rows is not None and (isinstance(selected_rows, list) and len(selected_rows) > 0 or isinstance(selected_rows, pd.DataFrame) and not selected_rows.empty):
        # En nuevas versiones de AgGrid, selected_rows puede ser un DataFrame o lista
        if isinstance(selected_rows, pd.DataFrame):
            row = selected_rows.iloc[0]
        else:
            row = selected_rows[0]
            
        id_venta = int(row['id_venta'])
        
        st.divider()
        col_act1, col_act2, col_act3 = st.columns(3)
        
        with col_act1:
            if st.button("🎫 Visualizar / Reimprimir Ticket", use_container_width=True):
                # Obtener detalles de la venta
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT * FROM ventas WHERE id_venta = %s", (id_venta,))
                sale_data = cursor.fetchone()
                
                cursor.execute("""
                    SELECT vd.*, m.descripcion, m.codigo_interno, m.unidad_medida 
                    FROM ventas_detalle vd 
                    JOIN materiales m ON vd.id_material = m.id 
                    WHERE vd.id_venta = %s
                """, (id_venta,))
                items = cursor.fetchall()
                
                # Mapear nombres de llaves para el generador
                sale_mapped = {
                    'cliente': sale_data['cliente'],
                    'telefono': sale_data['telefono_cliente'],
                    'email': sale_data['email_cliente'],
                    'forma_pago': sale_data['forma_pago'],
                    'descuento': sale_data['descuento_global'],
                    'condiciones': sale_data['condiciones']
                }
                
                try:
                    generator = TicketGenerator()
                    pdf_bytes = generator.generate_ticket(sale_mapped, items)
                    st.download_button(
                        label="⬇️ Descargar Ticket PDF",
                        data=pdf_bytes,
                        file_name=f"Reimpresion_Ticket_{id_venta}.pdf",
                        mime="application/pdf",
                        key=f"reprint_{id_venta}"
                    )
                except Exception as e:
                    st.error(f"Error generando ticket: {e}")

        with col_act2:
            if st.session_state.user['rol'] == 'ADMIN':
                if st.button("✏️ Editar Datos de Venta", use_container_width=True):
                    st.session_state.editing_sale = id_venta
                    st.rerun()

        with col_act3:
            if st.session_state.user['rol'] == 'ADMIN':
                if st.button("❌ Cancelar Venta", use_container_width=True):
                    # Lógica simple de cancelación (marcar estado y devolver stock)
                    if row['estado'] == 'CANCELADA':
                        st.warning("Esta venta ya está cancelada.")
                    else:
                        try:
                            cursor = conn.cursor()
                            conn.start_transaction()
                            
                            # 1. Obtener detalles para devolver stock
                            cursor.execute("SELECT id_material, cantidad FROM ventas_detalle WHERE id_venta = %s", (id_venta,))
                            details = cursor.fetchall()
                            for mat_id, qty in details:
                                cursor.execute("UPDATE materiales SET cantidad_actual = cantidad_actual + %s WHERE id = %s", (qty, mat_id))
                            
                            # 2. Cambiar estado
                            cursor.execute("UPDATE ventas SET estado = 'CANCELADA', monto_total = 0 WHERE id_venta = %s", (id_venta,))
                            
                            # 3. Log
                            cursor.execute("INSERT INTO log_actividad (usuario_id, accion, tabla_afectada, registro_id, descripcion) VALUES (%s, %s, %s, %s, %s)",
                                         (st.session_state.user['id'], 'CANCELACION', 'ventas', id_venta, f"Canceló venta {id_venta}"))
                            
                            conn.commit()
                            st.success(f"Venta {id_venta} cancelada y stock devuelto.")
                            st.rerun()
                        except Exception as e:
                            conn.rollback()
                            st.error(f"Error al cancelar: {e}")

    # --- FLUJO DE EDICIÓN ---
    if 'editing_sale' in st.session_state and st.session_state.editing_sale:
        id_edit = st.session_state.editing_sale
        st.divider()
        st.subheader(f"🛠️ Editando Venta #{id_edit}")
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM ventas WHERE id_venta = %s", (id_edit,))
        sale = cursor.fetchone()
        
        with st.form("edit_sale_form"):
            c1, c2 = st.columns(2)
            with c1:
                e_cliente = st.text_input("Cliente", value=sale['cliente'])
                e_tel = st.text_input("Teléfono", value=sale['telefono_cliente'] or "")
            with c2:
                e_forma = st.selectbox("Forma de Pago", ["EFECTIVO", "TRANSFERENCIA", "TARJETA", "DEVOLUCIÓN", "CREDITO"], 
                                      index=["EFECTIVO", "TRANSFERENCIA", "TARJETA", "DEVOLUCIÓN", "CREDITO"].index(sale['forma_pago']) if sale['forma_pago'] in ["EFECTIVO", "TRANSFERENCIA", "TARJETA", "DEVOLUCIÓN", "CREDITO"] else 0)
                e_desc = st.number_input("Descuento %", value=float(sale['descuento_global'] or 0))
            
            e_cond = st.text_area("Condiciones", value=sale['condiciones'] or "")
            
            col_eb1, col_eb2 = st.columns(2)
            if col_eb1.form_submit_button("💾 Guardar Cambios"):
                try:
                    cursor.execute("""
                        UPDATE ventas SET 
                            cliente = %s, telefono_cliente = %s, forma_pago = %s, 
                            descuento_global = %s, condiciones = %s 
                        WHERE id_venta = %s
                    """, (e_cliente, e_tel, e_forma, e_desc, e_cond, id_edit))
                    conn.commit()
                    st.success("Venta actualizada")
                    del st.session_state.editing_sale
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
            
            if col_eb2.form_submit_button("🚫 Cancelar Edición"):
                del st.session_state.editing_sale
                st.rerun()

    conn.close()

def show_inventory_upload():
    st.title("📤 Carga Masiva de Inventario (Excel)")
    st.info("Este módulo permite subir nuevos registros. El **Código Interno** se generará automáticamente si se deja vacío.")
    
    # Botón para descargar plantilla
    template_data = {
        'codigo_interno': [''], # Opcional ahora
        'descripcion': ['Descripción del material'],
        'categoria_hoja': ['Hulera'],
        'propiedad': ['Virgen'],
        'cantidad_actual': [100.0],
        'unidad_medida': ['Pares'],
        'precio_unitario': [50.50],
        'color': ['Negro'],
        'medida': ['25-28'],
        'marca': ['Marca X'],
        'proveedor': ['Proveedor Y'],
        'observaciones': ['Sin observaciones']
    }
    df_template = pd.DataFrame(template_data)
    
    # Usar bytes IO para el Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_template.to_excel(writer, index=False, sheet_name='Plantilla')
    processed_data = output.getvalue()
    
    st.download_button(
        label="📥 Descargar Plantilla Excel",
        data=processed_data,
        file_name="plantilla_carga_inventario.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        icon="📄"
    )
    
    st.divider()
    
    uploaded_file = st.file_uploader("Subir Archivo Excel", type=["xlsx"])
    
    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file)
            st.write("### Previsualización de Datos")
            st.dataframe(df.head(), use_container_width=True)
            
            if st.button("🚀 Procesar y Cargar a Base de Datos"):
                conn = get_db_connection()
                if conn:
                    try:
                        cursor = conn.cursor()
                        # Validar columnas requeridas (codigo_interno ya no es obligatorio)
                        required_cols = ['descripcion', 'categoria_hoja', 'cantidad_actual', 'unidad_medida', 'precio_unitario']
                        missing = [c for c in required_cols if c not in df.columns]
                        
                        if missing:
                            st.error(f"Faltan columnas obligatorias: {', '.join(missing)}")
                            return

                        def clean_nan(val, default=None, is_numeric=False):
                            import math
                            # Caso 1: Es nulo por pandas (NaN, None, <NA>)
                            if pd.isna(val):
                                return 0.0 if is_numeric else default
                            
                            if is_numeric:
                                try:
                                    f_val = float(val)
                                    # Caso 2: Es un valor que float() acepta pero es NaN matemáticamente
                                    if math.isnan(f_val):
                                        return 0.0
                                    return f_val
                                except:
                                    return 0.0
                            
                            # Caso 3: Es texto, asegurar que no sea el string "nan" literal de pandas
                            s_val = str(val).strip()
                            if s_val.lower() == 'nan':
                                return default
                            return s_val

                        count = 0
                        for _, row in df.iterrows():
                            # Generar código si está vacío
                            codigo = clean_nan(row.get('codigo_interno'), "")
                            if not codigo or codigo.lower() == 'nan':
                                codigo = generate_internal_code(clean_nan(row.get('categoria_hoja'), 'Sin Categoria'))

                            query = """
                                INSERT INTO materiales (
                                    codigo_interno, descripcion, categoria_hoja, propiedad,
                                    cantidad_actual, unidad_medida, precio_unitario,
                                    color, medida, marca, proveedor, observaciones, usuario_creacion_id
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """
                            
                            vals = (
                                codigo,
                                clean_nan(row.get('descripcion'), ''),
                                clean_nan(row.get('categoria_hoja'), 'Sin Categoría'),
                                clean_nan(row.get('propiedad')),
                                clean_nan(row.get('cantidad_actual'), 0, True),
                                clean_nan(row.get('unidad_medida'), 'Pza'),
                                clean_nan(row.get('precio_unitario'), 0, True),
                                clean_nan(row.get('color')),
                                clean_nan(row.get('medida')),
                                clean_nan(row.get('marca')),
                                clean_nan(row.get('proveedor')),
                                clean_nan(row.get('observaciones')),
                                st.session_state.user['id']
                            )
                            cursor.execute(query, vals)
                            count += 1
                        
                        conn.commit()
                        st.success(f"✅ Se cargaron {count} registros exitosamente.")
                        
                        # Registrar en log
                        cursor.execute("INSERT INTO log_actividad (usuario_id, accion, tabla_afectada, descripcion) VALUES (%s, %s, %s, %s)",
                                     (st.session_state.user['id'], 'CARGA_MASIVA', 'materiales', f"Carga masiva de {count} registros via Excel"))
                        conn.commit()
                        
                    except Exception as e:
                        st.error(f"Error al procesar el archivo: {e}")
                    finally:
                        conn.close()
        except Exception as e:
            st.error(f"Error al leer el archivo Excel: {e}")

def show_inventory_edit():
    st.title("✏️ Edición de Materiales")
    st.info("Busque un material para editar sus detalles.")
    
    conn = get_db_connection()
    if not conn: return
    
    search_q = st.text_input("Buscar por Código o Descripción", key="edit_search")
    
    if search_q:
        query = """
            SELECT * FROM materiales 
            WHERE (codigo_interno LIKE %s OR descripcion LIKE %s)
            LIMIT 10
        """
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, (f"%{search_q}%", f"%{search_q}%"))
        results = cursor.fetchall()
        
        if results:
            opts = {f"[{r['codigo_interno']}] {r['descripcion']}": r for r in results}
            selected_label = st.selectbox("Seleccione el material a editar", opts.keys())
            item = opts[selected_label]
            
            st.divider()
            with st.form("edit_material_form"):
                col_info, col_values = st.columns(2)
                with col_info:
                    st.write(f"**Código Actual:** `{item['codigo_interno']}`")
                    new_codigo = st.text_input("Cambiar Código (Opcional)", value=item['codigo_interno'])
                    new_desc = st.text_area("Descripción", value=item['descripcion'])
                    
                    # --- CATEGORÍA DINÁMICA ---
                    cursor.execute("SELECT DISTINCT categoria_hoja FROM materiales WHERE categoria_hoja IS NOT NULL AND categoria_hoja != ''")
                    existing_cats = [r['categoria_hoja'] for r in cursor.fetchall()]
                    if item['categoria_hoja'] not in existing_cats:
                        existing_cats.append(item['categoria_hoja'])
                    
                    cat_options = sorted(existing_cats) + ["➕ Agregar nueva categoría..."]
                    selected_cat = st.selectbox("Categoría", options=cat_options, index=cat_options.index(item['categoria_hoja']) if item['categoria_hoja'] in cat_options else 0)
                    
                    if selected_cat == "➕ Agregar nueva categoría...":
                        new_cat = st.text_input("Escriba la nueva categoría")
                    else:
                        new_cat = selected_cat

                    new_prop = st.text_input("Propiedad", value=item['propiedad'] or "")
                
                with col_values:
                    new_cant = st.number_input("Cantidad Actual", value=float(item['cantidad_actual']), format="%.3f")
                    
                    # --- UNIDAD DE MEDIDA DINÁMICA ---
                    cursor.execute("SELECT DISTINCT unidad_medida FROM materiales WHERE unidad_medida IS NOT NULL AND unidad_medida != ''")
                    existing_units = [r['unidad_medida'] for r in cursor.fetchall()]
                    if item['unidad_medida'] not in existing_units:
                        existing_units.append(item['unidad_medida'])
                    
                    unit_options = sorted(existing_units) + ["➕ Agregar nueva unidad..."]
                    selected_unit = st.selectbox("Unidad de Medida", options=unit_options, index=unit_options.index(item['unidad_medida']) if item['unidad_medida'] in unit_options else 0)
                    
                    if selected_unit == "➕ Agregar nueva unidad...":
                        new_unidad = st.text_input("Escriba la nueva unidad")
                    else:
                        new_unidad = selected_unit

                    new_precio = st.number_input("Precio Unitario ($)", value=float(item['precio_unitario']), format="%.2f")
                    new_color = st.text_input("Color", value=item['color'] or "")
                
                col_extra1, col_extra2 = st.columns(2)
                with col_extra1:
                    new_medida = st.text_input("Medida", value=item['medida'] or "")
                    new_marca = st.text_input("Marca", value=item['marca'] or "")
                with col_extra2:
                    new_prov = st.text_input("Proveedor", value=item['proveedor'] or "")
                    new_obs = st.text_area("Observaciones", value=item['observaciones'] or "")
                
                if st.form_submit_button("💾 Guardar Cambios"):
                    try:
                        update_query = """
                            UPDATE materiales SET 
                                codigo_interno = %s, descripcion = %s, categoria_hoja = %s, propiedad = %s,
                                cantidad_actual = %s, unidad_medida = %s, precio_unitario = %s,
                                color = %s, medida = %s, marca = %s, proveedor = %s, observaciones = %s
                            WHERE id = %s
                        """
                        cursor.execute(update_query, (
                            new_codigo, new_desc, new_cat, new_prop if new_prop else None,
                            new_cant, new_unidad, new_precio,
                            new_color if new_color else None, new_medida if new_medida else None,
                            new_marca if new_marca else None, new_prov if new_prov else None,
                            new_obs if new_obs else None, item['id']
                        ))
                        conn.commit()
                        
                        # Log
                        cursor.execute("INSERT INTO log_actividad (usuario_id, accion, tabla_afectada, registro_id, descripcion) VALUES (%s, %s, %s, %s, %s)",
                                     (st.session_state.user['id'], 'MODIFICACION', 'materiales', item['id'], f"Editó material {new_codigo}"))
                        conn.commit()
                        
                        st.success("✅ Cambios guardados exitosamente")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al actualizar: {e}")
        else:
            st.warning("No se encontraron materiales con ese criterio.")
    conn.close()

def show_inventory_bulk_edit():
    st.title("📋 Edición Masiva de Inventario")
    st.markdown("""
    Esta herramienta permite editar múltiples materiales al mismo tiempo usando una tabla interactiva.
    > [!TIP]
    > Puedes copiar y pegar desde Excel directamente en esta tabla. No olvides hacer clic en **Guardar Cambios** al finalizar.
    """)
    
    conn = get_db_connection()
    if not conn: return
    
    # Filtros para no cargar todo el inventario de golpe si es muy grande
    col1, col2 = st.columns(2)
    with col1:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT categoria_hoja FROM materiales WHERE categoria_hoja IS NOT NULL")
        cats = [r[0] for r in cursor.fetchall()]
        cat_filter = st.selectbox("Filtrar por Categoría", ["Todas"] + sorted(cats))
    with col2:
        search_filter = st.text_input("Buscar por descripción/código", placeholder="Escribe para buscar...")

    query = "SELECT * FROM materiales WHERE 1=1"
    params = []
    
    if cat_filter != "Todas":
        query += " AND categoria_hoja = %s"
        params.append(cat_filter)
    if search_filter:
        query += " AND (descripcion LIKE %s OR codigo_interno LIKE %s)"
        params.extend([f"%{search_filter}%", f"%{search_filter}%"])
    
    query += " ORDER BY id DESC LIMIT 500" # Limitar para rendimiento
    
    df_origin = pd.read_sql(query, conn, params=params)
    
    if not df_origin.empty:
        # Configurar el editor de datos
        edited_df = st.data_editor(
            df_origin,
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            disabled=["id", "fecha_creacion", "fecha_modificacion"],
            column_config={
                "id": None, # Ocultar ID
                "codigo_interno": st.column_config.TextColumn("Código", width="small", required=True),
                "descripcion": st.column_config.TextColumn("Descripción", width="large", required=True),
                "precio_unitario": st.column_config.NumberColumn("Precio ($)", format="$%.2f", min_value=0),
                "cantidad_actual": st.column_config.NumberColumn("Stock", format="%.3f"),
                "categoria_hoja": "Categoría",
                "unidad_medida": "Unidad",
                "fecha_creacion": None,
                "fecha_modificacion": None
            },
            key="bulk_editor"
        )
        
        # Verificar cambios
        if st.button("💾 Guardar Todos los Cambios"):
            changes = st.session_state.bulk_editor
            
            # Solo proceder si hay cambios detectados por Streamlit
            if changes['edited_rows'] or changes['added_rows'] or changes['deleted_rows']:
                cursor = conn.cursor()
                try:
                    if not conn.in_transaction:
                        conn.start_transaction()
                    
                    # 1. Procesar Ediciones
                    for idx, row_changes in changes['edited_rows'].items():
                        # Asegurar que el ID sea un tipo nativo de Python
                        val_id = df_origin.iloc[int(idx)]['id']
                        real_id = val_id.item() if hasattr(val_id, 'item') else val_id
                        
                        # Construir query dinámica para los campos cambiados
                        set_clause = ", ".join([f"{k} = %s" for k in row_changes.keys()])
                        # Convertir valores de numpy a nativos (si aplica)
                        vals = [v.item() if hasattr(v, 'item') else v for v in row_changes.values()] + [real_id]
                        cursor.execute(f"UPDATE materiales SET {set_clause} WHERE id = %s", vals)
                    
                    # 2. Procesar Adiciones
                    for row in changes['added_rows']:
                        cols = ", ".join(row.keys())
                        placeholders = ", ".join(["%s"] * len(row))
                        # Convertir valores a nativos
                        vals = [v.item() if hasattr(v, 'item') else v for v in row.values()]
                        cursor.execute(f"INSERT INTO materiales ({cols}) VALUES ({placeholders})", vals)
                    
                    # 3. Procesar Eliminaciones
                    for idx in changes['deleted_rows']:
                        val_id = df_origin.iloc[int(idx)]['id']
                        real_id = val_id.item() if hasattr(val_id, 'item') else val_id
                        cursor.execute("DELETE FROM materiales WHERE id = %s", (real_id,))
                    
                    conn.commit()
                    st.success(f"✅ Se han procesado los cambios correctamente.")
                    st.rerun()
                except Exception as e:
                    conn.rollback()
                    st.error(f"❌ Error al guardar cambios masivos: {e}")
            else:
                st.info("No se detectaron cambios pendientes en la tabla.")
    else:
        st.warning("No se encontraron materiales con los filtros aplicados.")
    
    conn.close()

# Punto de entrada
if __name__ == "__main__":
    check_auto_login()
    
    if not st.session_state.authenticated:
        login_page()
    else:
        main_dashboard()
