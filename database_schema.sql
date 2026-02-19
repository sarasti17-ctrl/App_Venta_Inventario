-- ============================================================================
-- Script de Creación de Base de Datos: Liquidación de Inventario
-- ============================================================================
-- Descripción: Crea la base de datos y las tablas necesarias para el sistema
--              de liquidación de materia prima
-- Autor: Sistema de Liquidación
-- Fecha: 2026-01-16
-- ============================================================================

-- Crear la base de datos si no existe
CREATE DATABASE IF NOT EXISTS liquidacion_inventario
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

-- Usar la base de datos
USE liquidacion_inventario;

-- Limpiar tablas si existen (para aplicar cambios de esquema)
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS log_actividad;
DROP TABLE IF EXISTS ventas;
DROP TABLE IF EXISTS materiales;
DROP TABLE IF EXISTS usuarios;
SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================================
-- TABLA: usuarios
-- Descripción: Almacena los usuarios del sistema con sus roles
-- ============================================================================
CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    nombre_completo VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    rol ENUM('ADMIN', 'VENDEDOR', 'CLIENTE') NOT NULL DEFAULT 'VENDEDOR',
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_rol (rol)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- TABLA: materiales
-- Descripción: Tabla maestra que unifica todas las hojas de Excel
-- ============================================================================
CREATE TABLE IF NOT EXISTS materiales (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo_interno VARCHAR(100) NOT NULL,
    descripcion TEXT NOT NULL,
    categoria_hoja VARCHAR(100) NOT NULL COMMENT 'Hoja de origen: Hulera, Inv_TelaVirgenMov, etc.',
    propiedad VARCHAR(50) COMMENT 'Virgen, No Utilizable, etc.',
    cantidad_actual DECIMAL(15, 3) NOT NULL DEFAULT 0 COMMENT 'Stock real disponible',
    unidad_medida VARCHAR(20) NOT NULL COMMENT 'Kg, Metros, Pares, etc.',
    precio_unitario DECIMAL(15, 2) NOT NULL DEFAULT 0 COMMENT 'Precio de liquidación',
    
    -- Atributos específicos (pueden ser NULL)
    color VARCHAR(50),
    medida VARCHAR(50),
    marca VARCHAR(100),
    proveedor VARCHAR(100),
    
    -- Información adicional
    observaciones TEXT,
    
    -- Campos de auditoría
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    usuario_creacion_id INT,
    
    -- Índices para mejorar rendimiento
    INDEX idx_codigo (codigo_interno),
    INDEX idx_categoria (categoria_hoja),
    INDEX idx_propiedad (propiedad),
    INDEX idx_color (color),
    INDEX idx_marca (marca),
    
    -- Relación con usuarios
    FOREIGN KEY (usuario_creacion_id) REFERENCES usuarios(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- TABLA: ventas (Cabecera)
CREATE TABLE IF NOT EXISTS ventas (
    id_venta INT AUTO_INCREMENT PRIMARY KEY,
    cliente VARCHAR(200) NOT NULL,
    telefono_cliente VARCHAR(20),
    email_cliente VARCHAR(100),
    condiciones TEXT,
    forma_pago ENUM('EFECTIVO', 'TRANSFERENCIA', 'CHEQUE', 'CREDITO', 'TARJETA', 'OTRO') DEFAULT 'EFECTIVO',
    responsable_id INT NOT NULL,
    monto_total DECIMAL(15, 2) NOT NULL DEFAULT 0,
    descuento_global DECIMAL(5, 2) DEFAULT 0,
    fecha_venta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estado ENUM('PENDIENTE', 'COMPLETADA', 'CANCELADA') DEFAULT 'COMPLETADA',
    
    INDEX idx_responsable (responsable_id),
    INDEX idx_fecha_venta (fecha_venta),
    INDEX idx_cliente (cliente),
    INDEX idx_estado (estado),
    FOREIGN KEY (responsable_id) REFERENCES usuarios(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- TABLA: ventas_detalle (Detalle de productos por venta)
CREATE TABLE IF NOT EXISTS ventas_detalle (
    id_detalle INT AUTO_INCREMENT PRIMARY KEY,
    id_venta INT NOT NULL,
    id_material INT NOT NULL,
    cantidad DECIMAL(15, 3) NOT NULL,
    precio_unitario DECIMAL(15, 2) NOT NULL,
    subtotal DECIMAL(15, 2) NOT NULL,
    
    INDEX idx_venta (id_venta),
    INDEX idx_material (id_material),
    FOREIGN KEY (id_venta) REFERENCES ventas(id_venta) ON DELETE CASCADE,
    FOREIGN KEY (id_material) REFERENCES materiales(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- TABLA: log_actividad
-- Descripción: Auditoría de todas las acciones en el sistema
-- ============================================================================
CREATE TABLE IF NOT EXISTS log_actividad (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT,
    accion VARCHAR(100) NOT NULL COMMENT 'LOGIN, VENTA, CONSULTA, MODIFICACION, etc.',
    tabla_afectada VARCHAR(50),
    registro_id INT,
    descripcion TEXT,
    ip_address VARCHAR(45),
    fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_usuario (usuario_id),
    INDEX idx_accion (accion),
    INDEX idx_fecha (fecha_hora),
    
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- INSERTAR DATOS INICIALES
-- ============================================================================

-- Usuario administrador por defecto (password: admin123)
-- NOTA: Cambiar la contraseña después del primer login
INSERT INTO usuarios (username, password_hash, nombre_completo, email, rol) 
VALUES (
    'admin',
    SHA2('admin123', 256),
    'Administrador del Sistema',
    'admin@liquidacion.com',
    'ADMIN'
) ON DUPLICATE KEY UPDATE username=username;

-- Usuario vendedor de ejemplo (password: vendedor123)
INSERT INTO usuarios (username, password_hash, nombre_completo, email, rol) 
VALUES (
    'vendedor1',
    SHA2('vendedor123', 256),
    'Vendedor Ejemplo',
    'vendedor@liquidacion.com',
    'VENDEDOR'
) ON DUPLICATE KEY UPDATE username=username;

-- ============================================================================
-- VISTAS ÚTILES
-- ============================================================================

DROP VIEW IF EXISTS v_inventario_disponible;
DROP VIEW IF EXISTS v_ventas_por_vendedor;
DROP VIEW IF EXISTS v_progreso_liquidacion;

-- Vista: Inventario disponible con valor total
CREATE OR REPLACE VIEW v_inventario_disponible AS
SELECT 
    m.id,
    m.codigo_interno,
    m.descripcion,
    m.categoria_hoja,
    m.cantidad_actual,
    m.unidad_medida,
    m.precio_unitario,
    (m.cantidad_actual * m.precio_unitario) AS valor_total,
    m.color,
    m.medida,
    m.marca,
    m.propiedad
FROM materiales m
WHERE m.cantidad_actual > 0
ORDER BY m.categoria_hoja, m.descripcion;

-- Vista: Resumen de ventas por vendedor
CREATE OR REPLACE VIEW v_ventas_por_vendedor AS
SELECT 
    u.id AS vendedor_id,
    u.nombre_completo AS vendedor,
    COUNT(v.id_venta) AS total_ventas,
    SUM(v.monto_total) AS monto_total,
    AVG(v.monto_total) AS promedio_venta,
    MAX(v.fecha_venta) AS ultima_venta
FROM usuarios u
LEFT JOIN ventas v ON u.id = v.responsable_id
WHERE u.rol = 'VENDEDOR'
GROUP BY u.id, u.nombre_completo;

-- Vista: Progreso de liquidación
CREATE OR REPLACE VIEW v_progreso_liquidacion AS
SELECT 
    COUNT(*) AS total_items,
    SUM(cantidad_actual) AS cantidad_total,
    SUM(cantidad_actual * precio_unitario) AS valor_inventario_actual,
    (SELECT SUM(monto_total) FROM ventas WHERE estado = 'COMPLETADA') AS monto_recuperado,
    (SELECT COUNT(*) FROM ventas WHERE estado = 'COMPLETADA') AS ventas_completadas
FROM materiales
WHERE cantidad_actual > 0;

-- ============================================================================
-- SP removido temporalmente para rediseño multi-artículo
-- Se manejará vía transacción en Python para mayor flexibilidad
SELECT 'Procedimientos: En rediseño' AS sp_status;

-- ============================================================================
-- SCRIPT COMPLETADO
-- ============================================================================

SELECT 'Base de datos creada exitosamente!' AS mensaje;
SELECT 'Tablas: usuarios, materiales, ventas, ventas_detalle, log_actividad' AS tablas_creadas;
SELECT 'Vistas: v_inventario_disponible, v_ventas_por_vendedor, v_progreso_liquidacion' AS vistas_creadas;
