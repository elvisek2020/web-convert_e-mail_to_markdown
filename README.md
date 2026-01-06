# Convert e-mail to Markdown

Systém pro konverzi emailů z Outlooku (.eml) do Markdown formátu s přílohami a organizací podle projektů.

## 📋 Popis

Aplikace umožňuje jednoduchou konverzi emailů z formátu .eml (Outlook) do strukturovaného Markdown formátu s YAML front-matter. Emaily jsou automaticky organizovány do složek podle názvu projektu, přílohy jsou ukládány do samostatné složky. Aplikace kontroluje duplicity a zabraňuje přepsání existujících souborů.

Aplikace je určena pro uživatele, kteří potřebují systematicky archivovat a organizovat emaily v textovém formátu, vhodném pro verzování a další zpracování.

## ✨ Funkce

- ✅ **Konverze emailů** z .eml formátu do Markdown s YAML front-matter
- ✅ **Správa příloh** včetně inline obrázků - přílohy se ukládají do samostatné složky
- ✅ **Organizace podle projektů** - emaily se ukládají do složek podle názvu projektu
- ✅ **Normalizace názvu projektu** - automatické odstranění diakritiky a speciálních znaků, ponechání jen alfanumerických znaků a podtržítka
- ✅ **Kontrola duplicit** - zabraňuje přepsání existujících souborů se stejným datum_čas
- ✅ **Jednotná aplikace** - frontend a backend v jednom Docker kontejneru
- ✅ **Drag & drop upload** - jednoduché nahrávání souborů přes webové rozhraní
- ✅ **Zobrazení verze** - verze aplikace je zobrazena v patičce

## 📖 Použití

Aplikace poskytuje jednoduché webové rozhraní pro konverzi emailů. Uživatel zadá název projektu a nahraje .eml soubor, který se automaticky zpracuje a uloží do strukturované složky.

### Základní workflow

1. **Zadání názvu projektu**: Uživatel zadá název projektu do textového pole (diakritika a speciální znaky budou automaticky odstraněny)
2. **Nahrání .eml souboru**: Přetáhne .eml soubor do aplikace nebo klikne na upload oblast
3. **Automatické zpracování**: Email se automaticky konvertuje a uloží do složky `output/{normalizovany_nazev_projektu}/`
4. **Pokračování**: Název projektu zůstane zachován, uživatel může nahrát další emaily do stejného projektu

## 🚀 Deployment

### Předpoklady

- Docker a Docker Compose

### Docker Compose

Aplikace je připravena pro spuštění pomocí Docker Compose. Soubor `docker-compose.yml` obsahuje veškerou potřebnou konfiguraci.

#### Spuštění

```bash
docker compose up -d --build
```

Aplikace bude dostupná na `http://localhost:8000`

#### Konfigurace

Aplikace je konfigurována pomocí `docker-compose.yml`:

```yaml
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: convert-mail-to-markdown
    hostname: convert-mail-to-markdown
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      - ./output:/app/output
    environment:
      - ROOT_FOLDER=/app/output
```

#### Update aplikace

```bash
docker compose pull
docker compose up -d
```

#### Rollback na konkrétní verzi

V `docker-compose.yml` změňte image tag:

```yaml
services:
  app:
    image: ghcr.io/elvisek2020/web-convert_e-mail_to_markdown:sha-<commit-sha>
```

### GitHub a CI/CD

#### Inicializace repozitáře

1. **Vytvoření GitHub repozitáře**:

   ```bash
   # Repozitář: git@github.com:elvisek2020/web-convert_e-mail_to_markdown.git
   ```
