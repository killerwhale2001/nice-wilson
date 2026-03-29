"""Send HTML email briefings via Gmail SMTP with TLS."""

from __future__ import annotations

import logging
import mimetypes
import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Any

import markdown as md

logger = logging.getLogger(__name__)

_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{subject}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: #f5f5f5; margin: 0; padding: 20px; color: #333; }}
  .container {{ max-width: 800px; margin: 0 auto; background: #fff;
                border-radius: 8px; padding: 32px; box-shadow: 0 2px 8px rgba(0,0,0,.08); }}
  h1 {{ color: #1a1a2e; border-bottom: 3px solid #e94560; padding-bottom: 12px; }}
  h2 {{ color: #1a1a2e; margin-top: 28px; }}
  h3 {{ color: #16213e; }}
  a {{ color: #e94560; }}
  blockquote {{ border-left: 4px solid #e94560; margin: 0; padding-left: 16px; color: #555; }}
  code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-size: 0.9em; }}
  .positive {{ color: #1a7a4a; font-weight: bold; }}
  .negative {{ color: #c73652; font-weight: bold; }}
  .neutral  {{ color: #555; font-weight: bold; }}
  .mixed    {{ color: #e08a00; font-weight: bold; }}
  .footer {{ margin-top: 32px; padding-top: 16px; border-top: 1px solid #eee;
             font-size: 0.85em; color: #888; text-align: center; }}
</style>
</head>
<body>
<div class="container">
{body}
<div class="footer">Daily News Briefing Bot &mdash; {date}</div>
</div>
</body>
</html>
"""


class EmailDelivery:
    def __init__(self, config: dict[str, Any]) -> None:
        email_cfg = config.get("email_delivery", {})
        self.enabled: bool = email_cfg.get("enabled", True)
        self.smtp_server: str = email_cfg.get("smtp_server", "smtp.gmail.com")
        self.smtp_port: int = email_cfg.get("smtp_port", 587)
        self.sender_email: str = email_cfg.get("sender_email", "")
        self.sender_password: str = email_cfg.get("sender_password", "")
        self.sender_name: str = email_cfg.get("sender_name", "News Briefing Bot")
        self.recipients: list[str] = email_cfg.get("recipients", [])
        self.html_format: bool = email_cfg.get("html_format", True)
        self.include_attachment: bool = email_cfg.get("include_attachment", True)

    def send(self, markdown_content: str, attachment_path: str | None = None) -> bool:
        """Send the briefing. Returns True on success."""
        if not self.enabled:
            logger.info("Email delivery disabled — skipping send")
            return False
        if not self.sender_email or not self.sender_password:
            logger.error("EMAIL_ADDRESS or EMAIL_PASSWORD not configured — cannot send")
            return False
        if not self.recipients:
            logger.error("No email recipients configured")
            return False

        subject = self._subject()
        msg = self._build_message(subject, markdown_content, attachment_path)

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.ehlo()
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, self.recipients, msg.as_string())
            logger.info("Email sent to %d recipients", len(self.recipients))
            return True
        except smtplib.SMTPException as exc:
            logger.error("Email send failed: %s", exc)
            return False

    # ── Message builder ────────────────────────────────────────────────────────

    def _build_message(
        self, subject: str, markdown_content: str, attachment_path: str | None
    ) -> MIMEMultipart:
        has_attachment = self.include_attachment and attachment_path

        # Outer container: mixed (body + attachment) or alternative (body only)
        msg = MIMEMultipart("mixed") if has_attachment else MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{self.sender_name} <{self.sender_email}>"
        msg["To"] = ", ".join(self.recipients)

        # Inner alternative container holds the plain+html body so email
        # clients render it inline rather than treating it as an attachment.
        if has_attachment:
            body = MIMEMultipart("alternative")
            msg.attach(body)
        else:
            body = msg

        body.attach(MIMEText(markdown_content, "plain", "utf-8"))

        if self.html_format:
            html_body = md.markdown(
                markdown_content,
                extensions=["tables", "fenced_code", "nl2br"],
            )
            date_str = datetime.now(timezone.utc).strftime("%B %d, %Y")
            full_html = _HTML_TEMPLATE.format(
                subject=subject, body=html_body, date=date_str
            )
            body.attach(MIMEText(full_html, "html", "utf-8"))

        if has_attachment:
            self._attach_file(msg, attachment_path)

        return msg

    @staticmethod
    def _attach_file(msg: MIMEMultipart, path: str) -> None:
        file_path = Path(path)
        if not file_path.exists():
            logger.warning("Attachment not found: %s", path)
            return
        mime_type, _ = mimetypes.guess_type(str(file_path))
        mime_type = mime_type or "application/octet-stream"
        main_type, sub_type = mime_type.split("/", 1)
        part = MIMEBase(main_type, sub_type)
        part.set_payload(file_path.read_bytes())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", "attachment", filename=file_path.name)
        msg.attach(part)

    @staticmethod
    def _subject() -> str:
        date_str = datetime.now(timezone.utc).strftime("%B %d, %Y")
        return f"Executive Briefing — {date_str}"
