import os
import qrcode
import base64
from io import BytesIO

# --- AGREGAMOS ESTA IMPORTACIÓN ---
from django.urls import reverse 

from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Q
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.core.mail import send_mail
from django.conf import settings 

from .forms import DocumentoForm
from .models import Documento

# --- 1. VISTA LOGIN PERSONALIZADA ---
def sign_in(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'GET':
        form = AuthenticationForm()
        return render(request, 'registration/login.html', {'form': form})
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                if not request.POST.get('remember_me'):
                    request.session.set_expiry(0)
                else:
                    request.session.set_expiry(1209600)
                return redirect('dashboard')
            else:
                form.add_error(None, 'Usuario o contraseña inválidos')
        else:
            form.add_error(None, 'Usuario o contraseña inválidos')
            
        return render(request, 'registration/login.html', {'form': form})


# --- 2. VISTA DASHBOARD ---
@login_required
def panel_control(request):
    total = Documento.objects.count()
    recibidos = Documento.objects.filter(estado='REC').count()
    derivados = Documento.objects.filter(estado='DER').count()
    finalizados = Documento.objects.filter(estado='FIN').count()
    recientes = Documento.objects.order_by('-creado_el')[:10]
    
    context = {
        'total': total,
        'recibidos': recibidos,
        'derivados': derivados,
        'finalizados': finalizados,
        'recientes': recientes
    }
    return render(request, 'gestion/dashboard.html', context)


# --- 3. VISTA LISTA DE EXPEDIENTES ---
@login_required
def lista_documentos(request):
    busqueda = request.GET.get('q', '')
    filtro_estado = request.GET.get('estado', '')
    orden = request.GET.get('orden', 'desc')

    if orden == 'asc':
        documentos = Documento.objects.all().order_by('creado_el')
    else:
        documentos = Documento.objects.all().order_by('-creado_el')

    if busqueda:
        documentos = documentos.filter(
            Q(numero_expediente__icontains=busqueda) |
            Q(asunto__icontains=busqueda) |
            Q(remitente__icontains=busqueda) |
            Q(dni_ruc__icontains=busqueda)
        )

    if filtro_estado:
        documentos = documentos.filter(estado=filtro_estado)

    return render(request, 'gestion/lista_docs.html', {
        'documentos': documentos,
        'busqueda': busqueda,
        'filtro_estado': filtro_estado,
        'orden': orden 
    })


# --- 4. VISTA MESA DE PARTES PÚBLICA ---
def mesa_partes_publica(request):
    if request.method == 'POST':
        form = DocumentoForm(request.POST, request.FILES)
        if form.is_valid():
            nuevo_doc = form.save(commit=False)
            nuevo_doc.estado = 'REC'
            nuevo_doc.save()
            
            request.session['ultimo_doc_id'] = nuevo_doc.id
            fecha_peru = timezone.localtime(nuevo_doc.creado_el)
            
            asunto = f"Confirmación de Recepción - Expediente {nuevo_doc.numero_expediente}"
            mensaje = f"""
            ESTIMADO(A) USUARIO,
            
            La Federación Peruana de Fútbol - Departamental Ucayali ha recibido su documento correctamente.
            
            --- DETALLES DEL TRÁMITE ---
            N° Expediente: {nuevo_doc.numero_expediente}
            Remitente: {nuevo_doc.remitente}
            Asunto: {nuevo_doc.asunto}
            Fecha: {fecha_peru.strftime('%d/%m/%Y a las %H:%M')}
            ----------------------------
            
            Puede descargar su cargo de recepción en la pantalla de confirmación.
            
            Atentamente,
            Mesa de Partes Virtual FPF.
            """
            
            try:
                send_mail(
                    asunto,
                    mensaje,
                    settings.DEFAULT_FROM_EMAIL,
                    [nuevo_doc.email],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Error enviando correo de confirmación: {e}")

            return render(request, 'gestion/exito_tramite.html', {'doc': nuevo_doc})
    else:
        form = DocumentoForm()

    return render(request, 'gestion/mesa_publica.html', {'form': form})


# --- 5. VISTA CAMBIAR ESTADO ---
@login_required
def cambiar_estado(request, doc_id, nuevo_estado):
    doc = get_object_or_404(Documento, id=doc_id)
    doc.estado = nuevo_estado
    doc.save()

    asunto = f"Actualización de Estado - Expediente {doc.numero_expediente}"
    
    cuerpo = ""
    if nuevo_estado == 'DER':
        cuerpo = f"El expediente {doc.numero_expediente} ha sido DERIVADO al área correspondiente para su gestión."
    elif nuevo_estado == 'FIN':
        cuerpo = f"El expediente {doc.numero_expediente} ha sido FINALIZADO/ARCHIVADO."
    elif nuevo_estado == 'REV':
        cuerpo = f"El expediente {doc.numero_expediente} ha entrado en proceso de REVISIÓN."
    elif nuevo_estado == 'OBS':
        cuerpo = f"El expediente {doc.numero_expediente} ha sido OBSERVADO. Por favor contacte con administración para subsanar."
    else:
        cuerpo = f"El expediente {doc.numero_expediente} ha cambiado de estado."

    mensaje_completo = f"""
    ACTUALIZACIÓN DE TRÁMITE - FPF UCAYALI
    
    Estimado usuario,
    
    {cuerpo}
    
    Remitente Original: {doc.remitente}
    Asunto: {doc.asunto}
    
    Atentamente,
    Sistema de Gestión Documental.
    """

    try:
        send_mail(
            asunto,
            mensaje_completo,
            settings.DEFAULT_FROM_EMAIL,
            [doc.email], 
            fail_silently=False,
        )
    except Exception as e:
        print(f"Error al enviar notificación de estado: {e}")

    return redirect('home')


# --- 6. VISTA GENERAR PDF DEL CARGO (ACTUALIZADA CON QR LINK) ---
def generar_cargo(request, doc_id):
    # Seguridad
    es_admin = request.user.is_authenticated
    es_dueno = (str(doc_id) == str(request.session.get('ultimo_doc_id'))) 
    
    if not es_admin and not es_dueno:
        return redirect('mesa_publica') 

    doc = get_object_or_404(Documento, pk=doc_id)
    
    # A. Generar QR (CON ENLACE DE SEGUIMIENTO)
    # 1. Construimos la URL completa (detecta si es localhost o render)
    path_consulta = reverse('consultar_tramite') 
    url_completa = request.build_absolute_uri(path_consulta)
    
    # 2. Creamos el link directo con los datos pre-llenados
    # Ejemplo: https://dominio.com/consultar?expediente=EXP-001&dni=12345678
    qr_data = f"{url_completa}?expediente={doc.numero_expediente}&dni={doc.dni_ruc}"
    
    qr = qrcode.QRCode(version=1, box_size=5, border=2)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white")
    
    # Guardar imagen en memoria
    buffer = BytesIO()
    img_qr.save(buffer, format="PNG")
    qr_image_base64 = base64.b64encode(buffer.getvalue()).decode()

    # B. Buscar Logo
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'gestion', 'img', 'logo_fpf.png')
    logo_base64 = ""
    
    if os.path.exists(logo_path):
        try:
            with open(logo_path, "rb") as image_file:
                logo_data = base64.b64encode(image_file.read()).decode()
                logo_base64 = f"data:image/png;base64,{logo_data}"
        except Exception as e:
            print(f"Error leyendo logo: {e}")

    # C. Renderizar PDF
    template_path = 'gestion/cargo_pdf.html'
    context = {
        'doc': doc, 
        'qr_code': qr_image_base64,
        'logo_url': logo_base64
    }
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Cargo_{doc.numero_expediente}.pdf"'
    
    template = get_template(template_path)
    html = template.render(context)
    
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    if pisa_status.err:
        return HttpResponse('Error al generar PDF')
    
    return response


# --- 7. VISTA PÚBLICA: CONSULTAR ESTADO DE TRÁMITE ---
def consultar_tramite(request):
    numero_expediente = request.GET.get('expediente', '').strip()
    dni_ruc = request.GET.get('dni', '').strip()
    
    documento = None
    buscado = False
    error = None
    
    if numero_expediente or dni_ruc:
        buscado = True
        if numero_expediente and dni_ruc:
            try:
                documento = Documento.objects.get(numero_expediente=numero_expediente, dni_ruc=dni_ruc)
            except Documento.DoesNotExist:
                error = "No se encontró ningún trámite. Verifique que el N° de Expediente y el DNI/RUC sean correctos."
        else:
            error = "Debe ingresar tanto el N° de Expediente como su DNI/RUC por seguridad."
            
    return render(request, 'gestion/consulta_tramite.html', {
        'documento': documento,
        'buscado': buscado,
        'error': error,
        'expediente_val': numero_expediente,
        'dni_val': dni_ruc
    })