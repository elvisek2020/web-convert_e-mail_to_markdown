# Convert e-mail to Markdown

Systém pro konverzi emailů z Outlooku (.eml) do Markdown formátu s přílohami a organizací podle projektů.

## Popis

Aplikace umožňuje konverzi emailů z formátu .eml (Outlook) do strukturovaného Markdown formátu s YAML front-matter. Emaily jsou automaticky organizovány do složek podle názvu projektu, přílohy jsou ukládány do samostatné složky. Aplikace kontroluje duplicity a zabraňuje přepsání existujících souborů.

## Funkce

- **Konverze emailů** z .eml formátu do Markdown s YAML front-matter
- **Multi-file upload** -- nahrání více .eml souborů najednou s progress indikátorem
- **Správa příloh** včetně inline obrázků -- přílohy se ukládají do samostatné složky
- **Organizace podle projektů** -- emaily se ukládají do složek podle názvu projektu
- **Seznam existujících projektů** s filtrováním (inbox / ostatní)
- **Seznam emailů** v projektu s datem, odesílatelem a předmětem
- **Normalizace názvu projektu** -- automatické odstranění diakritiky a speciálních znaků
- **Kontrola duplicit** -- zabraňuje přepsání existujících souborů
- **Drag & drop upload** -- jednoduché nahrávání souborů přes webové rozhraní
- **Dark/light mode** s persistencí v localStorage

## Použití

### Základní workflow

1. **Zadání názvu projektu**: Zadejte název projektu do textového pole nebo klikněte na existující projekt ze seznamu
2. **Nahrání .eml souborů**: Přetáhněte jeden nebo více .eml souborů do aplikace, nebo klikněte pro výběr
3. **Automatické zpracování**: Emaily se sekvenčně zpracují s progress indikátorem (2/5), duplikáty se přeskočí
4. **Souhrnná zpráva**: Po dokončení se zobrazí souhrn (počet uložených, přeskočených, chybných)

## Deployment

### Předpoklady

- Docker a Docker Compose

### Spuštění

```bash
docker compose up -d --build
```

Aplikace bude dostupná na `http://localhost:8000`

### Konfigurace

```yaml
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: convert-mail-to-markdown
    hostname: convert-mail-to-markdown
    ports:
      - "8000:8000"
    volumes:
      - ./output:/app/output
    environment:
      - ROOT_FOLDER=/app/output
      - INBOX_FOLDER=_from_email
      - LOG_LEVEL=INFO
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 5s
      start_period: 10s
      retries: 3
```

### Proměnné prostředí

