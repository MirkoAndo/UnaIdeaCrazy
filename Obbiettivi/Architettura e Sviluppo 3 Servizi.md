# 🦅 UNAIDEACRAZY · OCCHIO DI FALCO — Struttura Teorica Attuale & Architettura Futura dei 3 Servizi

Questo documento definisce in modo completo:
1. **La struttura teorica e tecnica dell'attuale progetto** (stack portabile, orchestratore desktop Python a 4 tab, listener HTTP/JSON su porta `5050`, script batch e landing page PHP/CSS).
2. **La struttura futura e la progettazione dettagliata dei 3 servizi web** ospitati in `OcchioDiFalcoWebServer/`:
   - **Servizio #1**: `Server Health Checker` (`/occhio-di-falco/`)
   - **Servizio #2**: `My Cloud · File Server` (`/my-cloud/`)
   - **Servizio #3**: `Discovery Server · Web Server Provider` (`/discovery-server/`)

---

# PARTE 1 — STRUTTURA TEORICA DELL'ATTUALE PROGETTO

## 1.1 Visione d'Insieme dell'Ecosistema Ibrido

Il progetto **UnaIdeaCrazy – OcchioDiFalco** non è un semplice sito web statico, ma una **piattaforma locale ibrida Desktop + Web** che gira interamente in modalità portabile su Windows (`127.0.0.1`), senza dipendere da Internet o da installazioni di sistema.

L'architettura si fonda su **due ambienti cooperanti**:
1. **Ambiente Desktop & Orchestrazione (`main.pyw` + pacchetto `occhio_di_falco/`)**:
   - Interagisce a basso livello con il sistema operativo Windows tramite **WMI (`Win32_Process`, `Win32_Processor`, `Win32_OperatingSystem`)**, **Win32 API (`kernel32.GlobalMemoryStatusEx`)**, **Socket TCP** e **Script Batch (`CmdCommands/*.bat`)**.
   - Espone un **Listener HTTP/JSON locale (`127.0.0.1:5050`)** che funge da ponte (bridge) in tempo reale verso l'applicazione web.
2. **Ambiente Web Server & Portale Servizi (`Apache 2.4` + `PHP 8.5 DSO` + `MySQL 26.10.0`)**:
   - Apache serve la `DocumentRoot` (`OcchioDiFalcoWebServer/`), eseguendo PHP come modulo nativo in-process (`php8apache2_4.dll`).
   - La **Landing Page (`index.php` + `style-root/landing.css`)** verifica istantaneamente lo stato dello stack e smista l'utente verso i **3 servizi web** (`/occhio-di-falco/`, `/my-cloud/`, `/discovery-server/`) e verso `/phpmyadmin/`.

```text
                       ┌───────────────────────────────────────────┐
                       │              SISTEMA WINDOWS              │
                       │     WMI · Win32 API · Filesystem · TCP    │
                       └─────────────────────┬─────────────────────┘
                                             │
                 ┌───────────────────────────┴───────────────────────────┐
                 ▼                                                       ▼
┌─────────────────────────────────────────┐             ┌─────────────────────────────────────────┐
│      AMBIENTE PYTHON (main.pyw)         │             │    STACK WEB PORTABILE (127.0.0.1)      │
│  Pacchetto modulare: occhio_di_falco/   │             │  Servizi_UnaIdeaCrazy/                  │
├─────────────────────────────────────────┤             ├─────────────────────────────────────────┤
│  • Tab 1: Panoramica & WMI Processi     │  Controllo  │  • Apache 2.4 (httpd.exe :80)           │
│  • Tab 2: Console Comandi & Script .bat ├────────────►│  • PHP 8.5.12 TS (php8apache2_4.dll)    │
│  • Tab 3: Scanner Socket & Albero Stack │  (.bat/WMI) │  • MySQL 26.10.0 (mysqld.exe :3306)     │
│  • Tab 4: HTTP API Listener (:5050)     │             └────────────────────┬────────────────────┘
└────────────────────┬────────────────────┘                                  │
                     │                                                       ▼
                     │     Bridge HTTP / JSON (127.0.0.1:5050)     ┌─────────────────────────────────────────┐
                     │◄───────────────────────────────────────────►│         OcchioDiFalcoWebServer/         │
                     │     GET /api/health, /services, /ports      │       Landing Page (index.php)          │
                     │     POST /api/command                       └─────────────────┬───────────────────────┘
                                                                                     │
                                                       ┌─────────────────────────────┼─────────────────────────────┐
                                                       ▼                             ▼                             ▼
                                          ┌─────────────────────────┐   ┌─────────────────────────┐   ┌─────────────────────────┐
                                          │      SERVIZIO #1        │   │      SERVIZIO #2        │   │      SERVIZIO #3        │
                                          │    /occhio-di-falco/    │   │       /my-cloud/        │   │   /discovery-server/    │
                                          │  Server Health Checker  │   │  My Cloud File Server   │   │   Web Server Provider   │
                                          └─────────────────────────┘   └─────────────────────────┘   └─────────────────────────┘
```

