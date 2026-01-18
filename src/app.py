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
        config = st.secrets["mysql"]
        conn = mysql.connector.connect(
            host=config["host"],
            port=config["port"],
            user=config["user"],
            password=config["password"],
            database=config["database"]
        )
        return conn
    except Error as e:
        st.error(f"Error de conexión a la base de datos: {e}")
        return None

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
            submit = st.form_submit_button("Iniciar Sesión")
            
            if submit:
                # Caso especial para desarrollo inicial o validación real
                # Si es admin/admin123 o vendedor1/vendedor123 (los del setup)
                # En un paso posterior integraremos validación real de bcrypt
                user = check_login(username, password)
                if user:
                    st.session_state.authenticated = True
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos")

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
        
        menu = ["📊 Dashboard", "🔍 Consulta de Inventario", "💰 Registrar Venta"]
        if st.session_state.user['rol'] == 'ADMIN':
            menu.append("👥 Gestión de Usuarios")
            menu.append("📈 Reportes")
        
        menu.append("❓ Ayuda / Tutorial")
            
        choice = st.radio("Navegación", menu)
        
        if st.button("Cerrar Sesión"):
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
    elif choice == "👥 Gestión de Usuarios":
        show_user_management()
    elif choice == "📈 Reportes":
        show_reports()
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
    query_stats = "SELECT * FROM v_progreso_liquidacion"
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

    # 3. Stock Crítico
    st.subheader("⚠️ Alerta de Stock Crítico")
    st.write("Materiales con menos de 10 unidades disponibles.")
    query_critico = """
        SELECT codigo_interno, descripcion, categoria_hoja, cantidad_actual, unidad_medida 
        FROM materiales 
        WHERE cantidad_actual < 10 AND cantidad_actual > 0
        ORDER BY cantidad_actual ASC
    """
    df_crit = pd.read_sql(query_critico, conn)
    if not df_crit.empty:
        st.dataframe(df_crit, use_container_width=True, hide_index=True)
    else:
        st.success("No hay materiales con stock crítico actualmente.")

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
            u_rol = st.selectbox("Rol", ["VENDEDOR", "ADMIN"])
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
        query = "SELECT * FROM v_progreso_liquidacion"
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

def show_inventory():
    st.title("📦 Consulta de Inventario")
    
    conn = get_db_connection()
    if conn:
        # Filtros
        query_cats = "SELECT DISTINCT categoria_hoja FROM materiales"
        cats_df = pd.read_sql(query_cats, conn)
        
        col1, col2 = st.columns([1, 2])
        with col1:
            categoria = st.selectbox("Categoría", ["Todas"] + list(cats_df['categoria_hoja']))
        with col2:
            search = st.text_input("Buscar por código o descripción")
        
        # Construir query dinámica
        query = """
            SELECT 
                id, 
                codigo_interno, 
                descripcion, 
                categoria_hoja, 
                cantidad_actual, 
                unidad_medida, 
                precio_unitario,
                (cantidad_actual * precio_unitario) as importe
            FROM materiales 
            WHERE 1=1
        """
        params = []
        
        if categoria != "Todas":
            query += " AND categoria_hoja = %s"
            params.append(categoria)
        
        if search:
            query += " AND (codigo_interno LIKE %s OR descripcion LIKE %s)"
            params.append(f"%{search}%")
            params.append(f"%{search}%")
            
        # Ejecutar usando motor de pandas para visualización
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params)
        data = cursor.fetchall()
        df = pd.DataFrame(data)
        conn.close()
        
        if not df.empty:
            # Formatear columnas para mejor visualización
            st.dataframe(
                df, 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "cantidad_actual": st.column_config.NumberColumn("Cantidad", format=",.3f"),
                    "precio_unitario": st.column_config.NumberColumn("Precio U.", format="$,.2f"),
                    "importe": st.column_config.NumberColumn("Importe Total", format="$,.2f"),
                    "codigo_interno": "Código",
                    "descripcion": "Descripción",
                    "categoria_hoja": "Categoría",
                    "unidad_medida": "Unidad"
                }
            )
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
                forma_pago = st.selectbox("Forma de Pago", ["EFECTIVO", "TRANSFERENCIA", "TARJETA", "OTRO"])
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

# Punto de entrada
if __name__ == "__main__":
    if not st.session_state.authenticated:
        login_page()
    else:
        main_dashboard()
