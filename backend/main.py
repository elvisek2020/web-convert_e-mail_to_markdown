from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from pathlib import Path
import yaml
from datetime import datetime

from services.email_processor import EmailProcessor
from models.schemas import EmailMetadata

app = FastAPI(title="Convert e-mail to Markdown")

# Initialize service
ROOT_FOLDER = os.getenv("ROOT_FOLDER", "/app/output")
INBOX_FOLDER = os.getenv("INBOX_FOLDER", "_from_email")
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
async def get_projects(include_others: bool = False):
    """
    Vrátí seznam existujících projektů (složek).
    Pokud include_others=False, zobrazí jen složky z adresáře INBOX_FOLDER.
    Pokud include_others=True, zobrazí všechny složky kromě INBOX_FOLDER.
    """
    try:
        output_path = Path(ROOT_FOLDER)
        inbox_path = output_path / INBOX_FOLDER
        
        # Debug: logovat cestu
        print(f"[DEBUG] ROOT_FOLDER: {ROOT_FOLDER}")
        print(f"[DEBUG] INBOX_FOLDER: {INBOX_FOLDER}")
        print(f"[DEBUG] output_path exists: {output_path.exists()}")
        print(f"[DEBUG] inbox_path exists: {inbox_path.exists()}")
        print(f"[DEBUG] include_others: {include_others}")
        
        projects = []
        
        if not include_others:
            # Zobrazit jen složky z INBOX_FOLDER adresáře
            if inbox_path.exists() and inbox_path.is_dir():
                all_items = list(inbox_path.iterdir())
                print(f"[DEBUG] All items in {inbox_path}: {[item.name for item in all_items]}")
                
                for item in all_items:
                    if item.is_dir() and not item.name.startswith('.'):
                        projects.append(item.name)
                        print(f"[DEBUG] Found project in {INBOX_FOLDER}: {item.name}")
            else:
                print(f"[DEBUG] {INBOX_FOLDER} directory does not exist")
        else:
            # Zobrazit všechny složky kromě INBOX_FOLDER
            if not output_path.exists():
                print(f"[DEBUG] Path {output_path} does not exist")
                return {"projects": []}
            
            all_items = list(output_path.iterdir())
            print(f"[DEBUG] All items in {output_path}: {[item.name for item in all_items]}")
            
            for item in all_items:
                if item.is_dir() and not item.name.startswith('.') and item.name != INBOX_FOLDER:
                    projects.append(item.name)
                    print(f"[DEBUG] Found project (excluding {INBOX_FOLDER}): {item.name}")
        
        # Seřadit abecedně
        projects.sort()
        
        print(f"[DEBUG] Returning projects: {projects}")
        return {"projects": projects}
    except Exception as e:
        import traceback
        error_detail = f"Chyba při načítání projektů: {str(e)}\n{traceback.format_exc()}"
        print(f"[ERROR] {error_detail}")
        raise HTTPException(status_code=500, detail=error_detail)


