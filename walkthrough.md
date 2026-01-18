# Walkthrough: Sistema de Gestión de Liquidación v1.0

Este documento resume los avances logrados en la configuración de la base de datos y la interfaz inicial de Streamlit.

## 🚀 Estado Actual
- **Base de Datos**: Configurada en MariaDB con 5 tablas, 3 vistas y 1 procedimiento almacenado.
- **Datos**: 623 materiales migrados desde Excel, soportando códigos duplicados para variantes de color/estilo y abarcando todas las hojas del archivo.
- **Dashboard**: Métricas en tiempo real con diseño **Premium** y soporte para **Modo Oscuro** 🌙.
- **Formato Local**: Cantidades y precios adaptados al estándar de México (punto para decimales, coma para miles).
- **Ventas**: Módulo multi-artículo con carrito y descarga de tickets PDF segura.

## 🔐 Acceso al Sistema
La aplicación se está ejecutando en: [http://localhost:8502](http://localhost:8502)

| Rol | Usuario | Contraseña |
| :--- | :--- | :--- |
| **Administrador** | `admin` | `admin123` |
| **Vendedor** | `vendedor1` | `vendedor123` |

## 🛠️ Funcionalidades Implementadas

### 1. Consulta Inteligente de Inventario
Permite filtrar por las 11 categorías migradas y realizar búsquedas de texto con cálculo de **Importe Total** (Cantidad x Precio) e indicadores de miles.

### 2. Registro de Ventas con Carrito (Módulo C - Mejorado)
He reestructurado profundamente el sistema para permitir ventas complejas:
- **Carrito de Compras**: Ahora puedes buscar y añadir múltiples productos a una sola venta.
- **Gestión de Selección**: Puedes ver el resumen de los productos añadidos, quitar ítems o vaciar el carrito antes de confirmar.
- **Transacciones Atómicas**: El sistema asegura que, al confirmar, se descuente el stock de todos los productos o que no se descuente nada si hay algún error (todo o nada).
- **Nueva Estructura de BD**: Se crearon tablas de `ventas` (cabecera) y `ventas_detalle` para un manejo profesional de la información.

### 3. Gestión de Usuarios y Seguridad (Módulo E)
El sistema ahora es más robusto y administrable:
- **Seguridad SHA2-256**: Todas las contraseñas se encriptan directamente en la base de datos usando estándares bancarios.
- **Panel de Administración**: Desde la pestaña **👥 Gestión de Usuarios**, un administrador puede:
    - Ver quién tiene acceso al sistema.
    - Dar de alta a nuevos empleados.
    - Resetear contraseñas olvidadas de forma instantánea.
    - Desactivar cuentas con un solo switch sin borrar su historial de ventas.

### 4. Reportes Avanzados e Inteligencia de Datos (Módulo F)
El administrador ahora tiene acceso a una pestaña de **📈 Reportes** que incluye:
- **KPIs en Tiempo Real**: Total de ítems, ventas realizadas y monto recuperado acumulado.
- **Gráficas Interactivas (Plotly)**: 
    - Desglose de ventas por categoría (proporción del total).
    - Tendencia histórica de ventas para ver el progreso día a día.
- **Monitor de Stock Crítico**: Alerta visual automática de materiales con menos de 10 unidades para evitar quiebres de inventario.

### 5. Generación de Tickets (PDF)
Tras registrar una venta exitosa:
- **Descarga Inmediata**: Aparecerá un botón azul para bajar el ticket.
- **Formato Profesional**: Incluye logotipo (texto), desglose de precios, descuentos aplicados y observaciones.
- **Nombre Automático**: Los archivos se nombran según el cliente y la fecha para fácil organización.

## 📸 Pruebas de Funcionamiento Recomendadas
1.  Ir a **💰 Registrar Venta**.
2.  Buscar `511` y seleccionar una de las variantes de tela.
3.  Ingresar datos de un cliente ficticio y un descuento del 10%.
4.  Registrar la venta.
5.  **Descargar el Ticket** y verificar que los cálculos y datos sean correctos.

---
**Sistema Finalizado**: Todos los módulos base están operativos y listos para producción.
