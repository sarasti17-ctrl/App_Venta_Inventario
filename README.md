# Aplicación de Liquidación de Materia Prima

Sistema multiusuario para control, promoción y venta de inventarios de materia prima.

## Estructura del Proyecto

```
App_Venta_Inventario/
├── .agent/
│   └── skills/          # Skills especializadas para agentes IA
├── .streamlit/
│   └── secrets.toml     # Configuración de credenciales (NO subir a Git)
├── src/                 # Código fuente de la aplicación
├── data/                # Archivos de datos (Excel, backups)
├── venv/                # Entorno virtual de Python
├── requirements.txt     # Dependencias del proyecto
└── PLAN_ACCION.MD      # Plan de desarrollo
```

## Instalación

1. Crear entorno virtual:
```bash
python -m venv venv
```

2. Activar entorno virtual:
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Configurar credenciales en `.streamlit/secrets.toml`

## Uso

```bash
streamlit run src/app.py
```

## Stack Tecnológico

- **Python**: 3.12+
- **Framework**: Streamlit
- **Base de Datos**: MySQL 8.0+
- **PDF**: fpdf2
- **IDE**: Antigravity (Agent-First IDE)

## Características

- ✅ Autenticación multiusuario (ADMIN/VENDEDOR)
- ✅ Consulta de inventario en tiempo real
- ✅ Registro de ventas con control de concurrencia
- ✅ Generación de catálogos PDF
- ✅ Reportes y auditoría