---

## 1.2 Analisi Teorica dei Componenti Attuali

### A. Lo Stack Portabile (`Servizi_UnaIdeaCrazy/`)

Tutti i demoni risiedono fuori dalle directory di sistema di Windows, in una cartella parallela al repository (`../Servizi_UnaIdeaCrazy`):

| Componente | Binario / Modulo | Porta / Interfaccia | Ruolo Teorico nell'Architettura |
|---|---|---|---|
| **Apache 2.4** | `Apache24/bin/httpd.exe` | `127.0.0.1:80` | Web Server HTTP locale. Legge `conf/httpd.conf` che include `conf/env.conf` per risolvere dinamicamente `SRVROOT`, `DOCUMENT_ROOT` e `PHP_DIR`. |
| **PHP 8.5.12 TS** | `php8apache2_4.dll` | In-process (DSO) | Interprete PHP Thread Safe caricato direttamente nello spazio di memoria di Apache tramite `LoadModule php_module`, garantendo prestazioni elevate senza overhead CGI. |
| **MySQL 26.10.0** | `mysql-26.10.0/bin/mysqld.exe` | `127.0.0.1:3306` | RDBMS relazionale configurato tramite `my.ini`, utilizzato per persistere i metadati del Cloud, i token di condivisione e il registro eventi di OcchioDiFalco. |
| **phpMyAdmin** | `OcchioDiFalcoWebServer/phpmyadmin/` | `http://127.0.0.1/phpmyadmin/` | Interfaccia web di amministrazione diretta del database MySQL. |

---

### B. L'Orchestratore Desktop Python (`main.pyw` e `occhio_di_falco/`)

L'applicazione Python è stata ingegnerizzata con un'architettura modulare all'interno del pacchetto `occhio_di_falco/`, avviata da `main.pyw` (estensione `.pyw` per l'esecuzione GUI nativa su Windows senza console CMD secondaria):

1. **`occhio_di_falco/config.py` (Configurazione & Parser Reale)**:
   - Centralizza i percorsi (`BASE_DIR`, `CMD_COMMANDS_DIR`, `WEB_SERVER_DIR`, `OBBIETTIVI_DIR`), la configurazione dell'API listener (`DEFAULT_API_HOST = "127.0.0.1"`, `DEFAULT_API_PORT = 5050`), i dizionari `SERVICE_POSITIONS` e `CUSTOM_COMMANDS`.
   - Include `read_real_service_configs()`, che effettua il parsing reale dei file `Apache24/conf/env.conf` e `mysql-26.10.0/my.ini` sul disco per estrarre le porte e le directory effettivamente configurate.
2. **`occhio_di_falco/services.py` (Process Management & Batch Runner)**:
   - `get_process_status(process_name)` interroga WMI (`Win32_Process`) in modo thread-safe (con inizializzazione `pythoncom.CoInitialize()` e rilascio esplicito dei puntatori COM prima di `CoUninitialize()`), ed esegue un fallback automatico su `tasklist /FO CSV` in caso di contesa WMI.
   - `execute_batch_command()` esegue gli script in `CmdCommands/` iniettando la posizione assoluta del servizio sia come parametro posizionale `%1` sia tramite le variabili d'ambiente `SERVICE_POSITION` e `SERVICE_NAME`.
   - `format_occhio_di_falco_table()` formatta la vista tabellare ASCII di stato e telemetria.
