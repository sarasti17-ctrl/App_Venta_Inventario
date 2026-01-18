-- ============================================================================
-- Script de Configuración Sarasti - Clever Cloud
-- ============================================================================

-- NOTA: No creamos la base de datos porque Clever Cloud ya la creó con nombre: bj6praqdpuirvzoqna22

-- Limpiar tablas si existen
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS log_actividad;
DROP TABLE IF EXISTS ventas_detalle;
DROP TABLE IF EXISTS ventas;
DROP TABLE IF EXISTS materiales;
DROP TABLE IF EXISTS usuarios;
SET FOREIGN_KEY_CHECKS = 1;

-- TABLA: usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    nombre_completo VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    rol ENUM('ADMIN', 'VENDEDOR') NOT NULL DEFAULT 'VENDEDOR',
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_rol (rol)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- TABLA: materiales
CREATE TABLE IF NOT EXISTS materiales (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo_interno VARCHAR(100) NOT NULL,
    descripcion TEXT NOT NULL,
    categoria_hoja VARCHAR(100) NOT NULL,
    propiedad VARCHAR(50),
    cantidad_actual DECIMAL(15, 3) NOT NULL DEFAULT 0,
    unidad_medida VARCHAR(20) NOT NULL,
    precio_unitario DECIMAL(15, 2) NOT NULL DEFAULT 0,
    color VARCHAR(50),
    medida VARCHAR(50),
    marca VARCHAR(100),
    proveedor VARCHAR(100),
    observaciones TEXT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    usuario_creacion_id INT,
    INDEX idx_codigo (codigo_interno),
    INDEX idx_categoria (categoria_hoja),
    FOREIGN KEY (usuario_creacion_id) REFERENCES usuarios(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- TABLA: ventas
CREATE TABLE IF NOT EXISTS ventas (
    id_venta INT AUTO_INCREMENT PRIMARY KEY,
    cliente VARCHAR(200) NOT NULL,
    telefono_cliente VARCHAR(20),
    email_cliente VARCHAR(100),
    condiciones TEXT,
    forma_pago VARCHAR(50),
    responsable_id INT NOT NULL,
    monto_total DECIMAL(15, 2) NOT NULL DEFAULT 0,
    descuento_global DECIMAL(5, 2) DEFAULT 0,
    fecha_venta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estado ENUM('PENDIENTE', 'COMPLETADA', 'CANCELADA') DEFAULT 'COMPLETADA',
    FOREIGN KEY (responsable_id) REFERENCES usuarios(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- TABLA: ventas_detalle
CREATE TABLE IF NOT EXISTS ventas_detalle (
    id_detalle INT AUTO_INCREMENT PRIMARY KEY,
    id_venta INT NOT NULL,
    id_material INT NOT NULL,
    cantidad DECIMAL(15, 3) NOT NULL,
    precio_unitario DECIMAL(15, 2) NOT NULL,
    subtotal DECIMAL(15, 2) NOT NULL,
    FOREIGN KEY (id_venta) REFERENCES ventas(id_venta) ON DELETE CASCADE,
    FOREIGN KEY (id_material) REFERENCES materiales(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- TABLA: log_actividad
CREATE TABLE IF NOT EXISTS log_actividad (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT,
    accion VARCHAR(100) NOT NULL,
    tabla_afectada VARCHAR(50),
    registro_id INT,
    descripcion TEXT,
    fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- USUARIOS INICIALES (admin / admin123, vendedor1 / vendedor123)
INSERT INTO usuarios (username, password_hash, nombre_completo, rol) 
VALUES 
('admin', SHA2('admin123', 256), 'Administrador Cloud', 'ADMIN'),
('vendedor1', SHA2('vendedor123', 256), 'Vendedor Cloud', 'VENDEDOR');

-- VISTAS
CREATE OR REPLACE VIEW v_progreso_liquidacion AS
SELECT 
    COUNT(*) AS total_items,
    SUM(cantidad_actual) AS cantidad_total,
    SUM(cantidad_actual * precio_unitario) AS valor_inventario_actual,
    (SELECT COALESCE(SUM(monto_total), 0) FROM ventas WHERE estado = 'COMPLETADA') AS monto_recuperado,
    (SELECT COUNT(*) FROM ventas WHERE estado = 'COMPLETADA') AS ventas_completadas
FROM materiales;