| Proměnná | Výchozí | Popis |
|----------|---------|-------|
| `ROOT_FOLDER` | `/app/output` | Kořenová složka pro výstupní data |
| `INBOX_FOLDER` | `_from_email` | Podsložka pro nové projekty |
| `LOG_LEVEL` | `INFO` | Úroveň logování (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`) |

### Update aplikace

```bash
docker compose pull
docker compose up -d
```

### Rollback na konkrétní verzi

V `docker-compose.yml` změňte image tag:

```yaml
services:
  app:
    image: ghcr.io/elvisek2020/web-convert_e-mail_to_markdown:sha-<commit-sha>
```

### GitHub a CI/CD

Po push do `main` branch se automaticky spustí GitHub Actions workflow:

- Vytvoří Docker image pro `linux/amd64` a `linux/arm64`
- Image se nahraje do GHCR jako `ghcr.io/elvisek2020/web-convert_e-mail_to_markdown`
- Taguje se jako `latest` a `sha-<commit-sha>`

---

## Technická dokumentace

### Architektura

Jednotná aplikace kombinující frontend a backend v jednom Docker kontejneru:

- **Backend (Python FastAPI)**: Zpracování .eml souborů, konverze do Markdown, ukládání do strukturovaných složek
- **Frontend (Vanilla JavaScript ES6+)**: Multi-file drag & drop upload, progress indikátor, správa projektů
- **Statické soubory**: Servovány přímo FastAPI

Hlavní charakteristiky:

- **Non-blocking I/O**: Blokující operace (parsování emailů, zápis na disk) běží v thread poolu přes `asyncio.to_thread()`
- **Bezpečnostní middleware**: Security headers (X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy)
- **Path traversal ochrana**: Všechny uživatelské vstupy pro cesty jsou normalizovány
- **Sanitizace názvů příloh**: Nebezpečné znaky v názvech souborů jsou odstraněny
- **Non-root Docker**: Kontejner běží pod neprivilegovaným uživatelem `appuser`
- **Healthcheck**: Docker i docker-compose monitorují zdraví aplikace

### Technický stack

**Backend:**

- Python 3.11, FastAPI, Uvicorn (ASGI server)
- mail-parser pro parsování .eml souborů
- markdownify pro konverzi HTML na Markdown
- PyYAML pro YAML front-matter
- Pydantic pro validaci dat
- Python logging s konfigurovatelnou úrovní

**Frontend:**

- Vanilla JavaScript (ES6+ moduly)
- HTML5 Drag & Drop API (multi-file)
- Fetch API pro komunikaci s backendem
- CSS3 s CSS proměnnými (dark/light mode)

**Deployment:**

- Docker (single-stage build, non-root user)
- Docker Compose s healthcheck
- GitHub Actions CI/CD (multi-arch: amd64 + arm64)

### Struktura projektu

```
convert-email-to-markdown/
├── backend/                    # Python FastAPI backend
│   ├── main.py                # Hlavní FastAPI aplikace + middleware
│   ├── models/
│   │   └── schemas.py         # Pydantic modely
│   ├── services/
│   │   └── email_processor.py # Zpracování emailů
│   └── requirements.txt       # Python závislosti
├── static/                    # Vanilla JS frontend
│   ├── index.html             # Hlavní HTML stránka
│   ├── app.js                 # Hlavní JavaScript aplikace
│   ├── components/            # ES6 moduly komponent
│   │   ├── dropzone.js        # Drag & drop (multi-file)
│   │   ├── processing-status.js # Progress indikátor
│   │   ├── message-banner.js  # Zprávy (úspěch/chyba)
│   │   ├── project-list.js    # Seznam projektů
│   │   ├── email-list.js      # Seznam emailů v projektu
│   │   └── theme-toggle.js    # Dark/light mode
│   ├── styles/                # CSS soubory
│   │   ├── main.css
│   │   ├── dropzone.css
│   │   ├── processing-status.css
│   │   ├── message-banner.css
│   │   ├── project-list.css
│   │   └── email-list.css
│   └── version.json           # Verze aplikace
├── output/                    # Výstupní složka (Docker volume)
├── .github/workflows/
│   └── docker.yml             # CI/CD workflow
├── Dockerfile                 # Single-stage build, non-root user
├── docker-compose.yml         # Docker Compose konfigurace
└── README.md
```

### Struktura výstupu

```
output/
  _from_email/                 # Inbox složka (výchozí pro nové projekty)
    {nazev_projektu}/
      {datum_cas}_{slug}.md
      attachments/
        {prilohy}
  {nazev_projektu}/            # Projekty přesunuté z inboxu
    ...
```

**Formát souboru:**

- `{datum_cas}_{slug}.md` -- datum_cas z emailu (formát: YYYY-MM-DD_HH-MM-SS), slug z předmětu (max 100 znaků)
- Přílohy se ukládají do složky `attachments/` v rámci projektu

**YAML front-matter obsahuje:**

- `subject`: Předmět emailu
- `from`: Odesílatel
- `to`: Příjemci
- `cc`: Kopie
- `date`: Datum a čas emailu (ISO formát)
- `attachments`: Seznam příloh

### API dokumentace

#### GET /health

Health check endpoint. Vrací `{"status": "ok"}`.

#### GET /version.json

Vrátí verzi aplikace (cached). Vrací `{"version": "YYYYMMDD.HHMM"}`.

#### GET /api/projects

Vrátí seznam existujících projektů.

- **Query parametry:**
  - `include_others` (bool, default: `false`) -- `false` = projekty z inbox složky, `true` = všechny ostatní
- **Odpověď:** `{"projects": ["projekt1", "projekt2", ...]}`

#### GET /api/projects/{project_name}/emails

Vrátí seznam emailů (markdown souborů) v projektu, seřazených od nejnovějšího.

- **Odpověď:**
  ```json
  {
    "emails": [
      {
        "filename": "2026-01-06_14-17-30_subject-slug.md",
        "date": "2026-01-06T14:17:30",
        "from": "user@example.com",
        "subject": "Předmět emailu"
      }
    ]
  }
  ```
- **Chyby:** `404` pokud projekt neexistuje

#### POST /api/convert-email

Konvertuje .eml soubor na Markdown.

- **Parametry** (multipart/form-data):
  - `file`: .eml soubor (povinný)
  - `project_name`: Název projektu (povinný)
- **Odpověď (200):**
  ```json
  {
    "status": "success",
    "project_name": "nazev_projektu",
    "filename": "2026-01-06_14-17-30_subject-slug.md",
    "path": "/app/output/_from_email/nazev_projektu/2026-01-06_14-17-30_subject-slug.md"
  }
  ```
- **Chyby:**
  - `400`: Neplatný soubor nebo chybějící název projektu
  - `409`: Soubor s daným datum_čas již existuje (duplikát)
  - `500`: Interní chyba serveru

### Vývoj

#### Přidání nových funkcí

- **Backend**: `backend/main.py` (endpointy), `backend/services/email_processor.py` (logika), `backend/models/schemas.py` (modely)
- **Frontend**: `static/app.js` (hlavní logika), `static/components/` (ES6 moduly), `static/styles/` (CSS)

#### Lokální testování

```bash
docker compose up -d --build
# Otevřete http://localhost:8000
```

#### Debugging

- Nastavte `LOG_LEVEL=DEBUG` v `docker-compose.yml` pro detailní logy
- Frontend loguje chyby do konzole prohlížeče
- Výstupní soubory jsou v `./output/` složce

### Známé problémy

- Kontrola duplicit je pouze podle datum_čas, ne podle obsahu emailu
- Název projektu je automaticky normalizován (diakritika odstraněna, mezery nahrazeny podtržítkem)

## Licence

Tento projekt je vytvořen pro vzdělávací účely.