3. **`occhio_di_falco/monitoring.py` (Telemetria Hardware & Socket Scanner)**:
   - `get_system_metrics()` legge istantaneamente la RAM fisica tramite chiamata diretta alla struct C `MEMORYSTATUSEX` di `kernel32.dll` (`GlobalMemoryStatusEx`) e interroga `Win32_Processor.LoadPercentage` e `Win32_OperatingSystem` per CPU % e nome OS.
   - `check_local_port(host, port)` apre un socket TCP non bloccante (`connect_ex`) misurando con `time.perf_counter()` la latenza esatta in millisecondi sulle porte `80`, `443`, `3306` e `5050`.
4. **`occhio_di_falco/styles.py` (Design System Dark/Slate)**:
   - Definisce la classe `ThemeColors` (identica alla palette CSS di `landing.css`) e configura il tema `clam` di `ttk.Style` per tutti i componenti della GUI.
5. **Le 4 Schede Modulari (`tab_overview.py`, `tab_commands.py`, `tab_monitor.py`, `tab_requests.py`) coordinate da `app.py` (`OcchioDiFalcoGUI`)**:
   - **Tab 1 (`OverviewTab`)**: Card di controllo rapido per Apache, MySQL e Risorse Hardware (barre CPU/RAM), tabella `services_status` con filtro live e ispettore ASCII.
   - **Tab 2 (`CommandsTab`)**: Console interattiva sostitutiva di `input()`, catalogo `CUSTOM_COMMANDS` filtrabile per servizio e ispettore del codice sorgente dei file `.bat`.
   - **Tab 3 (`MonitorTab`)**: Scanner live delle porte TCP (`80`, `443`, `3306`, `5050` + test porta custom) ed esploratore ad albero della gerarchia file con confronto rispetto a XAMPP e visualizzatore integrato dei file `.conf`/`.ini`.
   - **Tab 4 (`RequestsTab`)**: Server HTTP multi-thread (`ReusableThreadingHTTPServer` su `127.0.0.1:5050`) che ascolta le richieste dei client web (come `/occhio-di-falco/`), registra ogni transazione in una tabella live, mostra lo **script di risposta** (Payload JSON, Script Python Handler e Script Client PHP/JS) e include una **Console Live di Ascolto e Risposta**.
   - **Sincronizzazione Thread-Safe (`queue.Queue`)**: Tutte le comunicazioni dai thread secondari (WMI, scanner socket, script batch, server HTTP `:5050`) verso i widget Tkinter avvengono tramite code thread-safe (`_app_ui_queue` e `_ui_queue`) svuotate nel main thread, evitando qualsiasi race condition.

---

### C. Il Portale Web & Landing Page (`OcchioDiFalcoWebServer/index.php` + `style-root/landing.css`)

La landing page principale svolge il ruolo di **Service Gateway**:
- **Separazione tra Logica/Struttura e Stile**:
  - `OcchioDiFalcoWebServer/index.php` contiene la logica PHP di rilevamento rapido e il markup semantico HTML5.
  - `OcchioDiFalcoWebServer/style-root/landing.css` gestisce il layout responsive CSS Grid a 3 colonne, le variabili cromatiche (`--bg-main`, `--bg-card`, `--accent-blue`, `--accent-green`, `--accent-purple`) e le micro-interazioni.
- **Diagnostica Istantanea in PHP**:
  - Verifica se MySQL risponde sulla porta `127.0.0.1:3306` tramite `checkTcpPort()` (`@fsockopen` con timeout di `0.15s` per non rallentare mai il caricamento).
  - Rileva `gethostname()`, IP/Porta, versione PHP/SAPI, sistema operativo host e timestamp del server.
  - Controlla tramite `is_dir()` l'esistenza fisica delle sottocartelle `occhio-di-falco/`, `my-cloud/`, `discovery-server/` e `phpmyadmin/`, aggiornando dinamicamente i badge delle 3 card.

---

# PARTE 2 — STRUTTURA FUTURA E SVILUPPO DEI 3 SERVIZI WEB

Le tre sottocartelle dei servizi sono già state predisposte dentro `OcchioDiFalcoWebServer/`. Di seguito è definita l'architettura teorica e implementativa per lo sviluppo completo di ciascun servizio.

