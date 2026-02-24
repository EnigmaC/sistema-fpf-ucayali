from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Importamos todas las vistas de nuestra app 'gestion'
# OJO: Agregamos 'sign_in' a la lista de importaciones
from gestion.views import (
    lista_documentos, 
    generar_cargo, 
    cambiar_estado, 
    mesa_partes_publica, 
    panel_control,
    consultar_tramite,
    sign_in 
)

urlpatterns = [
    # --- 🛡️ CAMBIO DE SEGURIDAD 🛡️ ---
    path('sistema-interno-fpf/', admin.site.urls),
    
    # --- AUTENTICACIÓN (LOGIN/LOGOUT) ---
    path('accounts/', include('django.contrib.auth.urls')),
    
    # --- RUTAS PRINCIPALES ---
    
    # 1. Login Personalizado (Raíz):
    # Al entrar a "tudominio.com", el sistema verifica si eres tú.
    # Si sí -> te manda a dashboard. Si no -> muestra login.
    path('', sign_in, name='login'),
    
    # 2. Dashboard:
    # Esta es la página protegida donde verás las estadísticas.
    path('dashboard/', panel_control, name='dashboard'),
    
    # 3. Lista de Expedientes: Donde gestionas y filtras todo
    path('expedientes/', lista_documentos, name='home'),
    
    # 4. Mesa de Partes Virtual: El formulario público
    path('mesa-virtual/', mesa_partes_publica, name='mesa_publica'),
    
    # 5. Consultar Estado de Trámite
    path('consultar-tramite/', consultar_tramite, name='consultar_tramite'),
    
    # --- FUNCIONALIDADES ---
    # Generar PDF del cargo
    path('cargo/<int:doc_id>/', generar_cargo, name='generar_cargo'),
    
    # Cambiar estado (Derivar, Finalizar)
    path('cambiar-estado/<int:doc_id>/<str:nuevo_estado>/', cambiar_estado, name='cambiar_estado'),
]

# --- CONFIGURACIÓN PARA ARCHIVOS (Solo en Desarrollo) ---
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)