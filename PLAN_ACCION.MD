# Plan de Acción: Aplicación de Liquidación de Materia Prima (Streamlit + MySQL)

## 1. Resumen del Proyecto

Desarrollar una aplicación multiusuario para el control, promoción y venta de inventarios de materia prima de una empresa en liquidación. La aplicación debe permitir que múltiples promotores consulten existencias en tiempo real, registren ventas detalladas y generen catálogos para clientes, asegurando la integridad de los datos mediante bloqueos de concurrencia.

### Stack Tecnológico

- **IDE**: Antigravity (Agent-First IDE)
- **Lenguaje**: Python 3.12+
- **Interfaz**: Streamlit
- **Base de Datos**: MySQL 8.0+
- **Modelos de IA**: Gemini 3 (vía Antigravity)

---

## 2. Fase 1: Cimentación del Entorno

**Objetivo**: Configurar el espacio donde operarán los agentes.

- [ ] **Estructura de Directorios**: Crear carpetas `.agent/skills/`, `src/`, `data/` y `.streamlit/`
- [ ] **Dependencias**: Crear `requirements.txt` con:
  - `streamlit`
  - `pandas`
  - `openpyxl`
  - `sqlalchemy`
  - `mysql-connector-python`
  - `fpdf2`
  - `cryptography`
- [ ] **Configuración de Secretos**: Configurar `.streamlit/secrets.toml` con las credenciales de la base de datos MySQL

---

## 3. Fase 2: Arquitectura de la Base de Datos

**Objetivo**: Implementar un esquema normalizado que unifique las diversas hojas de Excel.

### Tabla Maestra: `materiales`

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id` | INT AI | PK |
| `codigo_interno` | VARCHAR | Código único de identificación del material |
| `descripcion` | TEXT | Nombre o descripción detallada |
| `categoria_hoja` | VARCHAR | Hoja de origen (ej. Hulera, Inv_TelaVirgenMov) |
| `propiedad` | VARCHAR | Clasificación (Virgen, No Utilizable, etc.) |
| `cantidad_actual` | DECIMAL | Stock real disponible |
| `unidad_medida` | VARCHAR | Kg, Metros, Pares, etc. |
| `precio_unitario` | DECIMAL | Costo o precio de liquidación |
| `color`, `medida`, `marca`, `proveedor` | VARCHAR | Atributos específicos (permitir NULL) |
| `observaciones` | TEXT | Comentarios adicionales del Excel |

### Tabla de Ventas: `ventas`

Campos: `id_venta`, `id_material`, `cantidad`, `precio_final`, `cliente`, `condiciones`, `responsable_id`, `fecha_venta`

---

## 4. Fase 3: Migración de Datos con IA (Skill Especializada)

### Instrucción para el Agente:

> "Actúa como Ingeniero de Datos. Lee el archivo `Inv_Dic_2025.xlsx`. Crea un script en `src/migration.py` que recorra todas las hojas relevantes, normalice los nombres de las columnas según la tabla `materiales` definida arriba, maneje valores nulos y cargue todo en MySQL. Asegúrate de que las unidades de medida (kg, KG, Kgs) se estandaricen a un solo formato."

---

## 5. Fase 4: Desarrollo de Módulos en Streamlit

Dividir el desarrollo en componentes funcionales:

### Módulo A: Autenticación y RBAC

- Implementar login basado en la tabla `usuarios`
- Definir roles: 
  - **ADMIN** (gestión total)
  - **VENDEDOR** (consulta y registro)

### Módulo B: Dashboard de Consulta (Promoción)

- Tabla interactiva con filtros dinámicos (Categoría, Color, Medida)
- Botón para exportar los resultados filtrados a un Catálogo PDF usando `fpdf2`

### Módulo C: Registro de Ventas (Concurrencia Crítica)

**Lógica de Bloqueo**: Implementar transacciones seguras.

#### Instrucción para el Agente:

> "Escribe una función de venta que utilice `SELECT... FOR UPDATE` en MySQL para bloquear la fila del material. Esto evitará que dos vendedores descuenten stock del mismo ítem simultáneamente."

---

## 6. Fase 5: Reportes y Auditoría

- [ ] **Seguimiento de Liquidación**: Visualización del % de avance de venta (Monto recuperado vs. Valor inicial)
- [ ] **Log de Actividad**: Registro automático de quién vendió qué material y en qué fecha

---

## 7. Fase 6: Despliegue

- Configurar el acceso remoto a MySQL (Túnel SSH o SSL)
- Desplegar la app en Streamlit Community Cloud o un VPS (Kamatera/Hostinger)