```text
OcchioDiFalcoWebServer/
├── index.php                       # Landing Page (Gateway ai 3 servizi)
├── style-root/
│   └── landing.css                 # Stile globale coordinato Dark/Slate
├── occhio-di-falco/                # [SERVIZIO #1] Server Health Checker
├── my-cloud/                       # [SERVIZIO #2] My Cloud · File Server
└── discovery-server/               # [SERVIZIO #3] Discovery Server · Web Server Provider
```

---

## 2.1 SERVIZIO #1 — Server Health Checker (`/occhio-di-falco/`)

### Obiettivo Funzionale
Fornire una dashboard web interattiva che mostri lo stato di salute della macchina ospitante in tempo reale (CPU, RAM, Spazio Disco, Rete, Stato e PID dei processi Apache, MySQL e Python), permetta l'avvio/arresto manuale dei singoli servizi e visualizzi il registro storico degli eventi (`INFO`, `WARNING`, `CRITICAL`) con sistema di notifiche popup in coda.

### Architettura di Comunicazione (Web Client ↔ Python Listener `:5050` ↔ MySQL `:3306`)

Il Server Health Checker sfrutta direttamente il **Listener HTTP della Tab 4** (`http://127.0.0.1:5050`) già attivo in `occhio_di_falco/tab_requests.py`, con un **meccanismo di fallback in PHP** qualora l'applicazione desktop `main.pyw` sia chiusa:

```text
┌─────────────────────────────────────────────────────────────────────────┐
│               BROWSER: http://127.0.0.1/occhio-di-falco/                │
│         Polling asincrono JS fetch() ogni ~3s + Controlli UI            │
└───────────────────┬─────────────────────────────────┬───────────────────┘
                    │                                 │
      1. Richiesta Telemetria / Azione       2. Lettura / Scrittura Event Log
                    ▼                                 ▼
┌───────────────────────────────────────┐ ┌───────────────────────────────┐
│  OcchioDiFalco Python Listener (:5050)│ │   PHP Backend (api_health.php)│
│  • GET  /api/health                   │ │   • Fallback PHP se :5050     │
│  • GET  /api/services                 │ │     è offline (disk_free_space│
│  • GET  /api/ports                    │ │     + checkTcpPort + tasklist)│
│  • POST /api/command?cmd=...          │ │   • Query MySQL tabella events│
└───────────────────┬───────────────────┘ └───────────────┬───────────────┘
                    │                                     │
                    ▼                                     ▼
         [ WMI / Win32 / .bat ]                [ MySQL :3306 (events) ]
          (Visibile in Tab 4!)
```

1. **Modalità Primaria (Python Listener Online su `:5050`)**:
   - La pagina `/occhio-di-falco/` interroga `http://127.0.0.1:5050/api/health`.
   - Nella **Tab 4 di OcchioDiFalco GUI** vengono visualizzati in diretta la richiesta ricevuta dal client, il payload JSON inviato e la riga di log nella console.
   - Il JSON restituisce: `cpu_percent`, `ram_used_mb`, `ram_total_mb`, `ram_percent`, `disk_used_gb`, `disk_total_gb`, `disk_free_gb`, `disk_percent`, lo stato e i PID di `occhio_di_falco`, `APACHE`, `MYSQL`, `PHP` e la latenza delle porte `80`, `443`, `3306`, `5050`.
2. **Modalità Fallback (Python Listener Offline)**:
   - Se `127.0.0.1:5050` non risponde, `api_health.php` segnala `OcchioDiFalco Python Listener: OFFLINE` (generando un alert `CRITICAL`), ma continua a fornire i dati rilevabili direttamente da PHP (`disk_total_space`, `disk_free_space`, stato socket `3306` di MySQL, stato `ONLINE` di Apache/PHP).

### Struttura Futura dei File in `OcchioDiFalcoWebServer/occhio-di-falco/`

```text
OcchioDiFalcoWebServer/occhio-di-falco/
├── index.php               # Dashboard principale Server Health Checker
├── api_health.php          # Proxy/Fallback PHP verso 127.0.0.1:5050 e lettura Event Log MySQL
├── style/
│   └── health.css          # Stili specifici per gauge CPU/RAM/Disco, tabella servizi e popup alert
└── js/
    └── health.js           # Polling ogni 3s, aggiornamento DOM barre/badge e coda Popup (1 evento alla volta)
```