2. **Inicializace lokálního repozitáře**:

   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin git@github.com:elvisek2020/web-convert_e-mail_to_markdown.git
   git push -u origin main
   ```
3. **Vytvoření GitHub Actions workflow**:

   Vytvořte soubor `.github/workflows/docker.yml` s workflow pro automatické buildy Docker image. Příklad workflow najdete v dokumentaci GitHub Actions nebo v existujících projektech.
4. **Nastavení viditelnosti image**:

   - Po prvním buildu jděte na GitHub → Packages
   - Najděte vytvořený package `web-convert_e-mail_to_Markdown`
   - V Settings → Change visibility nastavte na **Public**

#### Commitování změn a automatické buildy

1. **Proveďte změny v kódu**
2. **Commit a push**:

   ```bash
   git add .
   git commit -m "Popis změn"
   git push origin main
   ```
3. **Automatický build**:

   - Po push do `main` branch se automaticky spustí GitHub Actions workflow
   - Vytvoří se Docker image pro `linux/amd64` a `linux/arm64`
   - Image se nahraje do GHCR
   - Taguje se jako `latest` a `sha-<commit-sha>`
4. **Sledování buildu**:

   - GitHub → Actions → zobrazí se běžící workflow
   - Po dokončení je image dostupná na `ghcr.io/elvisek2020/web-convert_e-mail_to_markdown:latest`

#### GitHub Container Registry (GHCR)

Aplikace je dostupná jako Docker image z GitHub Container Registry:

- **Latest**: `ghcr.io/elvisek2020/web-convert_e-mail_to_markdown:latest`
- **Konkrétní commit**: `ghcr.io/elvisek2020/web-convert_e-mail_to_markdown:sha-<commit-sha>`

Image je **veřejný** (public), takže není potřeba autentizace pro pull.

---

## 🔧 Technická dokumentace

### 🏗️ Architektura

Jednotná aplikace kombinující frontend a backend v jednom Docker kontejneru:

- **Backend (Python FastAPI)**: Zpracování .eml souborů, konverze do Markdown formátu, ukládání do strukturovaných složek
- **Frontend (Vanilla JavaScript ES6+)**: Drag & drop upload, zobrazení průběhu zpracování, zadání názvu projektu
- **Statické soubory**: Vanilla JS frontend je servován FastAPI jako statické soubory

Hlavní charakteristiky:

- **Jednoduchý Docker build**: Statické soubory se kopírují přímo do Python kontejneru (bez build fáze)
- **Volume mapping**: Výstupní složka `./output` je mapována do kontejneru pro perzistenci dat
- **REST API**: FastAPI poskytuje REST endpointy pro konverzi emailů
- **Kontrola duplicit**: Aplikace kontroluje, zda soubor s daným datum_čas již existuje

### Technický stack

**Backend:**

- FastAPI (Python 3.11+)
- Uvicorn jako ASGI server
- mail-parser pro parsování .eml souborů
- markdownify pro konverzi HTML na Markdown
- PyYAML pro YAML front-matter
- Python logging s konfigurovatelnou úrovní

**Frontend:**

- Vanilla JavaScript (ES6+)
- ES6 moduly pro komponenty
- REST API pro komunikaci s backendem
- HTML5 + CSS3
- Drag & drop API

**Deployment:**

- Docker
- Docker Compose
- Jednoduchý single-stage build

### 📁 Struktura projektu

```
convert-email-to-markdown/
├── backend/              # Python FastAPI backend
│   ├── main.py          # Hlavní FastAPI aplikace
│   ├── models/          # Data modely
│   │   └── schemas.py   # Pydantic modely
│   ├── services/        # Business logika
│   │   └── email_processor.py  # Zpracování emailů
│   └── requirements.txt # Python závislosti
├── static/              # Vanilla JS frontend
│   ├── index.html       # Hlavní HTML stránka
│   ├── app.js           # Hlavní JavaScript aplikace
│   ├── components/      # ES6 moduly komponent
│   │   ├── dropzone.js
│   │   ├── processing-status.js
│   │   └── message-banner.js
│   ├── styles/          # CSS soubory
│   │   ├── main.css
│   │   ├── dropzone.css
│   │   ├── processing-status.css
│   │   └── message-banner.css
│   └── version.json     # Verze aplikace
├── output/              # Výstupní složka (mapována jako volume)
├── Dockerfile           # Single-stage build pro jednotnou aplikaci
├── docker-compose.yml   # Docker Compose konfigurace
└── README.md            # Tato dokumentace
```

### 📁 Struktura výstupu

```
output/
  {nazev_projektu}/
    {datum_cas}_{slug}.md
    attachments/
      {prilohy}
