from django.contrib import admin
from django.utils.html import format_html # Necesario para los colores
from .models import Documento

@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    # --- LISTA PRINCIPAL (Columnas) ---
    # Cambiamos 'estado' por 'estado_badge' para que se vea con color
    list_display = (
        'numero_expediente', 
        'estado_badge',  # <--- COLUMNA PERSONALIZADA
        'tipo_documento', 
        'remitente', 
        'asunto', 
        'area_destino', 
        'fecha_recepcion'
    )
    
    # --- FILTROS Y BÚSQUEDA ---
    list_filter = ('estado', 'area_destino', 'tipo_documento', 'creado_el')
    search_fields = ('numero_expediente', 'remitente', 'asunto', 'dni_ruc', 'email')
    
    # Navegación por fechas (Aparece arriba de la lista)
    date_hierarchy = 'creado_el'
    
    # Campos que no se pueden editar
    readonly_fields = ('numero_expediente', 'creado_el', 'recepcionado_por')

    # --- ORGANIZACIÓN DEL FORMULARIO ---
    fieldsets = (
        ('Identificación del Trámite', {
            'fields': ('numero_expediente', 'estado', 'recepcionado_por')
        }),
        ('Datos del Remitente', {
            # ¡OJO! Aquí faltaba 'email'. Ya lo agregué 👇
            'fields': ('remitente', 'dni_ruc', 'email', 'tipo_documento', 'asunto')
        }),
        ('Derivación Interna', {
            'fields': ('area_destino', 'archivo')
        }),
    )

    # --- FUNCIONES PERSONALIZADAS ---

    # 1. Formato de fecha amigable
    def fecha_recepcion(self, obj):
        return obj.creado_el.strftime("%d/%m/%Y %H:%M")
    fecha_recepcion.short_description = 'Fecha Recepción'
    fecha_recepcion.admin_order_field = 'creado_el'

    # 2. Etiquetas de colores para los Estados (Igual que en tu Dashboard)
    def estado_badge(self, obj):
        colors = {
            'REC': '#0d6efd', # Azul (Primary)
            'DER': '#0dcaf0', # Cyan (Info)
            'REV': '#ffc107', # Amarillo (Warning)
            'OBS': '#dc3545', # Rojo (Danger)
            'FIN': '#198754', # Verde (Success)
        }
        color = colors.get(obj.estado, '#6c757d') # Gris por defecto
        nombre = obj.get_estado_display()
        
        # Generamos el HTML de la etiqueta
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 50px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            nombre
        )
    estado_badge.short_description = 'Estado Actual'
    estado_badge.admin_order_field = 'estado'

    # --- LÓGICA DE GUARDADO ---
    # Auto-asignar el usuario que registra el documento (si es nuevo)
    def save_model(self, request, obj, form, change):
        if not change: # Solo al crear
            obj.recepcionado_por = request.user
        super().save_model(request, obj, form, change)