### Schema Database MySQL per il Registro Eventi (`events`)

```sql
CREATE DATABASE IF NOT EXISTS unaideacrazy_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE unaideacrazy_db;

CREATE TABLE IF NOT EXISTS events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    event_level ENUM('INFO', 'WARNING', 'CRITICAL') NOT NULL,
    event_type VARCHAR(64) NOT NULL,          -- es. 'MYSQL_OFFLINE', 'CPU_HIGH', 'APACHE_ONLINE'
    message VARCHAR(255) NOT NULL,            -- es. 'CPU USAGE > 90% (94.2%)'
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_created_at (created_at),
    INDEX idx_level (event_level)
);
```

---

## 2.2 SERVIZIO #2 — My Cloud · File Server (`/my-cloud/`)

### Obiettivo Funzionale
Fornire uno spazio di archiviazione cloud personale e file server locale (accessibile via browser) che permetta di:
- Navigare in una gerarchia di cartelle e sottocartelle a profondità arbitraria tramite breadcrumb (`HOME / Documenti / Scuola / ...`).
- Creare nuove cartelle ed eliminare file o intere cartelle.
- Caricare file (`Upload`) mantenendo il **nome originale sanitizzato** sul filesystem.
- Scaricare file (`Download`) passando **esclusivamente attraverso un controller PHP di sicurezza** (mai esponendo i file con link diretti Apache).
- Generare **link temporanei di condivisione** con durata selezionabile dall'utente (es. `1 ora`, `6 ore`, `24 ore`, `7 giorni`), riutilizzabili fino alla scadenza.

### Architettura Dual-Layer (Filesystem Fisico + Database Metadati)

```text
                        ┌───────────────────────────────┐
                        │   /my-cloud/ (Controller PHP) │
                        └───────────────┬───────────────┘
                                        │
                 ┌──────────────────────┴──────────────────────┐
                 ▼                                             ▼
┌─────────────────────────────────────────┐   ┌─────────────────────────────────────────┐
│           FILESYSTEM LOCALE             │   │         DATABASE MYSQL (:3306)          │
│  OcchioDiFalcoWebServer/my-cloud/       │   │  • Tabella `folders` (gerarchia)        │
│  └── storage/ (protetto da .htaccess)   │   │  • Tabella `files` (metadati & path)    │
│      ├── Documenti/                     │   │  • Tabella `share_tokens` (token & exp) │
│      ├── Immagini/                      │   └─────────────────────────────────────────┘
│      └── Progetti/                      │
└─────────────────────────────────────────┘
```

### Meccanismi di Sicurezza del File Server
1. **Protezione Accesso Diretto (`storage/.htaccess`)**:
   - Dentro `my-cloud/storage/` viene inserito un file `.htaccess` con `Require all denied` (o la cartella `storage` viene validata a livello PHP), così nessuno può scaricare `http://127.0.0.1/my-cloud/storage/segreto.pdf` aggirando PHP.
2. **Prevenzione Path Traversal**:
   - Ogni percorso richiesto viene risolto con `realpath()` in PHP e confrontato con il prefisso `realpath($STORAGE_ROOT)`: se il percorso normalizzato esce da `storage/` (es. `../../../../Windows/...`), la richiesta viene bloccata con `HTTP 403 Forbidden`.
