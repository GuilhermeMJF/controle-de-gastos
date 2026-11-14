"""Envio de e-mails pela API HTTP do Brevo.

O Render gratuito bloqueia as portas de e-mail tradicionais (SMTP), então o envio
é feito por uma chamada HTTPS comum, que não é bloqueada.
"""

import json
import logging
import urllib.error
import urllib.request
from html import escape

from .config import (
    BREVO_API_KEY,
    EMAIL_REMETENTE,
    NOME_REMETENTE,
    REDEFINICAO_EXPIRA_MINUTOS,
)

logger = logging.getLogger("controle_de_gastos")

URL_BREVO = "https://api.brevo.com/v3/smtp/email"


def enviar_email(para_email: str, para_nome: str, assunto: str, html: str, texto: str):
    if not BREVO_API_KEY or not EMAIL_REMETENTE:
        # Sem Brevo configurado (ex.: no seu computador): mostra o e-mail no log
        logger.warning(
            "Envio de e-mail não configurado. E-mail que seria enviado para %s:\n"
            "Assunto: %s\n%s",
            para_email,
            assunto,
            texto,
        )
        return

    corpo = {
        "sender": {"name": NOME_REMETENTE, "email": EMAIL_REMETENTE},
        "to": [{"email": para_email, "name": para_nome}],
        "subject": assunto,
        "htmlContent": html,
        "textContent": texto,
    }
    pedido = urllib.request.Request(
        URL_BREVO,
        data=json.dumps(corpo).encode(),
        headers={
            "api-key": BREVO_API_KEY,
            "content-type": "application/json",
            "accept": "application/json",
        },
        method="POST",
    )
    # URL_BREVO é uma constante https, nunca vem do usuário
    if pedido.type != "https":
        raise ValueError("O envio de e-mail só aceita URLs https")
    try:
        with urllib.request.urlopen(pedido, timeout=10) as resposta:  # nosemgrep: dynamic-urllib-use-detected
            resposta.read()
    except urllib.error.HTTPError as erro:
        detalhe = erro.read()[:500].decode(errors="replace")
        logger.error("O Brevo recusou o e-mail para %s (%s): %s", para_email, erro.code, detalhe)
    except OSError as erro:
        logger.error("Falha ao enviar e-mail para %s: %s", para_email, erro)


def enviar_email_de_redefinicao(para_email: str, para_nome: str, link: str):
    primeiro_nome = para_nome.split(" ")[0]
    assunto = "Redefinição de senha - Controle de Gastos"
    texto = (
        f"Olá, {primeiro_nome}!\n\n"
        "Recebemos um pedido para redefinir a senha da sua conta no Controle de Gastos.\n"
        f"Para criar uma nova senha, abra o link abaixo (ele vale por "
        f"{REDEFINICAO_EXPIRA_MINUTOS} minutos e só pode ser usado uma vez):\n\n"
        f"{link}\n\n"
        "Se não foi você que pediu, é só ignorar este e-mail: sua senha continua a mesma."
    )
    html = f"""
<div style="font-family: Arial, sans-serif; max-width: 480px; color: #1f2937;">
  <h2 style="margin-bottom: 8px;">Controle de Gastos</h2>
  <p>Olá, {escape(primeiro_nome)}!</p>
  <p>Recebemos um pedido para redefinir a senha da sua conta.</p>
  <p style="margin: 24px 0;">
    <a href="{escape(link)}"
       style="background: #0f766e; color: #ffffff; padding: 12px 20px;
              border-radius: 8px; text-decoration: none; display: inline-block;">
      Criar nova senha
    </a>
  </p>
  <p style="color: #6b7280; font-size: 14px;">
    O link vale por {REDEFINICAO_EXPIRA_MINUTOS} minutos e só pode ser usado uma vez.
    Se não foi você que pediu, é só ignorar este e-mail: sua senha continua a mesma.
  </p>
</div>
"""
    enviar_email(para_email, para_nome, assunto, html, texto)
