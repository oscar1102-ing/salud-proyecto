import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
import random
import string
import os

BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")

def generar_codigo():
    return ''.join(random.choices(string.digits, k=6))

def enviar_codigo(destinatario: str, codigo: str, tipo: str):
    print(f"=== ENVIANDO A: {destinatario} | CÓDIGO: {codigo} ===")
    
    if tipo == "registro":
        asunto = "Verifica tu cuenta — Planificador Anti-Estrés"
    else:
        asunto = "Tu código de acceso — Planificador Anti-Estrés"

    cuerpo = f"""
    <div style="font-family:Arial,sans-serif;max-width:480px;margin:auto;background:#0F172A;color:#E2E8F0;padding:32px;border-radius:12px;">
        <h2 style="color:#4CB8A4;">{"Bienvenido al Planificador 👋" if tipo == "registro" else "Código de acceso 🔐"}</h2>
        <p>{"Para verificar tu cuenta ingresa este código:" if tipo == "registro" else "Tu código para iniciar sesión:"}</p>
        <div style="background:#1E293B;border-radius:8px;padding:24px;text-align:center;margin:24px 0;">
            <span style="font-size:2.5rem;font-weight:bold;letter-spacing:0.5rem;color:#4CB8A4;">{codigo}</span>
        </div>
        <p style="color:#64748B;font-size:0.85rem;">Expira en 10 minutos.</p>
    </div>
    """

    try:
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = BREVO_API_KEY

        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
            sib_api_v3_sdk.ApiClient(configuration)
        )

        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": destinatario}],
            sender={"name": "Planificador Anti-Estrés", "email": "noreply@planificador.com"},
            subject=asunto,
            html_content=cuerpo
        )

        api_instance.send_transac_email(send_smtp_email)
        print("=== CORREO ENVIADO ===")
        return True

    except ApiException as e:
        print(f"=== ERROR BREVO: {e} ===")
        return False
    except Exception as e:
        print(f"=== ERROR: {e} ===")
        return False
