import asyncio
import json
import logging
import os
from datetime import datetime
from functools import lru_cache
from pathlib import Path

import yaml
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from services.email_processor import EmailProcessor

logger = logging.getLogger("app")
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(title="Convert e-mail to Markdown")

ROOT_FOLDER = os.getenv("ROOT_FOLDER", "/app/output")
INBOX_FOLDER = os.getenv("INBOX_FOLDER", "_from_email")
INBOX_SUBFOLDER = "_01_inbox"
email_processor = EmailProcessor(ROOT_FOLDER)


@lru_cache(maxsize=1)
def _load_version() -> dict:
    version_path = Path(__file__).parent / "static" / "version.json"
    if version_path.exists():
        with open(version_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"version": "unknown"}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response


app.add_middleware(SecurityHeadersMiddleware)

static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


def _resolve_project_path(project_name: str) -> Path | None:
    """Safely resolve project path, preventing path traversal."""
    normalized = email_processor._normalize_project_name(project_name)
    if not normalized:
        return None

    output_path = Path(ROOT_FOLDER)
    inbox_path = output_path / INBOX_FOLDER

    if inbox_path.is_dir():
        candidate = inbox_path / normalized
        if candidate.is_dir():
            return candidate

    candidate = output_path / normalized
    if candidate.is_dir():
        return candidate

    return None


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/version.json")
async def get_version():
    return _load_version()


def _list_projects(include_others: bool) -> list[str]:
    output_path = Path(ROOT_FOLDER)
    inbox_path = output_path / INBOX_FOLDER
    projects = []

    if not include_others:
        if inbox_path.exists() and inbox_path.is_dir():
            for item in inbox_path.iterdir():
                if item.is_dir() and not item.name.startswith("."):
                    projects.append(item.name)
    else:
        if not output_path.exists():
            return []
        for item in output_path.iterdir():
            if item.is_dir() and not item.name.startswith(".") and item.name != INBOX_FOLDER:
                projects.append(item.name)

    projects.sort()
    return projects


@app.get("/api/projects")
async def get_projects(include_others: bool = False):
    """
    Vrátí seznam existujících projektů (složek).
    include_others=False -> složky z INBOX_FOLDER.
    include_others=True  -> všechny složky kromě INBOX_FOLDER.
    """
    try:
        projects = await asyncio.to_thread(_list_projects, include_others)
        return {"projects": projects}
    except Exception:
        logger.exception("Chyba při načítání projektů")
        raise HTTPException(status_code=500, detail="Interní chyba serveru")


def _list_emails(project_path: Path, limit: int = 500) -> list[dict]:
    emails = []

    # Seřadit soubory podle názvu sestupně (názvy začínají datem) a omezit počet
    md_files = sorted(project_path.glob("*.md"), key=lambda f: f.name, reverse=True)[:limit]

    for md_file in md_files:
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()

            if not content.startswith("---"):
                continue

            parts = content.split("---", 2)
            if len(parts) < 3:
                continue

            front_matter = yaml.safe_load(parts[1].strip())
            if not front_matter:
                continue

            email_date = _parse_email_date(
                front_matter.get("date", ""), md_file.stem
            )
            email_date_str = front_matter.get("date", "")

            emails.append({
                "filename": md_file.name,
                "date": email_date.isoformat() if email_date else email_date_str,
                "from": front_matter.get("from", ""),
                "subject": front_matter.get("subject", ""),
                "_sort_date": email_date,
            })
        except Exception:
            logger.warning("Chyba při parsování souboru %s", md_file.name, exc_info=True)
            continue

    emails.sort(key=lambda x: x.get("_sort_date") or datetime.min, reverse=True)
    for email in emails:
        email.pop("_sort_date", None)

    return emails


@app.get("/api/projects/{project_name}/emails")
async def get_project_emails(project_name: str):
    """Vrátí seznam emailů (markdown souborů) v projektu."""
    try:
        project_path = _resolve_project_path(project_name)
        if project_path is None:
            raise HTTPException(status_code=404, detail="Projekt neexistuje")

        inbox_sub = project_path / INBOX_SUBFOLDER
        emails_root = inbox_sub if inbox_sub.is_dir() else project_path
        emails = await asyncio.to_thread(_list_emails, emails_root)
        return {"emails": emails}

    except HTTPException:
        raise
    except Exception:
        logger.exception("Chyba při načítání emailů")
        raise HTTPException(status_code=500, detail="Interní chyba serveru")


def _parse_email_date(date_value, file_stem: str) -> datetime | None:
    """Parse date from YAML front-matter with fallback to filename."""
    if isinstance(date_value, datetime):
        return date_value

    date_str = str(date_value) if date_value else ""
    if not date_str:
        return None

    try:
        if "Z" in date_str:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return datetime.fromisoformat(date_str.replace("+00:00", ""))
    except (ValueError, TypeError):
        pass

    try:
        date_part = file_stem.split("_", 1)[0]
        if len(date_part) >= 19:
            return datetime.strptime(date_part, "%Y-%m-%d_%H-%M-%S")
        if len(date_part) >= 10:
            return datetime.strptime(date_part, "%Y-%m-%d")
    except (ValueError, IndexError):
        pass

    return None


@app.post("/api/convert-email")
async def convert_email(
    file: UploadFile = File(...),
    project_name: str = Form(...),
):
    """Konvertuje .eml soubor na markdown a uloží do projektu."""
    if not file.filename or not file.filename.lower().endswith(".eml"):
        raise HTTPException(status_code=400, detail="Soubor musí být .eml")

    if not project_name or not project_name.strip():
        raise HTTPException(status_code=400, detail="Název projektu je povinný")

    project_name = email_processor._normalize_project_name(project_name.strip())
    if not project_name:
        raise HTTPException(status_code=400, detail="Neplatný název projektu")

    temp_path = None
    try:
        output_path = Path(ROOT_FOLDER)
        inbox_path = output_path / INBOX_FOLDER

        project_in_inbox = None

        if inbox_path.is_dir():
            if (inbox_path / project_name).is_dir():
                project_in_inbox = True
                logger.debug("Projekt %s nalezen v %s", project_name, INBOX_FOLDER)

        if project_in_inbox is None:
            if (output_path / project_name).is_dir():
                project_in_inbox = False
                logger.debug("Projekt %s nalezen v root", project_name)
            else:
                project_in_inbox = True
                logger.debug("Projekt %s neexistuje, bude vytvořen v %s", project_name, INBOX_FOLDER)

        temp_path = await email_processor.save_temp_file(file)
        email_data, mail_object = await email_processor.parse_email(temp_path)

        result = await email_processor.convert_and_save(
            temp_path,
            email_data,
            project_name,
            project_in_inbox=project_in_inbox,
            inbox_folder=INBOX_FOLDER,
            mail_object=mail_object,
        )

        return result

    except FileExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=413, detail=str(e))
    except HTTPException:
        raise
    except Exception:
        logger.exception("Chyba při konverzi emailu")
        raise HTTPException(status_code=500, detail="Interní chyba serveru")
    finally:
        if temp_path and temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                logger.warning("Nepodařilo se smazat temp soubor %s", temp_path)


@app.get("/")
async def root():
    index_path = Path(__file__).parent / "static" / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "Convert e-mail to Markdown API"}


@app.get("/{full_path:path}")
async def serve_app(full_path: str):
    if not full_path.startswith("api") and not full_path.startswith("static"):
        index_path = Path(__file__).parent / "static" / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
    raise HTTPException(status_code=404, detail="Not found")
