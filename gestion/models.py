from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator # Para validar que solo sean números
from cloudinary.models import CloudinaryField
import datetime

class Documento(models.Model):
    # --- 1. DATOS DEL TRÁMITE ---
    TIPOS_DOC = [
        ('OFI', 'Oficio'),
        ('SOL', 'Solicitud'),
        ('CAR', 'Carta'),
        ('MEM', 'Memorándum'),
        ('RES', 'Resolución'),
    ]
    AREAS_DESTINO = [
        ('PRES', 'Presidencia'),
        ('SEC', 'Secretaría General'),
        ('JUST', 'Comisión de Justicia'),
        ('COMP', 'Competiciones'),
        ('LOG', 'Logística'),
    ]
    ESTADOS = [
        ('REC', 'Recibido'),
        ('REV', 'En Revisión'),
        ('DER', 'Derivado'),
        ('OBS', 'Observado'),
        ('FIN', 'Finalizado/Archivado'),
    ]

    # El código único del trámite (Ej: EXP-2026-0005)
    numero_expediente = models.CharField(max_length=20, unique=True, editable=False)
    
    asunto = models.CharField(max_length=200, help_text="Ej: Solicitud de inscripción al torneo")
    tipo_documento = models.CharField(max_length=3, choices=TIPOS_DOC, default='OFI')
    
    # --- 2. ORIGEN (¿Quién lo manda?) ---
    remitente = models.CharField(max_length=150, help_text="Institución o persona que envía el documento")
    
    # MEJORA: Validación para asegurar que solo entren números (Backend safety)
    dni_ruc = models.CharField(
        "DNI / RUC", 
        max_length=15,
        validators=[RegexValidator(r'^\d+$', 'Solo se permiten números.')]
    )
    email = models.EmailField(verbose_name="Correo Electrónico")
    
    # --- 3. DESTINO (¿A dónde va?) ---
    area_destino = models.CharField(max_length=4, choices=AREAS_DESTINO, default='SEC')
    estado = models.CharField(max_length=3, choices=ESTADOS, default='REC')

    # --- 4. EL ARCHIVO ---
    # MEJORA: 'folder' organiza los archivos en una carpeta dentro de tu Cloudinary
    archivo = CloudinaryField(
        'documento', 
        resource_type='auto', 
        folder='tramites_fpf_ucayali' 
    ) 
    
    # --- 5. AUDITORÍA ---
    creado_el = models.DateTimeField(auto_now_add=True)
    actualizado_el = models.DateTimeField(auto_now=True)
    recepcionado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-creado_el'] # Orden por defecto: El más nuevo primero
        verbose_name = "Documento"
        verbose_name_plural = "Documentos"

    def save(self, *args, **kwargs):
        # LÓGICA AUTOMÁTICA DE EXPEDIENTE (CORREGIDA)
        if not self.numero_expediente:
            year = datetime.date.today().year
            
            # Buscamos el ÚLTIMO documento creado este año (ordenado por ID descendente)
            ultimo_doc = Documento.objects.filter(numero_expediente__contains=str(year)).order_by('-id').first()
            
            if ultimo_doc:
                # Si existe, extraemos el número final. Ej: "EXP-2026-0005" -> "0005"
                correlativo_actual = int(ultimo_doc.numero_expediente.split('-')[-1])
                nuevo_correlativo = correlativo_actual + 1
            else:
                # Si es el primero del año
                nuevo_correlativo = 1
            
            self.numero_expediente = f"EXP-{year}-{nuevo_correlativo:04d}" # Genera: EXP-2026-0001
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.numero_expediente} - {self.asunto}"