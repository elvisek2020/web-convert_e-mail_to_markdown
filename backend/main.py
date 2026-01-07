from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from pathlib import Path

from services.email_processor import EmailProcessor
from models.schemas import EmailMetadata

app = FastAPI(title="Convert e-mail to Markdown")

# Initialize service
ROOT_FOLDER = os.getenv("ROOT_FOLDER", "/app/output")
email_processor = EmailProcessor(ROOT_FOLDER)

# Mount static files
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/version.json")
async def get_version():
    """Vrátí verzi aplikace"""
    version_path = Path(__file__).parent / "static" / "version.json"
    if version_path.exists():
        import json
        with open(version_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"version": "unknown"}


@app.get("/api/projects")
async def get_projects():
    """Vrátí seznam existujících projektů (složek v output/)"""
    try:
        output_path = Path(ROOT_FOLDER)
        if not output_path.exists():
            return {"projects": []}
        
        # Získat všechny složky v output/ (projekty)
        projects = [
            item.name for item in output_path.iterdir()
            if item.is_dir() and not item.name.startswith('.')
        ]
        
        # Seřadit abecedně
        projects.sort()
        
        return {"projects": projects}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chyba při načítání projektů: {str(e)}")


@app.post("/api/convert-email")
async def convert_email(
    file: UploadFile = File(...),
    project_name: str = Form(...)
):
    """
    Konvertuje .eml soubor na markdown a uloží do projektu.
    """
    if not file.filename.endswith('.eml'):
        raise HTTPException(status_code=400, detail="Soubor musí být .eml")
    
    if not project_name or not project_name.strip():
        raise HTTPException(status_code=400, detail="Název projektu je povinný")
    
    # Normalizovat název projektu (odstranit diakritiku, speciální znaky, ponechat jen alfanumerické a _)
    project_name = email_processor._normalize_project_name(project_name.strip())
    if not project_name:
        raise HTTPException(status_code=400, detail="Neplatný název projektu")
    
    try:
        # Uložit dočasně soubor
        temp_path = await email_processor.save_temp_file(file)
        
        # Zpracovat email
        email_data = await email_processor.parse_email(temp_path)
        
        # Konvertovat a uložit
        result = await email_processor.convert_and_save(
            temp_path,
            email_data,
            project_name
        )
        
        return result
        
    except FileExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """Serve app index.html"""
    index_path = Path(__file__).parent / "static" / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "Convert e-mail to Markdown API"}


@app.get("/{full_path:path}")
async def serve_app(full_path: str):
    """Catch-all route - serve index.html for all non-API routes"""
    # Pokud to není API endpoint, servuj aplikaci
    if not full_path.startswith("api") and not full_path.startswith("static"):
        index_path = Path(__file__).parent / "static" / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
    raise HTTPException(status_code=404, detail="Not found")
