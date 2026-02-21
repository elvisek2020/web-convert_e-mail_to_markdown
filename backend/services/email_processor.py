import asyncio
import base64
import logging
import re
import tempfile
import unicodedata
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import mailparser
import markdownify
import yaml

from models.schemas import EmailMetadata

logger = logging.getLogger("app.email_processor")


class EmailProcessor:
    def __init__(self, root_folder: str):
        self.root_folder = Path(root_folder)
        self.root_folder.mkdir(parents=True, exist_ok=True)
        self.temp_dir = Path(tempfile.gettempdir()) / "transcendence_emails"
        self.temp_dir.mkdir(exist_ok=True)

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """Strip path separators and dangerous characters from a filename."""
        name = Path(filename).name
        name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
        name = name.strip(". ")
        return name or "unknown"

    async def save_temp_file(self, file) -> Path:
        """Uloží uploadovaný soubor dočasně s unikátním názvem."""
        suffix = Path(file.filename).suffix if file.filename else ".eml"
        unique_name = f"{uuid.uuid4().hex}{suffix}"
        temp_path = self.temp_dir / unique_name

        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)

        return temp_path

    async def parse_email(self, eml_path: Path) -> tuple[EmailMetadata, mailparser.MailParser]:
        """Parsuje .eml soubor a vrátí (metadata, raw mail object)."""
        mail = await asyncio.to_thread(mailparser.parse_from_file, str(eml_path))

        from_email = mail.from_[0][1] if mail.from_ else ""
        from_domain = from_email.split("@")[-1] if "@" in from_email else ""

        to_emails = [addr[1] for addr in mail.to] if mail.to else []
        cc_emails = [addr[1] for addr in mail.cc] if mail.cc else []

        body_text = mail.text_plain[0] if mail.text_plain else ""
        body_html = mail.text_html[0] if mail.text_html else ""

        if not body_text and body_html:
            body_text = markdownify.markdownify(body_html, heading_style="ATX")

        attachments = []
        inline_images = []
        if mail.attachments:
            for att in mail.attachments:
                safe_name = self._sanitize_filename(att.get("filename", "unknown"))
                att_data = {
                    "filename": safe_name,
                    "content_type": att.get("content_type", "application/octet-stream"),
                    "size": len(att.get("payload", b"")) if att.get("payload") else 0,
                }
                attachments.append(att_data)

                if att.get("content_disposition") == "inline":
                    inline_images.append({
                        "cid": att.get("content_id", ""),
                        "filename": safe_name,
                        "content_type": att.get("content_type", ""),
                    })

        metadata = EmailMetadata(
            subject=mail.subject or "",
            from_email=from_email,
            from_domain=from_domain,
            to=to_emails,
            cc=cc_emails,
            date=mail.date if mail.date else datetime.now(),
            body_text=body_text,
            body_html=body_html,
            attachments=attachments,
            inline_images=inline_images,
        )

        return metadata, mail

    def _normalize_project_name(self, text: str) -> str:
        """Normalizuje název projektu -- alfanumerické znaky a podtržítka."""
        if not text:
            return ""

        text = unicodedata.normalize("NFKD", text)
        text = text.encode("ascii", "ignore").decode("ascii")
        text = re.sub(r"[\s\-\.]+", "_", text)
        text = re.sub(r"[^a-zA-Z0-9_]", "", text)
        text = re.sub(r"_+", "_", text)
        return text.strip("_")

    def _slugify(self, text: str, max_length: int = 100) -> str:
        """Převede text na slug."""
        text = unicodedata.normalize("NFKD", text)
        text = text.encode("ascii", "ignore").decode("ascii")
        text = text.lower()
        text = re.sub(r"[^a-z0-9_-]", "", text)
        text = re.sub(r"[-\s]+", "-", text)
        text = text[:max_length]
        return text.strip("-")

    @staticmethod
    def _resolve_payload(payload) -> bytes | None:
        """Normalize attachment payload to bytes."""
        if isinstance(payload, bytes):
            return payload
        if isinstance(payload, str):
            try:
                return base64.b64decode(payload.strip())
            except Exception:
                pass
            try:
                return payload.encode("utf-8")
            except Exception:
                pass
            try:
                return payload.encode("latin-1")
            except Exception:
                return None
        if isinstance(payload, list):
            try:
                return b"".join(bytes([b]) if isinstance(b, int) else b for b in payload)
            except Exception:
                return None
        try:
            return bytes(payload)
        except Exception:
            return None

    def _convert_and_save_sync(
        self,
        temp_eml_path: Path,
        email_data: EmailMetadata,
        project_name: str,
        project_in_inbox: bool,
        inbox_folder: str | None,
        mail_object: mailparser.MailParser | None,
    ) -> Dict[str, Any]:
        """Synchronous core of convert_and_save (runs in thread pool)."""
        if project_in_inbox and inbox_folder:
            project_path = self.root_folder / inbox_folder / project_name
        else:
            project_path = self.root_folder / project_name

        attachments_path = project_path / "attachments"

        project_path.mkdir(parents=True, exist_ok=True)
        attachments_path.mkdir(parents=True, exist_ok=True)

        slug = self._slugify(email_data.subject)
        date_str = email_data.date.strftime("%Y-%m-%d_%H-%M-%S")
        md_filename = f"{date_str}_{slug}.md"
        md_path = project_path / md_filename

        if md_path.exists():
            raise FileExistsError(f"Soubor {md_filename} již existuje v projektu {project_name}")

        attachment_payloads: dict[str, bytes] = {}
        inline_image_payloads: dict[str, bytes] = {}

        mail = mail_object
        if mail is None and temp_eml_path.exists():
            mail = mailparser.parse_from_file(str(temp_eml_path))

        if mail and mail.attachments:
            for att in mail.attachments:
                raw_name = att.get("filename", "unknown")
                safe_name = self._sanitize_filename(raw_name)
                payload = self._resolve_payload(att.get("payload"))
                if payload is None:
                    logger.warning("Nelze dekódovat přílohu: %s", safe_name)
                    continue

                if att.get("content_disposition") == "inline":
                    inline_image_payloads[safe_name] = payload
                else:
                    attachment_payloads[safe_name] = payload

        front_matter = {
            "subject": email_data.subject,
            "from": email_data.from_email,
            "to": email_data.to,
            "cc": email_data.cc,
            "date": email_data.date.isoformat(),
            "attachments": [att["filename"] for att in email_data.attachments],
        }

        with open(md_path, "w", encoding="utf-8") as f:
            f.write("---\n")
            f.write(yaml.dump(front_matter, allow_unicode=True, default_flow_style=False))
            f.write("---\n\n")
            f.write(email_data.body_text)

        for att in email_data.attachments:
            filename = att["filename"]
            payload = attachment_payloads.get(filename)
            if payload and len(payload) > 0:
                att_path = attachments_path / filename
                with open(att_path, "wb") as f:
                    f.write(payload)

        for img in email_data.inline_images:
            filename = img["filename"]
            payload = inline_image_payloads.get(filename)
            if payload and len(payload) > 0:
                img_path = attachments_path / filename
                with open(img_path, "wb") as f:
                    f.write(payload)

        return {
            "status": "success",
            "project_name": project_name,
            "filename": md_filename,
            "path": str(md_path),
        }

    async def convert_and_save(
        self,
        temp_eml_path: Path,
        email_data: EmailMetadata,
        project_name: str,
        project_in_inbox: bool = True,
        inbox_folder: str = None,
        mail_object: mailparser.MailParser = None,
    ) -> Dict[str, Any]:
        """Konvertuje email na markdown a uloží do projektu (non-blocking)."""
        return await asyncio.to_thread(
            self._convert_and_save_sync,
            temp_eml_path,
            email_data,
            project_name,
            project_in_inbox,
            inbox_folder,
            mail_object,
        )
