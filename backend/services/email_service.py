import smtplib
import random
import string
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

EMAIL_REMITENTE = "oscara200411@gmail.com"
EMAIL_PASSWORD  = "frqfnumfasvqanmm"

def generar_codigo():
    return ''.join(random.choices(string.digits, k=6))

def enviar_codigo(destinatario: str, codigo: str, tipo: str):
    print(f"=== ENVIANDO A: {destinatario} | CÓDIGO: {codigo} ===")

    if tipo == "registro":
        asunto = "Verifica tu cuenta — Planificador Anti-Estrés"
        cuerpo = f"""
        <div style="font-family:Arial,sans-serif;max-width:480px;margin:auto;background:#0F172A;color:#E2E8F0;padding:32px;border-radius:12px;">
            <h2 style="color:#4CB8A4;">Bienvenido al Planificador 👋</h2>
            <p>Para verificar tu cuenta ingresa este código:</p>
            <div style="background:#1E293B;border-radius:8px;padding:24px;text-align:center;margin:24px 0;">
                <span style="font-size:2.5rem;font-weight:bold;letter-spacing:0.5rem;color:#4CB8A4;">{codigo}</span>
            </div>
            <p style="color:#64748B;font-size:0.85rem;">Expira en 10 minutos.</p>
        </div>
        """
    else:
        asunto = "Tu código de acceso — Planificador Anti-Estrés"
        cuerpo = f"""
        <div style="font-family:Arial,sans-serif;max-width:480px;margin:auto;background:#0F172A;color:#E2E8F0;padding:32px;border-radius:12px;">
            <h2 style="color:#4CB8A4;">Código de acceso 🔐</h2>
            <p>Tu código para iniciar sesión:</p>
            <div style="background:#1E293B;border-radius:8px;padding:24px;text-align:center;margin:24px 0;">
                <span style="font-size:2.5rem;font-weight:bold;letter-spacing:0.5rem;color:#4CB8A4;">{codigo}</span>
            </div>
            <p style="color:#64748B;font-size:0.85rem;">Expira en 10 minutos.</p>
        </div>
        """

    mensaje = MIMEMultipart("alternative")
    mensaje["Subject"] = asunto
    mensaje["From"]    = EMAIL_REMITENTE
    mensaje["To"]      = destinatario
    mensaje.attach(MIMEText(cuerpo, "html"))

    try:
        servidor = smtplib.SMTP("smtp.gmail.com", 587, timeout=10)
        servidor.ehlo()
        servidor.starttls()
        servidor.ehlo()
        servidor.login(EMAIL_REMITENTE, EMAIL_PASSWORD)
        servidor.sendmail(EMAIL_REMITENTE, destinatario, mensaje.as_string())
        servidor.quit()
        print("=== CORREO ENVIADO ===")
        return True
    except Exception as e:
        print(f"=== ERROR: {e} ===")
        return False
