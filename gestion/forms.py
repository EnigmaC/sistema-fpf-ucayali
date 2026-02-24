from django import forms
from django.core.exceptions import ValidationError
from .models import Documento
import dns.resolver

class DocumentoForm(forms.ModelForm):
    # Campo extra para confirmar correo (no se guarda en BD, solo valida)
    email_confirmacion = forms.EmailField(
        label="Confirmar Correo",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Repita su correo'})
    )

    class Meta:
        model = Documento
        fields = ['remitente', 'dni_ruc', 'email', 'tipo_documento', 'asunto', 'archivo']
        
        widgets = {
            'remitente': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del Club o Persona'}),
            'dni_ruc': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'DNI (8 dígitos) o RUC (11 dígitos)'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'ejemplo@correo.com'}),
            'tipo_documento': forms.Select(attrs={'class': 'form-select'}),
            'asunto': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Solicitud de inscripción'}),
            'archivo': forms.FileInput(attrs={'class': 'form-control'}),
        }

    # --- VALIDACIÓN 1: DNI / RUC ---
    def clean_dni_ruc(self):
        dni = self.cleaned_data.get('dni_ruc')
        # Quitamos espacios en blanco por si acaso
        if dni:
            dni = dni.strip()
            
        if not dni.isdigit():
            raise ValidationError("El DNI/RUC solo debe contener números.")
        
        if len(dni) not in [8, 11]:
            raise ValidationError("El número debe tener exactamente 8 dígitos (DNI) u 11 dígitos (RUC).")
            
        return dni

    # --- VALIDACIÓN 2: CORREO (DOMINIO + DNS) ---
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            try:
                dominio = email.split('@')[1]
                
                # OPTIMIZACIÓN: Configuramos un tiempo límite (timeout)
                # Si el DNS tarda más de 5 segundos, asumimos que está bien para no bloquear al usuario.
                resolver = dns.resolver.Resolver()
                resolver.lifetime = 5 # 5 segundos máximo de espera
                
                resolver.resolve(dominio, 'MX')
            except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
                raise ValidationError(f"El dominio '@{dominio}' no parece válido o no recibe correos.")
            except (dns.resolver.Timeout, IndexError, Exception):
                # Si falla por tiempo o error desconocido, lo dejamos pasar (es mejor ser permisivo que bloquear a un usuario válido)
                pass
        return email

    # --- VALIDACIÓN 3: COMPARAR CORREOS ---
    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        email_confirmacion = cleaned_data.get("email_confirmacion")

        if email and email_confirmacion:
            if email != email_confirmacion:
                self.add_error('email_confirmacion', "Los correos electrónicos no coinciden.")

        return cleaned_data

    # --- VALIDACIÓN 4: ARCHIVO ---
    def clean_archivo(self):
        archivo = self.cleaned_data.get('archivo')
        if archivo:
            # 1. Validar Tamaño (10MB)
            limit_mb = 10
            if archivo.size > limit_mb * 1024 * 1024:
                raise ValidationError(f"El archivo es demasiado pesado. El límite es de {limit_mb}MB.")
            
            # 2. Validar Extensión
            nombre = archivo.name.lower()
            if not nombre.endswith(('.pdf', '.jpg', '.jpeg', '.png')):
                raise ValidationError("Formato no permitido. Solo se aceptan archivos PDF, JPG o PNG.")
        return archivo