@app.get("/api/projects/{project_name}/emails")
async def get_project_emails(project_name: str):
    """Vrátí seznam emailů (markdown souborů) v projektu"""
    try:
        output_path = Path(ROOT_FOLDER)
        inbox_path = output_path / INBOX_FOLDER
        
        # Zkusit najít projekt - nejprve v INBOX_FOLDER, pak v root
        project_path = None
        
        # Zkusit v INBOX_FOLDER adresáři
        if inbox_path.exists() and inbox_path.is_dir():
            potential_path = inbox_path / project_name
            if potential_path.exists() and potential_path.is_dir():
                project_path = potential_path
                print(f"[DEBUG] Found project in {INBOX_FOLDER}: {project_path}")
        
        # Pokud nebyl nalezen v INBOX_FOLDER, zkusit v root
        if project_path is None:
            potential_path = output_path / project_name
            if potential_path.exists() and potential_path.is_dir():
                project_path = potential_path
                print(f"[DEBUG] Found project in root: {project_path}")
        
        if project_path is None:
            raise HTTPException(status_code=404, detail=f"Projekt {project_name} neexistuje")
        
        emails = []
        
        # Načíst všechny .md soubory v projektu (kromě attachments složky)
        for md_file in project_path.glob("*.md"):
            try:
                # Přečíst soubor
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parsovat YAML front-matter
                if content.startswith('---'):
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        yaml_content = parts[1].strip()
                        front_matter = yaml.safe_load(yaml_content)
                        
                        # Extrahovat potřebné informace
                        email_date_str = front_matter.get('date', '')
                        email_date = None
                        if email_date_str:
                            try:
                                # Zkusit ISO formát (s nebo bez timezone)
                                if 'Z' in email_date_str:
                                    email_date = datetime.fromisoformat(email_date_str.replace('Z', '+00:00'))
                                elif '+' in email_date_str or email_date_str.count('-') >= 2:
                                    # ISO formát s timezone nebo bez
                                    email_date = datetime.fromisoformat(email_date_str.replace('+00:00', ''))
                                else:
                                    # Jiný formát - zkusit parsovat
                                    email_date = datetime.fromisoformat(email_date_str)
                            except:
                                # Pokud selže parsing, zkusit extrahovat z názvu souboru
                                try:
                                    filename_parts = md_file.stem.split('_', 1)
                                    if len(filename_parts) >= 1:
                                        date_time_part = filename_parts[0]
                                        # Formát: YYYY-MM-DD_HH-MM-SS
                                        if len(date_time_part) >= 19:
                                            email_date = datetime.strptime(date_time_part, '%Y-%m-%d_%H-%M-%S')
                                        elif len(date_time_part) >= 10:
                                            email_date = datetime.strptime(date_time_part, '%Y-%m-%d')
                                except:
                                    pass
                        
                        emails.append({
                            "filename": md_file.name,
                            "date": email_date.isoformat() if email_date else email_date_str,
                            "from": front_matter.get('from', ''),
                            "subject": front_matter.get('subject', ''),
                            "date_obj": email_date  # Pro řazení
                        })
            except Exception as e:
                print(f"[WARNING] Chyba při parsování souboru {md_file.name}: {str(e)}")
                continue
        
        # Seřadit podle data (nejnovější nahoře)
        emails.sort(key=lambda x: x.get('date_obj') or datetime.min, reverse=True)
        
        # Odstranit date_obj z výsledku (není potřeba v JSON)
        for email in emails:
            email.pop('date_obj', None)
        
        return {"emails": emails}
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"Chyba při načítání emailů: {str(e)}\n{traceback.format_exc()}"
        print(f"[ERROR] {error_detail}")
        raise HTTPException(status_code=500, detail=error_detail)


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
        # Zjistit, jestli projekt existuje v INBOX_FOLDER nebo v root
        output_path = Path(ROOT_FOLDER)
        inbox_path = output_path / INBOX_FOLDER
        
        # Zkontrolovat, jestli projekt existuje v INBOX_FOLDER nebo v root
        project_in_inbox = None  # None = nový projekt, použije se výchozí (INBOX_FOLDER)
        
        # Zkontrolovat, jestli projekt existuje v INBOX_FOLDER
        if inbox_path.exists() and inbox_path.is_dir():
            potential_path = inbox_path / project_name
            if potential_path.exists() and potential_path.is_dir():
                project_in_inbox = True
                print(f"[DEBUG] Project {project_name} found in {INBOX_FOLDER}, will save there")
        
        # Pokud nebyl nalezen v INBOX_FOLDER, zkontrolovat v root
        if project_in_inbox is None:
            potential_path = output_path / project_name
            if potential_path.exists() and potential_path.is_dir():
                project_in_inbox = False
                print(f"[DEBUG] Project {project_name} found in root, will save there")
            else:
                # Projekt neexistuje - vytvořit v INBOX_FOLDER (výchozí)
                project_in_inbox = True
                print(f"[DEBUG] Project {project_name} does not exist, will create in {INBOX_FOLDER} (default)")
        
        # Uložit dočasně soubor
        temp_path = await email_processor.save_temp_file(file)
        
        # Zpracovat email
        email_data = await email_processor.parse_email(temp_path)
        
        # Konvertovat a uložit - předat informaci, jestli ukládat do INBOX_FOLDER
        result = await email_processor.convert_and_save(
            temp_path,
            email_data,
            project_name,
            project_in_inbox=project_in_inbox,
            inbox_folder=INBOX_FOLDER
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