3. **Sanitizzazione dei Nomi File**:
   - Rimozione di caratteri pericolosi (`..`, `/`, `\`, `:`, `*`, `?`, `"`, `<`, `>`, `|`, null bytes) preservando il nome leggibile originale (es. `relazione_informatica.pdf`).

### Struttura Futura dei File in `OcchioDiFalcoWebServer/my-cloud/`

```text
OcchioDiFalcoWebServer/my-cloud/
├── index.php               # Interfaccia File Browser (breadcrumb, griglia cartelle/file, modale link)
├── config_db.php           # Connessione PDO/MySQLi e helper di validazione path anti-traversal
├── actions/
│   ├── upload.php          # Ricezione multipart/form-data, validazione, salvataggio FS + insert DB
│   ├── download.php        # Verifica sessione/permessi e streaming binario (readfile) con header MIME
│   ├── create_folder.php   # Creazione directory fisica (mkdir) + registrazione in tabella `folders`
│   ├── delete.php          # Eliminazione sincronizzata file/cartella da DB e filesystem
│   └── create_share.php    # Generazione token crittografico (random_bytes) con data di scadenza
├── share.php               # Endpoint pubblico per il download tramite link temporaneo (?token=...)
├── storage/                # Radice fisica dei file caricati (protetta da accesso diretto)
├── style/
│   └── cloud.css           # Stile file manager coordinato con il tema Dark/Slate
└── js/
    └── cloud.js            # Gestione drag & drop upload, modali creazione cartella e copia link
```

### Schema Database MySQL per My Cloud (`folders`, `files`, `share_tokens`)

```sql
CREATE TABLE IF NOT EXISTS folders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    parent_id INT NULL DEFAULT NULL,
    relative_path VARCHAR(1024) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES folders(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS files (
    id INT AUTO_INCREMENT PRIMARY KEY,
    folder_id INT NULL DEFAULT NULL,
    original_name VARCHAR(255) NOT NULL,
    relative_path VARCHAR(1024) NOT NULL,
    file_size BIGINT UNSIGNED NOT NULL DEFAULT 0,
    mime_type VARCHAR(128) NOT NULL DEFAULT 'application/octet-stream',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (folder_id) REFERENCES folders(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS share_tokens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    file_id INT NOT NULL,
    token VARCHAR(64) NOT NULL UNIQUE,
    expires_at DATETIME NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
    INDEX idx_token (token),
    INDEX idx_expires (expires_at)
);
```

---

## 2.3 SERVIZIO #3 — Discovery Server · Web Server Provider (`/discovery-server/`)

### Obiettivo Funzionale
Trasformare `/discovery-server/` in un **Web Server Provider e Catalogo Automatico di Siti Web**: qualsiasi sito o progetto web (HTML/CSS/JS o PHP) copiato all'interno della cartella dedicata viene **rilevato automaticamente**, analizzato nei suoi metadati e presentato in una dashboard da cui è possibile aprirlo, ispezionarne la struttura o testarlo con un solo click.

### Architettura del Motore di Auto-Discovery

```text
           ┌────────────────────────────────────────────────────────┐
           │      OcchioDiFalcoWebServer/discovery-server/          │
           │                     index.php                          │
           └───────────────────────────┬────────────────────────────┘
                                       │
                        Scansione automatica directory
                         (DirectoryIterator / scandir)
                                       │
                                       ▼
           ┌────────────────────────────────────────────────────────┐
           │       Cartella Progetti Ospitati (es. sites/ o ./)     │
           ├──────────────────┬──────────────────┬──────────────────┤
           ▼                  ▼                  ▼                  ▼
   ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐
   │  Sito-Alpha/  │  │ Portfolio-5C/ │  │  Game-JS-2D/  │  │  App-Scuola/  │
   │  • index.php  │  │  • index.html │  │  • index.html │  │  • site.json  │
   │  • style.css  │  │  • assets/    │  │  • game.js    │  │  • index.php  │
   └───────────────┘  └───────────────┘  └───────────────┘  └───────────────┘
```

### Logica di Scansione e Classificazione Automatica di Ogni Sito

Per ogni sottocartella trovata (escludendo le cartelle di servizio interne come `style/`, `js/`, `assets/`), il motore PHP di **Discovery Server** esegue automaticamente:

1. **Rilevamento Entrypoint & Stato**:
   - Se contiene `index.php` → classificato come **`PHP Web App`** (Stato: **Pronto / Avviabile**).
   - Se contiene `index.html` o `index.htm` → classificato come **`Static HTML5 Site`** (Stato: **Pronto / Avviabile**).
   - Se non contiene né `index.php` né `index.html` → classificato come **`Directory / Work in Progress`** (mostra l'elenco dei file presenti o avvisa dell'assenza dell'entrypoint).
2. **Estrazione Automatica dei Metadati del Sito**:
   - **Opzione A (`site.json` opzionale)**: se nella cartella del sito è presente un piccolo file `site.json` (`{"title": "...", "description": "...", "author": "...", "version": "1.0", "tags": ["PHP", "MySQL"]}`), il Discovery Server usa questi dati per arricchire la card.
   - **Opzione B (Zero-Config / Automatica)**: se `site.json` non esiste, il Discovery Server legge automaticamente il tag `<title>...</title>` dall'`index.php`/`index.html` (oppure formatta il nome della cartella), calcola la **data di ultima modifica**, il **numero totale di file** e la **dimensione complessiva in KB/MB**.
3. **Funzionalità dell'Interfaccia Discovery Server**:
   - **Barra di Ricerca e Filtro per Tecnologia**: filtra istantaneamente i siti ospitati per nome o per stack (`Tutti`, `PHP`, `HTML/JS`, `Senza Entrypoint`).
   - **Card del Sito Ospitato**:
     - Titolo del sito, badge tecnologia (`🐘 PHP` / `🌐 HTML5`), percorso relativo, dimensione, numero di file e timestamp ultima modifica.
     - Pulsante **`🚀 Apri Sito`** (apre il sito nel browser) e pulsante **`🔍 Ispeziona File`** (mostra i file principali presenti nella cartella del progetto).

### Struttura Futura dei File in `OcchioDiFalcoWebServer/discovery-server/`

```text
OcchioDiFalcoWebServer/discovery-server/
├── index.php               # Dashboard Discovery Server con catalogo siti, ricerca e filtri
├── scanner.php             # Motore PHP di scansione cartelle, parsing <title>/site.json e calcolo dimensioni
├── style/
│   └── discovery.css       # Stile griglia siti ospitati (con accento Purple coordinato con la Card #3)
├── js/
│   └── discovery.js        # Filtro live istantaneo per nome/tecnologia e modale ispezione struttura sito
└── sites/                  # (Oppure sottocartelle dirette) Contenitore dei siti web caricati
    └── demo-welcome/       # Sito dimostrativo preinstallato per testare subito il Discovery Server
        ├── index.html
        └── site.json
```

---

## 2.4 Integrazione Unificata e Navigazione Comune

Tutti e 3 i servizi condividono la stessa filosofia architetturale:

```text
                      ┌───────────────────────────────────┐
                      │   Landing Page (http://127.0.0.1) │
                      │     OcchioDiFalcoWebServer/       │
                      └─────────────────┬─────────────────┘
                                        │
        ┌───────────────────────────────┼───────────────────────────────┐
        ▼                               ▼                               ▼
┌───────────────────┐           ┌───────────────────┐           ┌───────────────────┐
│ /occhio-di-falco/ │◄─────────►│    /my-cloud/     │◄─────────►│/discovery-server/ │
│  Health Checker   │  Topbar   │    File Server    │  Topbar   │   Web Provider    │
└─────────┬─────────┘  Comune   └─────────┬─────────┘  Comune   └─────────┬─────────┘
          │                               │                               │
          ▼                               ▼                               ▼
   Python Listener                 Filesystem Locale               Auto-Discovery
   (127.0.0.1:5050)                  + MySQL (:3306)              Siti Web Ospitati
   + MySQL (:3306)
```

1. **Topbar di Navigazione Condivisa**:
   - Ogni servizio presenta in alto la stessa barra `OcchioDiFalco` con il pulsante rapido per tornare alla **Landing Page (`/`)** o passare direttamente agli altri due servizi.
2. **Design System Unificato**:
   - Tutti i servizi utilizzano la stessa palette Dark/Slate (`#0f172a` / `#1e293b`) con il proprio colore d'accento distintivo:
     - **Sky Blue (`#38bdf8`)** per **Server Health Checker** (`/occhio-di-falco/`)
     - **Emerald Green (`#22c55e`)** per **My Cloud · File Server** (`/my-cloud/`)
     - **Royal Purple (`#a855f7`)** per **Discovery Server** (`/discovery-server/`)
3. **Funzionamento 100% Locale & Offline**:
   - Nessuna dipendenza da librerie o font esterni su Internet: l'intero sistema (GUI Desktop Python + 3 Servizi Web + MySQL) è autonomo e pronto per l'esecuzione immediata su `127.0.0.1`.
