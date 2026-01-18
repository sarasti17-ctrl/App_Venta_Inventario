-- Procedimiento almacenado para registrar ventas con control de concurrencia
-- Este archivo se ejecuta por separado debido a diferencias en el manejo de delimitadores

DROP PROCEDURE IF EXISTS sp_registrar_venta;

CREATE PROCEDURE sp_registrar_venta(
    IN p_id_material INT,
    IN p_cantidad DECIMAL(15,3),
    IN p_precio_unitario DECIMAL(15,2),
    IN p_descuento DECIMAL(5,2),
    IN p_cliente VARCHAR(200),
    IN p_telefono VARCHAR(20),
    IN p_email VARCHAR(100),
    IN p_condiciones TEXT,
    IN p_forma_pago VARCHAR(20),
    IN p_responsable_id INT,
    OUT p_resultado VARCHAR(100)
)
BEGIN
    DECLARE v_cantidad_actual DECIMAL(15,3);
    DECLARE v_precio_final DECIMAL(15,2);
    
    -- Iniciar transacción
    START TRANSACTION;
    
    -- Bloquear la fila del material (SELECT FOR UPDATE)
    SELECT cantidad_actual INTO v_cantidad_actual
    FROM materiales
    WHERE id = p_id_material
    FOR UPDATE;
    
    -- Verificar si hay suficiente stock
    IF v_cantidad_actual >= p_cantidad THEN
        -- Calcular precio final
        SET v_precio_final = (p_cantidad * p_precio_unitario) * (1 - p_descuento/100);
        
        -- Insertar la venta
        INSERT INTO ventas (
            id_material, cantidad, precio_unitario, precio_final, descuento,
            cliente, telefono_cliente, email_cliente, condiciones, forma_pago,
            responsable_id, estado
        ) VALUES (
            p_id_material, p_cantidad, p_precio_unitario, v_precio_final, p_descuento,
            p_cliente, p_telefono, p_email, p_condiciones, p_forma_pago,
            p_responsable_id, 'COMPLETADA'
        );
        
        -- Actualizar el stock
        UPDATE materiales
        SET cantidad_actual = cantidad_actual - p_cantidad
        WHERE id = p_id_material;
        
        -- Registrar en log
        INSERT INTO log_actividad (usuario_id, accion, tabla_afectada, registro_id, descripcion)
        VALUES (p_responsable_id, 'VENTA', 'ventas', LAST_INSERT_ID(), 
                CONCAT('Venta de ', p_cantidad, ' unidades a ', p_cliente));
        
        COMMIT;
        SET p_resultado = 'EXITO';
    ELSE
        ROLLBACK;
        SET p_resultado = CONCAT('ERROR: Stock insuficiente. Disponible: ', v_cantidad_actual);
    END IF;
END;
