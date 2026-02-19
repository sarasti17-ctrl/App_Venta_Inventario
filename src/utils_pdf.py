from fpdf import FPDF
from datetime import datetime
import os
import io

class TicketGenerator:
    """Generador de tickets de venta en formato PDF."""
    
    def __init__(self):
        self.company_name = "Sarasti"
        self.brand_name = "Collec"
        self.address = "Almacén Central de Inventarios"
        self.logo_path = os.path.join(os.path.dirname(__file__), "..", "data", "LogoCollec.jpg")
    
    def generate_ticket(self, sale_data, items_list):
        """
        Genera un PDF en memoria (BytesIO) con los datos de la venta.
        
        sale_data: dict con 'cliente', 'total', 'descuento', 'forma_pago', 'condiciones'
        items_list: lista de dicts, cada uno con 'descripcion', 'codigo_interno', 'unidad_medida', 'cantidad', 'precio_unitario', 'subtotal'
        """
        pdf = FPDF(orientation='P', unit='mm', format='A4')
        pdf.add_page()
        pdf.set_font("Arial", '', 10) # Fuente por defecto
        
        # --- Encabezado ---
        if os.path.exists(self.logo_path):
            # Centrar imagen (Ancho de página es 210mm, margen 10mm -> 190mm usable)
            # Logo ancho 50mm
            pdf.image(self.logo_path, x=80, y=10, w=50)
            pdf.ln(25) # Espacio para el logo
        else:
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, self.company_name, ln=True, align='C')
            pdf.set_font("Arial", 'I', 12)
            pdf.cell(0, 7, f"Marca: {self.brand_name}", ln=True, align='C')
            pdf.set_font("Arial", '', 10) # Restaurar para el resto
        pdf.cell(0, 5, self.address, ln=True, align='C')
        pdf.cell(0, 5, f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align='C')
        pdf.ln(10)
        
        # --- Información del Cliente ---
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, "DATOS DE LA VENTA", ln=True, border='B')
        pdf.ln(2)
        
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(30, 6, "Cliente:", 0)
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 6, str(sale_data['cliente']), ln=True)
        
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(30, 6, "Teléfono:", 0)
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 6, str(sale_data.get('telefono', 'N/A')), ln=True)
        
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(30, 6, "Pago:", 0)
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 6, str(sale_data['forma_pago']), ln=True)
        pdf.ln(5)
        
        # --- Detalle de Productos ---
        pdf.set_font("Arial", 'B', 10)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(25, 8, "CÓDIGO", 1, 0, 'C', fill=True)
        pdf.cell(85, 8, "DESCRIPCIÓN", 1, 0, 'C', fill=True)
        pdf.cell(25, 8, "CANT.", 1, 0, 'C', fill=True)
        pdf.cell(25, 8, "PRECIO U.", 1, 0, 'C', fill=True)
        pdf.cell(30, 8, "TOTAL", 1, 1, 'C', fill=True)
        
        pdf.set_font("Arial", '', 9)
        subtotal_acumulado = 0
        
        for item in items_list:
            # Limitar descripción si es muy larga
            desc = item['descripcion']
            if len(desc) > 45: desc = desc[:42] + "..."
            
            pdf.cell(25, 7, str(item['codigo_interno']), 1, 0, 'C')
            pdf.cell(85, 7, desc, 1, 0, 'L')
            pdf.cell(25, 7, f"{float(item['cantidad']):,.3f} {item['unidad_medida']}", 1, 0, 'C')
            precio_u = float(item['precio_unitario'])
            pdf.cell(25, 7, f"${precio_u:,.2f}", 1, 0, 'R')
            
            line_total = float(item['subtotal'])
            pdf.cell(30, 7, f"${line_total:,.2f}", 1, 1, 'R')
            subtotal_acumulado += line_total
            
        # --- Sección de Totales ---
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 10)
        pdf.set_x(130)
        pdf.cell(40, 8, "Subtotal:", 0, 0, 'R')
        pdf.set_font("Arial", '', 10)
        pdf.cell(30, 8, f"${subtotal_acumulado:,.2f}", 0, 1, 'R')
        
        descuento_pct = float(sale_data.get('descuento', 0) or 0)
        if descuento_pct > 0:
            monto_desc = subtotal_acumulado * (descuento_pct / 100.0)
            pdf.set_x(130)
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(40, 8, f"Descuento ({descuento_pct}%):", 0, 0, 'R')
            pdf.set_font("Arial", '', 10)
            pdf.cell(30, 8, f"-${monto_desc:,.2f}", 0, 1, 'R')
            
            total_final = subtotal_acumulado - monto_desc
        else:
            total_final = subtotal_acumulado
            
        pdf.set_x(130)
        pdf.set_font("Arial", 'B', 12)
        pdf.set_text_color(0, 128, 0)
        pdf.cell(40, 10, "TOTAL FINAL:", 0, 0, 'R')
        pdf.cell(30, 10, f"${total_final:,.2f}", 0, 1, 'R')
        pdf.set_text_color(0, 0, 0)
        
        # --- Observaciones ---
        if sale_data.get('condiciones'):
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(0, 6, "Condiciones y Observaciones:", ln=True)
            pdf.set_font("Arial", '', 9)
            pdf.multi_cell(0, 5, str(sale_data['condiciones']))
        
        # --- Footer ---
        pdf.ln(15)
        pdf.set_font("Arial", 'I', 8)
        pdf.cell(0, 5, "Este documento es un comprobante de liquidación de inventario.", ln=True, align='C')
        pdf.cell(0, 5, "¡Gracias por su compra!", ln=True, align='C')
        
        # Generar output como bytes
        buf = io.BytesIO()
        pdf_bytes = pdf.output() # fpdf2 output() returns bytes by default if format='S' or nothing
        # En fpdf2, output() sin argumentos devuelve los bytes directamente
        return bytes(pdf_bytes)
