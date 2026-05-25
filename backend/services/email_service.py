import resend
import random
import string

resend.api_key = "re_MU356q89_97bh4AcMcmp8oMhLuqj2gzyo"  # ← tu API key de Resend

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
        params = {
            "from": "Planificador <onboarding@resend.dev>",
            "to": [destinatario],
            "subject": asunto,
            "html": cuerpo
        }
        resend.Emails.send(params)
        print("=== CORREO ENVIADO ===")
        return True
    except Exception as e:
        print(f"=== ERROR: {e} ===")
        return False
