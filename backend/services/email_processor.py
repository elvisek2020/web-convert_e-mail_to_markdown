import os
import re
import unicodedata
import base64
from pathlib import Path
from typing import Dict, Any
import tempfile
import mailparser
from datetime import datetime
import markdownify
import yaml
from models.schemas import EmailMetadata


class EmailProcessor:
    def __init__(self, root_folder: str):
        self.root_folder = Path(root_folder)
        self.root_folder.mkdir(parents=True, exist_ok=True)
        self.temp_dir = Path(tempfile.gettempdir()) / "transcendence_emails"
        self.temp_dir.mkdir(exist_ok=True)
    
    async def save_temp_file(self, file) -> Path:
        """Uloží uploadovaný soubor dočasně"""
        temp_path = self.temp_dir / file.filename
        
        with open(temp_path, 'wb') as f:
            content = await file.read()
            f.write(content)
        
        return temp_path
    
    async def parse_email(self, eml_path: Path) -> EmailMetadata:
        """Parsuje .eml soubor a vrátí metadata"""
        mail = mailparser.parse_from_file(str(eml_path))
        
        # Extrahovat základní metadata
        from_email = mail.from_[0][1] if mail.from_ else ""
        from_domain = from_email.split('@')[-1] if '@' in from_email else ""
        
        to_emails = [addr[1] for addr in mail.to] if mail.to else []
        cc_emails = [addr[1] for addr in mail.cc] if mail.cc else []
        
        # Parsovat tělo emailu
        body_text = mail.text_plain[0] if mail.text_plain else ""
        body_html = mail.text_html[0] if mail.text_html else ""
        
        # Pokud není plain text, převést z HTML
        if not body_text and body_html:
            body_text = markdownify.markdownify(body_html, heading_style="ATX")
        
        # Extrahovat přílohy
        attachments = []
        if mail.attachments:
            for att in mail.attachments:
                att_data = {
                    "filename": att.get("filename", "unknown"),
                    "content_type": att.get("content_type", "application/octet-stream"),
                    "size": len(att.get("payload", b"")) if att.get("payload") else 0
                }
                attachments.append(att_data)
        
        # Extrahovat inline obrázky (CID)
        inline_images = []
        if mail.attachments:
            for att in mail.attachments:
                if att.get("content_disposition") == "inline":
                    img_data = {
                        "cid": att.get("content_id", ""),
                        "filename": att.get("filename", ""),
                        "content_type": att.get("content_type", "")
                    }
                    inline_images.append(img_data)
        
        return EmailMetadata(
            subject=mail.subject or "",
            from_email=from_email,
            from_domain=from_domain,
            to=to_emails,
            cc=cc_emails,
            date=mail.date if mail.date else datetime.now(),
            body_text=body_text,
            body_html=body_html,
            attachments=attachments,
            inline_images=inline_images
        )
    
    def _normalize_project_name(self, text: str) -> str:
        """Normalizuje název projektu - odstraní diakritiku, speciální znaky, ponechá jen alfanumerické a _"""
        if not text:
            return ""
        
        # Odstranit diakritiku
        text = unicodedata.normalize('NFKD', text)
        text = text.encode('ascii', 'ignore').decode('ascii')
        
        # Nahradit mezery a další oddělovače podtržítkem
        text = re.sub(r'[\s\-\.]+', '_', text)
        
        # Odstranit všechny speciální znaky kromě alfanumerických a podtržítka
        text = re.sub(r'[^a-zA-Z0-9_]', '', text)
        
        # Nahradit více podtržítek jednou
        text = re.sub(r'_+', '_', text)
        
        # Odstranit podtržítka na začátku a konci
        text = text.strip('_')
        
        return text
    
    def _slugify(self, text: str, max_length: int = 100) -> str:
        """Převede text na slug - max 100 znaků, bez diakritiky a speciálních znaků"""
        # Odstranit diakritiku
        text = unicodedata.normalize('NFKD', text)
        text = text.encode('ascii', 'ignore').decode('ascii')
        
        # Převede na lowercase
        text = text.lower()
        
        # Odstranit speciální znaky (ponechat pouze alfanumerické, pomlčky a podtržítka)
        text = re.sub(r'[^a-z0-9_-]', '', text)
        
        # Nahradit více mezer/pomlček jednou pomlčkou
        text = re.sub(r'[-\s]+', '-', text)
        
        # Omezit délku
        text = text[:max_length]
        
        # Odstranit pomlčky na začátku a konci
        return text.strip('-')
    
    async def convert_and_save(
        self,
        temp_eml_path: Path,
        email_data: EmailMetadata,
        project_name: str,
        project_in_inbox: bool = True,
        inbox_folder: str = None
    ) -> Dict[str, Any]:
        """
        Konvertuje email na markdown a uloží do projektu.
        Vrací dict s výsledkem nebo vyhodí výjimku pokud soubor existuje.
        
        Args:
            project_in_inbox: Pokud True, ukládat do inbox_folder/project_name. 
                              Pokud None/True (výchozí), vytvoří nový projekt v INBOX_FOLDER.
            inbox_folder: Název inbox adresáře (např. "_from_email")
        """
        # Vytvořit cestu k projektu
        # Výchozí je INBOX_FOLDER pro nové projekty
        if project_in_inbox and inbox_folder:
            project_path = self.root_folder / inbox_folder / project_name
        else:
            project_path = self.root_folder / project_name
        
        attachments_path = project_path / "attachments"
        
        project_path.mkdir(parents=True, exist_ok=True)
        attachments_path.mkdir(parents=True, exist_ok=True)
        
        # Vytvořit slug z subject
        slug = self._slugify(email_data.subject)
        
        # Vytvořit datum_čas z emailu (formát: YYYY-MM-DD_HH-MM-SS)
        date_str = email_data.date.strftime('%Y-%m-%d_%H-%M-%S')
        
        # Vytvořit název souboru
        md_filename = f"{date_str}_{slug}.md"
        md_path = project_path / md_filename
        
        # Kontrola duplicit - pokud soubor existuje, vyhodit chybu
        if md_path.exists():
            raise FileExistsError(f"Soubor {md_filename} již existuje v projektu {project_name}")
        
        # Načíst přílohy z .eml souboru
        attachment_payloads = {}
        inline_image_payloads = {}
        
        if temp_eml_path.exists():
            mail = mailparser.parse_from_file(str(temp_eml_path))
            if mail.attachments:
                for att in mail.attachments:
                    filename = att.get("filename", "unknown")
                    payload = att.get("payload")
                    if payload:
                        # Zajistit, že payload je bytes
                        if isinstance(payload, str):
                            # Mailparser může vracet base64 encoded string
                            # Zkusit dekódovat jako base64
                            try:
                                # Odstranit případné whitespace
                                payload_clean = payload.strip()
                                payload = base64.b64decode(payload_clean)
                            except Exception:
                                # Pokud to není base64, zkusit jako UTF-8
                                try:
                                    payload = payload.encode('utf-8')
                                except Exception:
                                    # Pokud selže, zkusit jako latin-1 (zachová binární data)
                                    try:
                                        payload = payload.encode('latin-1')
                                    except Exception:
                                        # Pokud všechno selže, přeskočit tuto přílohu
                                        continue
                        elif isinstance(payload, bytes):
                            # Už je to bytes, použít přímo
                            pass
                        else:
                            # Pokud je to něco jiného (list, dict, atd.), zkusit převést
                            try:
                                if isinstance(payload, list):
                                    # Pokud je to list bytů, spojit je
                                    payload = b''.join(bytes([b]) if isinstance(b, int) else b for b in payload)
                                else:
                                    payload = bytes(payload)
                            except Exception:
                                # Pokud selže, přeskočit tuto přílohu
                                continue
                        
                        # Uložit payload podle typu přílohy
                        if att.get("content_disposition") == "inline":
                            inline_image_payloads[filename] = payload
                        else:
                            attachment_payloads[filename] = payload
        
        # Vytvořit YAML front matter
        front_matter = {
            "subject": email_data.subject,
            "from": email_data.from_email,
            "to": email_data.to,
            "cc": email_data.cc,
            "date": email_data.date.isoformat(),
            "attachments": [att["filename"] for att in email_data.attachments]
        }
        
        # Zapsat markdown soubor
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write("---\n")
            f.write(yaml.dump(front_matter, allow_unicode=True, default_flow_style=False))
            f.write("---\n\n")
            f.write(email_data.body_text)
        
        # Uložit přílohy
        for att in email_data.attachments:
            filename = att["filename"]
            payload = attachment_payloads.get(filename)
            if payload and isinstance(payload, bytes) and len(payload) > 0:
                att_path = attachments_path / filename
                # Zajistit, že soubor má správnou příponu
                with open(att_path, 'wb') as f:
                    f.write(payload)
        
        # Uložit inline obrázky
        for img in email_data.inline_images:
            filename = img["filename"]
            payload = inline_image_payloads.get(filename)
            if payload and isinstance(payload, bytes) and len(payload) > 0:
                img_path = attachments_path / filename
                # Zajistit, že soubor má správnou příponu
                with open(img_path, 'wb') as f:
                    f.write(payload)
        
        # Smazat dočasný .eml soubor
        if temp_eml_path.exists():
            temp_eml_path.unlink()
        
        return {
            "status": "success",
            "project_name": project_name,
            "filename": md_filename,
            "path": str(md_path)
        }
