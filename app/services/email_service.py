import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import get_settings

logger = logging.getLogger(__name__)


def send_verification_email(to_email: str, code: str, is_login: bool = True) -> bool:
    """Send a verification code via SMTP."""
    settings = get_settings()

    subject = f"Je verificatiecode: {code}" if is_login else f"Bevestig je account: {code}"
    action = "in te loggen" if is_login else "je account te bevestigen"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; background-color: #f3f4f6; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
      <div style="max-width: 480px; margin: 40px auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.07);">
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #059669, #047857); padding: 32px; text-align: center;">
          <div style="display: inline-flex; align-items: center; gap: 10px;">
            <div style="width: 40px; height: 40px; background: rgba(255,255,255,0.2); border-radius: 12px; display: inline-flex; align-items: center; justify-content: center;">
              <span style="font-size: 20px; color: white;">&#9889;</span>
            </div>
            <span style="font-size: 22px; font-weight: 700; color: white; letter-spacing: -0.5px;">FiscalFlow</span>
          </div>
        </div>

        <!-- Body -->
        <div style="padding: 32px;">
          <h1 style="font-size: 20px; font-weight: 700; color: #111827; margin: 0 0 8px;">
            Verificatiecode
          </h1>
          <p style="font-size: 14px; color: #6b7280; margin: 0 0 24px; line-height: 1.6;">
            Gebruik onderstaande code om {action} bij FiscalFlow. Deze code is 10 minuten geldig.
          </p>

          <!-- Code -->
          <div style="background: #f0fdf4; border: 2px solid #bbf7d0; border-radius: 12px; padding: 20px; text-align: center; margin: 0 0 24px;">
            <div style="font-size: 36px; font-weight: 800; color: #059669; letter-spacing: 8px; font-family: 'Courier New', monospace;">
              {code}
            </div>
          </div>

          <p style="font-size: 13px; color: #9ca3af; margin: 0 0 4px;">
            Heb je deze code niet aangevraagd? Dan kun je deze e-mail negeren.
          </p>
          <p style="font-size: 13px; color: #9ca3af; margin: 0;">
            De code verloopt automatisch na 10 minuten.
          </p>
        </div>

        <!-- Footer -->
        <div style="background: #f9fafb; padding: 20px 32px; border-top: 1px solid #e5e7eb;">
          <p style="font-size: 11px; color: #9ca3af; margin: 0; text-align: center;">
            &copy; 2026 FiscalFlow | AI-powered boekhouding voor Nederlandse ondernemers<br>
            <a href="https://fiscalflow.nl" style="color: #059669; text-decoration: none;">fiscalflow.nl</a>
          </p>
        </div>
      </div>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{settings.MAIL_FROM_NAME} <{settings.MAIL_FROM}>"
    msg["To"] = to_email

    # Plain text fallback
    text = f"Je FiscalFlow verificatiecode is: {code}\n\nDeze code is 10 minuten geldig.\n\nHeb je deze code niet aangevraagd? Negeer deze e-mail."
    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))

    try:
        if settings.MAIL_USE_SSL:
            with smtplib.SMTP_SSL(settings.MAIL_HOST, settings.MAIL_PORT, timeout=10) as server:
                server.login(settings.MAIL_FROM, settings.MAIL_PASSWORD)
                server.sendmail(settings.MAIL_FROM, to_email, msg.as_string())
        else:
            with smtplib.SMTP(settings.MAIL_HOST, settings.MAIL_PORT, timeout=10) as server:
                server.starttls()
                server.login(settings.MAIL_FROM, settings.MAIL_PASSWORD)
                server.sendmail(settings.MAIL_FROM, to_email, msg.as_string())
        logger.info(f"Verification email sent to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False


def send_welcome_email(to_email: str, name: str) -> bool:
    """Send a welcome email after successful registration."""
    settings = get_settings()

    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="margin: 0; padding: 0; background-color: #f3f4f6; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
      <div style="max-width: 480px; margin: 40px auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.07);">
        <div style="background: linear-gradient(135deg, #059669, #047857); padding: 32px; text-align: center;">
          <span style="font-size: 22px; font-weight: 700; color: white;">&#9889; FiscalFlow</span>
        </div>
        <div style="padding: 32px;">
          <h1 style="font-size: 20px; font-weight: 700; color: #111827; margin: 0 0 8px;">
            Welkom bij FiscalFlow, {name}!
          </h1>
          <p style="font-size: 14px; color: #6b7280; line-height: 1.6;">
            Je account is succesvol aangemaakt. Je kunt nu inloggen en beginnen met je boekhouding.
          </p>
          <div style="margin: 24px 0;">
            <a href="{settings.FRONTEND_URL}/login" style="display: inline-block; background: #059669; color: white; padding: 12px 24px; border-radius: 10px; font-size: 14px; font-weight: 600; text-decoration: none;">
              Ga naar FiscalFlow
            </a>
          </div>
          <p style="font-size: 13px; color: #9ca3af;">
            Vragen? Mail ons op {settings.MAIL_FROM}
          </p>
        </div>
        <div style="background: #f9fafb; padding: 20px 32px; border-top: 1px solid #e5e7eb;">
          <p style="font-size: 11px; color: #9ca3af; margin: 0; text-align: center;">
            &copy; 2026 FiscalFlow | fiscalflow.nl
          </p>
        </div>
      </div>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Welkom bij FiscalFlow, {name}!"
    msg["From"] = f"{settings.MAIL_FROM_NAME} <{settings.MAIL_FROM}>"
    msg["To"] = to_email

    text = f"Welkom bij FiscalFlow, {name}!\n\nJe account is aangemaakt. Log in op {settings.FRONTEND_URL}/login"
    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))

    try:
        if settings.MAIL_USE_SSL:
            with smtplib.SMTP_SSL(settings.MAIL_HOST, settings.MAIL_PORT, timeout=10) as server:
                server.login(settings.MAIL_FROM, settings.MAIL_PASSWORD)
                server.sendmail(settings.MAIL_FROM, to_email, msg.as_string())
        else:
            with smtplib.SMTP(settings.MAIL_HOST, settings.MAIL_PORT, timeout=10) as server:
                server.starttls()
                server.login(settings.MAIL_FROM, settings.MAIL_PASSWORD)
                server.sendmail(settings.MAIL_FROM, to_email, msg.as_string())
        logger.info(f"Welcome email sent to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send welcome email to {to_email}: {e}")
        return False