```

**Formát souboru:**

- `{datum_cas}_{slug}.md` - kde datum_cas je z emailu (formát: YYYY-MM-DD_HH-MM-SS)
- Slug je vytvořen z subject emailu (max 100 znaků, bez diakritiky a speciálních znaků)
- Přílohy se ukládají do složky `attachments/` v rámci projektu

**YAML front-matter obsahuje:**

- `subject`: Předmět emailu
- `from`: Odesílatel
- `to`: Příjemci
- `cc`: Kopie
- `date`: Datum a čas emailu (ISO formát)
- `attachments`: Seznam příloh

### 🔧 API dokumentace

#### REST Endpoints

**GET /health**

- Health check endpoint
- Vrací: `{"status": "ok"}`

**GET /version.json**

- Vrátí verzi aplikace z `version.json`
- Vrací: `{"version": "YYYYMMDD.HHMM"}`

**POST /api/convert-email**

- Konvertuje .eml soubor na Markdown
- **Parametry** (multipart/form-data):
  - `file`: .eml soubor (povinný)
  - `project_name`: Název projektu (povinný)
- **Úspěšná odpověď** (200):
  ```json
  {
    "status": "success",
    "project_name": "název-projektu",
    "filename": "2026-01-06_14-17-30_subject-slug.md",
    "path": "/app/output/název-projektu/2026-01-06_14-17-30_subject-slug.md"
  }
  ```
- **Chyby**:
  - `400`: Neplatný soubor nebo chybějící název projektu
  - `409`: Soubor s daným datum_čas již existuje
  - `500`: Interní chyba serveru

**GET /**

- Servuje aplikaci (index.html)

**GET /{full_path:path}**

- Catch-all route - servuje index.html pro všechny non-API routes

### 💻 Vývoj

#### Přidání nových funkcí

1. **Backend změny**:

   - Hlavní aplikace: `backend/main.py`
   - Business logika: `backend/services/email_processor.py`
   - Data modely: `backend/models/schemas.py`
2. **Frontend změny**:

   - UI logika: `static/app.js`
   - Komponenty: `static/components/` (ES6 moduly)
   - Styly: `static/styles/` (používejte box-style komponenty)

#### Testování

- **Lokální testování**: Spusťte aplikaci pomocí `docker compose up -d --build` a otestujte všechny funkce
- **Testování REST API**: Použijte nástroje jako Postman nebo curl pro testování REST endpointů
- **Testování frontendu**: Otevřete `http://localhost:8000` a otestujte drag & drop upload

#### Debugging

- Nastavte `LOG_LEVEL=DEBUG` v `docker-compose.yml` pro detailní logy (pokud je podporováno)
- Server loguje všechny důležité události
- Frontend loguje chyby do konzole prohlížeče
- Výstupní soubory jsou v `./output/` složce

#### Úroveň logování (`LOG_LEVEL`)

- `DEBUG` - zobrazí všechny logy včetně detailních debug informací (vývoj)
- `INFO` - zobrazí informační logy (výchozí, vhodné pro testování)
- `WARNING` - zobrazí pouze varování a chyby (doporučeno pro produkci)
- `ERROR` - zobrazí pouze chyby (minimální logování)
- `CRITICAL` - zobrazí pouze kritické chyby

Pro produkci doporučujeme nastavit `LOG_LEVEL=WARNING` nebo `LOG_LEVEL=ERROR`.

### 🎨 UI/UX

Aplikace používá **box-style komponenty** pro konzistentní vzhled:

- Všechny komponenty mají boxový vzhled s rámečky
- Konzistentní barvy a rozestupy
- Responzivní design
- Drag & drop upload s vizuálním feedbackem
- Zobrazení průběhu zpracování
- Zobrazení úspěšných/chybných zpráv

### 🐛 Známé problémy

- Aplikace kontroluje duplicity pouze podle datum_čas, ne podle obsahu emailu
- Velké přílohy mohou zpomalit zpracování
- Název projektu je automaticky normalizován (odstranění diakritiky, speciálních znaků, mezery nahrazeny podtržítkem)

### 📚 Další zdroje

- [FastAPI dokumentace](https://fastapi.tiangolo.com/)
- [ES6 moduly](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Modules)
- [Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API)
- [Docker dokumentace](https://docs.docker.com/)
- [GitHub Actions dokumentace](https://docs.github.com/en/actions)
- [mail-parser dokumentace](https://github.com/SpamScope/mail-parser)

## 📄 Licence

Tento projekt je vytvořen pro vzdělávací účely.
