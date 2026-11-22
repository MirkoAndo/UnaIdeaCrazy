# UnaIdeaCrazy – OcchioDiFalco

Piattaforma locale per Windows che unisce una **Web Application modulare a 3 servizi** e un **Pannello di Controllo Desktop interattivo (Python GUI + HTTP API Listener)**:

1. **Server Health Checker (`/occhio-di-falco/`)** – monitoraggio web dello stato dei processi, telemetria hardware (CPU, RAM, Disco, Porte TCP) e registro eventi in comunicazione diretta con il listener Python.
2. **My Cloud · File Server (`/my-cloud/`)** – file manager e cloud storage locale con navigazione cartelle, upload/download protetto da PHP e condivisione tramite link temporanei a scadenza.
3. **Discovery Server (`/discovery-server/`)** – Web Server Provider che scansiona ed elenca automaticamente tutti i siti e i progetti web caricati all'interno della propria directory.
4. **OcchioDiFalco Desktop GUI (`main.pyw` / `occhio_di_falco/`)** – orchestratore desktop (`tkinter`/`ttk`) a 4 schede con telemetria WMI/Win32, esecuzione script batch, scanner porte TCP e server HTTP listener (`127.0.0.1:5050`) con console live delle richieste client.

Lo stack è composto da **Apache HTTP Server 2.4**, **PHP 8.5** (caricato come modulo DSO nativo in Apache), **MySQL Server 26.10.0** e l'applicazione desktop **Python GUI (`tkinter` / `ttk`)** avviabile da `main.pyw`. Tutti i servizi sono eseguiti in modalità portabile, senza installazione di sistema, e sono raggiungibili esclusivamente da `localhost` (`127.0.0.1`).

---

## Indice

1. [Requisiti e Download](#requisiti-e-download)
2. [Struttura delle directory](#struttura-delle-directory)
3. [Architettura Modulare Python (`occhio_di_falco`)](#architettura-modulare-python-occhio_di_falco)
4. [Portale Web e I 3 Servizi (`OcchioDiFalcoWebServer`)](#portale-web-e-i-3-servizi-occhiodifalcowebserver)
5. [Configurazione di Apache](#configurazione-di-apache)
6. [Configurazione di PHP](#configurazione-di-php)
7. [Configurazione di MySQL (`my.ini`)](#configurazione-di-mysql-myini)
8. [Avvio dell'Applicazione GUI, Comandi e API Listener](#avvio-dellapplicazione-gui-comandi-e-api-listener)
9. [Script batch (`CmdCommands`)](#script-batch-cmdcommands)
10. [Note di sicurezza](#note-di-sicurezza)

---

## Requisiti e Download

| Componente | Versione | Link Download | Note |
|---|---|---|---|
| Windows | 10 / 11 x64 | - | Sistema operativo host |
| Visual C++ Redistributable | 2015–2022 x64 | [Download VC++ x64](https://aka.ms/vs/17/release/vc_redist.x64.exe) | Richiesto da Apache, PHP e MySQL |
| Apache HTTP Server | 2.4 (`Apache24`) | [Apache Lounge Downloads](https://www.apachelounge.com/download/) | Build Win64 (ZIP portabile) |
| PHP | 8.5.x x64 (`php-8.5.12x64`) | [PHP for Windows](https://windows.php.net/download/) | Build **VS17 x64 Thread Safe (TS)**, necessaria per `php8apache2_4.dll` |
| MySQL Server | 8.x / 26.x (`mysql-26.10.0`) | [MySQL Community Server](https://dev.mysql.com/downloads/mysql/) | Selezionare **Windows (x86, 64-bit), ZIP Archive** |
| phpMyAdmin | 5.2.3 | [phpMyAdmin Downloads](https://www.phpmyadmin.net/downloads/) | Già presente in `OcchioDiFalcoWebServer/phpmyadmin` |
| Python | 3.10+ | [Python Official Site](https://www.python.org/downloads/) | Include `tkinter`/`ttk`, `http.server` e `socket`; richiede `wmi` (`pip install wmi`) |

> [!IMPORTANT]
> La versione **Non Thread Safe (NTS)** di PHP **non** contiene `php8apache2_4.dll` e non può essere caricata come modulo nativo di Apache. Scaricare sempre la variante **Thread Safe (TS)**.

---

## Struttura delle directory

Il progetto presuppone che i binari dei servizi siano estratti nella cartella `Servizi_UnaIdeaCrazy`, posizionata allo stesso livello del repository `UnaIdeaCrazy`:

```text
GitHub/
├── Servizi_UnaIdeaCrazy/
│   ├── Apache24/
│   │   ├── bin/
│   │   │   └── httpd.exe               # Binario Apache monitorato via WMI
│   │   └── conf/
│   │       ├── env.conf                # Variabili d'ambiente locali (non versionato)
│   │       └── httpd.conf              # Configurazione principale Apache
│   ├── mysql-26.10.0/
│   │   ├── bin/
│   │   │   └── mysqld.exe              # Demone MySQL monitorato via WMI
│   │   ├── data/                       # Directory fisica dei database
│   │   └── my.ini                      # Configurazione MySQL (porta 3306)
│   └── php-8.5.12x64/
│       ├── ext/                        # Estensioni PHP (.dll)
│       ├── php8apache2_4.dll           # Modulo nativo caricato da Apache
│       └── php.ini                     # Configurazione PHP
└── UnaIdeaCrazy/
    ├── CmdCommands/                    # Script batch eseguiti dall'applicazione Python
    │   ├── sv_apache.bat               # Avvio Apache HTTP Server
    │   ├── sv_mysql.bat                # Avvio MySQL Server
    │   ├── stop_apache.bat             # Arresto Apache (con elevazione UAC automatica)
    │   └── stop_mysql.bat              # Arresto MySQL (con elevazione UAC automatica)
    ├── OcchioDiFalcoWebServer/         # DocumentRoot di Apache (equivalente htdocs/)
    │   ├── index.php                   # Landing Page principale con accesso ai 3 servizi
    │   ├── style-root/
    │   │   └── landing.css             # Foglio di stile Dark/Slate della Landing Page
    │   ├── occhio-di-falco/            # Servizio #1: Server Health Checker
    │   ├── my-cloud/                   # Servizio #2: My Cloud (File Server / FTP Web)
    │   ├── discovery-server/           # Servizio #3: Discovery Server (Web Server Provider)
    │   └── phpmyadmin/                 # phpMyAdmin 5.2.3 per amministrazione MySQL
    ├── occhio_di_falco/                # Pacchetto Python modulare (GUI, servizi, monitoraggio, API)
    │   ├── __init__.py                 # Esportazione API del pacchetto
    │   ├── config.py                   # Costanti, percorsi, porte API, CUSTOM_COMMANDS e parser config
    │   ├── services.py                 # Controllo processi WMI, stato servizi ed esecuzione .bat
    │   ├── monitoring.py               # Telemetria CPU/RAM (WMI/Win32) e scanner porte socket
    │   ├── styles.py                   # Palette colori (ThemeColors) e configurazione ttk.Style
    │   ├── tab_overview.py             # Tab 1: Card servizi (Apache, MySQL, Sistema) e tabella stato
    │   ├── tab_commands.py             # Tab 2: Console comandi custom, filtri e ispettore .bat
    │   ├── tab_monitor.py              # Tab 3: Scanner porte socket (80, 443, 3306, 5050) e albero stack
    │   ├── tab_requests.py             # Tab 4: Listener HTTP (127.0.0.1:5050), script risposta e console
    │   └── app.py                      # Finestra principale OcchioDiFalcoGUI
    ├── Obbiettivi/                     # Documentazione architetturale e specifiche progettuali
    │   ├── Architettura e Sviluppo 3 Servizi.md
    │   ├── OcchioDiFalco.md
    │   ├── My Cloud.md
    │   └── qualcosa di davvero fottutissimamente mentalemente instabile.md
    ├── main.pyw                        # Entrypoint principale dell'applicazione desktop GUI
    └── readme.md
```

---

## Architettura Modulare Python (`occhio_di_falco`)

Il pannello di controllo desktop è progettato secondo una separazione netta delle responsabilità all'interno del pacchetto `occhio_di_falco/`, mantenendo `main.pyw` snello e leggibile:

| Modulo | Responsabilità Principale |
|---|---|
| `main.pyw` | Entrypoint dell'applicazione desktop (senza finestra console CMD residua): importa il pacchetto `occhio_di_falco`, espone le variabili di stato a livello di modulo e avvia `OcchioDiFalcoGUI`. |
| `occhio_di_falco/config.py` | Definisce i percorsi base (`BASE_DIR`, `CMD_COMMANDS_DIR`, `WEB_SERVER_DIR`, `OBBIETTIVI_DIR`), l'endpoint del listener Python (`DEFAULT_API_HOST = "127.0.0.1"`, `DEFAULT_API_PORT = 5050`), i codici ANSI, `ASCII_logo_service`, `CUSTOM_COMMANDS` e il parser `read_real_service_configs()` per `env.conf` e `my.ini`. |
| `occhio_di_falco/services.py` | Gestisce la rilevazione thread-safe dei processi tramite WMI (`get_process_status` con rilascio esplicito dei puntatori COM e fallback `tasklist`), la costruzione di `services_status`, l'esecuzione degli script `.bat` (`execute_batch_command`) e la generazione della tabella ASCII `format_occhio_di_falco_table()`. |
| `occhio_di_falco/monitoring.py` | Raccoglie le metriche hardware CPU e RAM (`get_system_metrics` tramite struttura C `MEMORYSTATUSEX` di `kernel32` e classi WMI `Win32_Processor` / `Win32_OperatingSystem`) e verifica l'apertura e la latenza delle porte locali TCP tramite `socket` (`check_local_port`). |
| `occhio_di_falco/styles.py` | Centralizza la palette cromatica (`ThemeColors`, tema Dark/Slate coordinato con il portale web) e configura tutti i widget `ttk` (`TNotebook`, `TButton`, `Treeview`, `TCombobox`, `TRadiobutton`, `TCheckbutton`, `Horizontal.TProgressbar`). |
| `occhio_di_falco/tab_overview.py` | **Tab 1 – Panoramica & Dati `main.pyw`**: Card dedicate per **Apache HTTP Server**, **MySQL Database Server** e **Risorse & Hardware** con badge dinamici (`ONLINE`/`OFFLINE` + PID), pulsanti rapidi, tabella `services_status` filtrabile e anteprima live di `Occhio_di_falco_table`. |
| `occhio_di_falco/tab_commands.py` | **Tab 2 – Comandi Custom & Script Batch**: Barra di esecuzione comandi interattiva, catalogo filtrabile di `CUSTOM_COMMANDS` e ispettore in sola lettura del codice sorgente dei file `.bat`. |
| `occhio_di_falco/tab_monitor.py` | **Tab 3 – Monitor Porte & Struttura Servizi**: Scanner porte TCP locali (`127.0.0.1:80`, `127.0.0.1:443`, `127.0.0.1:3306`, `127.0.0.1:5050` + porta custom) tramite `socket` ed esploratore ad albero della gerarchia reale dello stack con anteprima dei file di configurazione. |
| `occhio_di_falco/tab_requests.py` | **Tab 4 – Listener Richieste & Console Risposte**: Server HTTP multi-thread (`ReusableThreadingHTTPServer` su `127.0.0.1:5050`) che intercetta le richieste effettuate dai client web (es. `/occhio-di-falco/`), mostra la tabella delle richieste ricevute, l'ispettore a 3 viste dello script/payload di risposta e la console live socket. |
| `occhio_di_falco/app.py` | Finestra principale `OcchioDiFalcoGUI`: coordina l'header, il `ttk.Notebook` a 4 schede, la coda thread-safe `_app_ui_queue` per l'aggiornamento UI, il pannello di log scorrevole `ScrolledText`, la barra di stato e il ciclo di auto-refresh asincrono. |

---

## Portale Web e I 3 Servizi (`OcchioDiFalcoWebServer`)

La `DocumentRoot` di Apache (`OcchioDiFalcoWebServer/`) ospita la landing page principale e le directory dedicate ai 3 servizi web:

- **`index.php` + `style-root/landing.css`**:
  - Esegue un controllo istantaneo in PHP dello stato di Apache, della versione PHP/SAPI, del Sistema Operativo host e della raggiungibilità del socket MySQL (`127.0.0.1:3306` con timeout rapido a `150ms`).
  - Verifica dinamicamente tramite `is_dir()` la presenza delle cartelle dei 3 servizi e presenta le rispettive card di accesso:
    1. **Servizio #1 – Server Health Checker (`/occhio-di-falco/`)**: diagnostica hardware, stato processi e log eventi della macchina ospitante.
    2. **Servizio #2 – My Cloud · File Server (`/my-cloud/`)**: archiviazione, organizzazione cartelle, upload/download protetto e condivisione file tramite link temporanei.
    3. **Servizio #3 – Discovery Server (`/discovery-server/`)**: Web Server Provider che scansiona ed elenca tutti i siti web caricati nella propria directory per avviarli con un click.

> [!TIP]
> Per l'analisi teorica approfondita dell'architettura attuale e le specifiche di implementazione futura dei 3 servizi web, consultare il documento [Obbiettivi/Architettura e Sviluppo 3 Servizi.md](Obbiettivi/Architettura%20e%20Sviluppo%203%20Servizi.md).

---

## Configurazione di Apache

La configurazione è suddivisa in due file:

- `env.conf` – contiene i percorsi e i parametri specifici della macchina. È escluso dal versionamento (`.gitignore`).
- `httpd.conf` – configurazione principale, indipendente dalla macchina, che importa `env.conf`.

### `Apache24/conf/env.conf`

Adattare i percorsi alla propria installazione (usare lo slash `/` come separatore):

```apache
# ==========================================
# VARIABILI D'AMBIENTE LOCALI (APACHE)
# ==========================================

Define SRVROOT       "C:/Users/salvo/Documents/GitHub/Servizi_UnaIdeaCrazy/Apache24"
Define DOCUMENT_ROOT "C:/Users/salvo/Documents/GitHub/UnaIdeaCrazy/OcchioDiFalcoWebServer"
Define PHP_DIR       "C:/Users/salvo/Documents/GitHub/Servizi_UnaIdeaCrazy/php-8.5.12x64"

# Binding di sicurezza (solo localhost)
Define HOST_IP   "127.0.0.1"
Define HOST_PORT "80"
```

### `Apache24/conf/httpd.conf`

```apache
# ==========================================
# INCLUSIONE VARIABILI D'AMBIENTE
# ==========================================
Include conf/env.conf

# Radice del server Apache
ServerRoot "${SRVROOT}"

# ==========================================
# CONFIGURAZIONE DI ASCOLTO (NETWORK)
# ==========================================
# Binding esclusivo su 127.0.0.1 (localhost)
Listen ${HOST_IP}:${HOST_PORT}

# ==========================================
# MODULI DINAMICI (DSO)
# ==========================================
LoadModule access_compat_module   modules/mod_access_compat.so
LoadModule auth_basic_module      modules/mod_auth_basic.so
LoadModule authn_core_module      modules/mod_authn_core.so
LoadModule authn_file_module      modules/mod_authn_file.so
LoadModule authz_core_module      modules/mod_authz_core.so
LoadModule authz_groupfile_module modules/mod_authz_groupfile.so
LoadModule authz_host_module      modules/mod_authz_host.so
LoadModule authz_user_module      modules/mod_authz_user.so
LoadModule filter_module          modules/mod_filter.so
LoadModule reqtimeout_module      modules/mod_reqtimeout.so
LoadModule autoindex_module       modules/mod_autoindex.so
LoadModule mime_module            modules/mod_mime.so
LoadModule log_config_module      modules/mod_log_config.so
LoadModule alias_module           modules/mod_alias.so
LoadModule dir_module             modules/mod_dir.so
LoadModule env_module             modules/mod_env.so
LoadModule headers_module         modules/mod_headers.so
LoadModule setenvif_module        modules/mod_setenvif.so
LoadModule version_module         modules/mod_version.so

<IfModule unixd_module>
    User daemon
    Group daemon
</IfModule>

# ==========================================
# IMPOSTAZIONI GENERALI DEL SERVER
# ==========================================
ServerAdmin mirko.ando.dev@gmail.com

# Protezione globale del filesystem
<Directory />
    AllowOverride none
    Require all denied
</Directory>

# Cartella principale del progetto (OcchioDiFalcoWebServer)
DocumentRoot "${DOCUMENT_ROOT}"
<Directory "${DOCUMENT_ROOT}">
    Options Indexes FollowSymLinks
    AllowOverride None
    Require all granted
</Directory>

# Pagina predefinita
<IfModule dir_module>
    DirectoryIndex index.php index.html
</IfModule>

# Protezione file nascosti (.htaccess, .htpasswd, ecc.)
<Files ".ht*">
    Require all denied
</Files>

# Log del server
ErrorLog "logs/error_log"
LogLevel warn

<IfModule log_config_module>
    LogFormat "%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-Agent}i\"" combined
    LogFormat "%h %l %u %t \"%r\" %>s %b" common
    CustomLog "logs/access_log" common
</IfModule>

<IfModule alias_module>
    ScriptAlias /cgi-bin/ "${SRVROOT}/cgi-bin/"
</IfModule>

<Directory "${SRVROOT}/cgi-bin">
    AllowOverride None
    Options None
    Require all granted
</Directory>

<IfModule headers_module>
    RequestHeader unset Proxy early
</IfModule>

<IfModule mime_module>
    TypesConfig conf/mime.types
    AddType application/x-compress .Z
    AddType application/x-gzip .gz .tgz
</IfModule>

# ==========================================
# INTEGRAZIONE PHP (phpMyAdmin / Script)
# ==========================================
LoadModule php_module "${PHP_DIR}/php8apache2_4.dll"
AddHandler application/x-httpd-php .php
PHPIniDir "${PHP_DIR}"
```

Verifica della sintassi di configurazione:

```powershell
..\Servizi_UnaIdeaCrazy\Apache24\bin\httpd.exe -t
```

---

## Configurazione di PHP

Creare `php.ini` a partire da `php.ini-development` (o `php.ini-production`) e abilitare le seguenti direttive.

### `php-8.5.12x64/php.ini`

```ini
extension_dir = "ext"
extension=mysqli
```

Estensioni consigliate per phpMyAdmin:

```ini
extension=mbstring
extension=openssl
extension=zip
```

> [!NOTE]
> Un percorso relativo in `extension_dir` (es. `"./ext"`) viene risolto rispetto alla directory di lavoro del processo `httpd.exe`, non a quella di PHP. In caso di errori di caricamento delle estensioni, usare il percorso assoluto, ad esempio:  
> `extension_dir = "C:/Users/salvo/Documents/GitHub/Servizi_UnaIdeaCrazy/php-8.5.12x64/ext"`

Verifica dei moduli caricati:

```powershell
..\Servizi_UnaIdeaCrazy\php-8.5.12x64\php.exe -m
```

---

## Configurazione di MySQL (`my.ini`)

All'interno della cartella di MySQL (`Servizi_UnaIdeaCrazy/mysql-26.10.0/`), creare o modificare il file `my.ini` con il seguente contenuto:

```ini
[mysqld]
basedir=C:/Users/salvo/Documents/GitHub/Servizi_UnaIdeaCrazy/mysql-26.10.0
datadir=C:/Users/salvo/Documents/GitHub/Servizi_UnaIdeaCrazy/mysql-26.10.0/data
port=3306
```

Inizializzazione della cartella dati (`data`) al primo avvio:

```powershell
cd ..\Servizi_UnaIdeaCrazy\mysql-26.10.0\bin
.\mysqld.exe --defaults-file="..\my.ini" --initialize-insecure --console
```

---

## Avvio dell'Applicazione GUI, Comandi e API Listener

Per avviare l'applicazione desktop **OcchioDiFalco GUI**:

```powershell
pip install wmi
python main.pyw
```
*(In alternativa è possibile fare doppio click direttamente su `main.pyw` da Esplora File di Windows per avviare la GUI senza finestra terminale).*

### Funzionalità Principali dell'Interfaccia Grafica (4 Tab)

1. **Tab 1 – Panoramica & Dati `main.pyw`**:
   - **Card Apache HTTP Server** e **Card MySQL Database Server** con badge di stato in tempo reale (`●  ONLINE  ·  PID ...` / `●  OFFLINE  ·  PID —`), pulsanti rapidi di avvio/arresto (`▶ Avvia`, `⏹ Ferma`), apertura rapida nel browser (`🌐 Web` / `🗄️ Admin`) e apertura della cartella del servizio in Esplora File (`📂 File`).
   - **Card Risorse & Hardware** con barre di utilizzo **CPU %** e **RAM GB** aggiornate in background tramite WMI e Win32 API.
   - Tabella interattiva `services_status` con filtro di ricerca e ispettore dettagliato con anteprima di `Occhio_di_falco_table`.
2. **Tab 2 – Comandi Custom & Script Batch**:
   - Console comandi interattiva (con menu a tendina e campo di input), filtro per servizio e visualizzatore del codice sorgente degli script `.bat` e delle variabili d'ambiente passate (`%1`, `SERVICE_POSITION`, `SERVICE_NAME`).
3. **Tab 3 – Monitor Porte (`socket`) & Struttura Servizi**:
   - Scanner di porte TCP locali tramite `socket` per `127.0.0.1:80` (Apache HTTP), `127.0.0.1:443` (Apache HTTPS), `127.0.0.1:3306` (MySQL) e `127.0.0.1:5050` (OcchioDiFalco Python API Listener), oltre a un tester per porte personalizzate.
   - Albero gerarchico interattivo dell'intero stack (`UnaIdeaCrazy` e `Servizi_UnaIdeaCrazy`) con corrispondenza rispetto a un ambiente XAMPP tradizionale e anteprima integrata dei file di configurazione (`env.conf`, `httpd.conf`, `my.ini`, `php.ini`).
4. **Tab 4 – Listener Richieste & Console Risposte**:
   - **Controllo Listener HTTP (`127.0.0.1:5050`)**: avvio/arresto del server HTTP multi-thread integrato e simulatore di richieste client (`🧪 Simula Richiesta Client`).
   - **Tabella Richieste Client**: intercetta e mostra in tempo reale tutte le richieste provenienti dal client web (es. da `http://127.0.0.1/occhio-di-falco/`), riportando `#ID`, `Orario`, `Metodo`, `Endpoint`, `Origine/Referer`, `Status HTTP`, `Latenza (ms)` e `Dimensione Payload`.
   - **Ispettore Script di Risposta (3 Viste)**:
     - *Payload JSON Risposta*: header HTTP della richiesta e JSON completo restituito al client.
     - *Script Python Handler*: codice sorgente del costruttore del payload in Python.
     - *Script Client PHP/JS*: snippet di integrazione PHP e JavaScript (`fetch`) per `/occhio-di-falco/`.
   - **Console Listener Live**: terminale dedicato che mostra in diretta i log di ascolto socket (`[LISTEN]`), le richieste in ingresso (`[REQ <<]`) e le risposte inviate (`[RES >>]`).

### Comandi Custom Supportati

| Comando | Pulsante GUI / Azione | Script Eseguito |
|---|---|---|
| `/help` | Pulsante `❓ /help` / Console Tab 2 | Stampa la lista dei comandi custom nel pannello di log |
| `sv apache` | Pulsante `▶ Avvia` (Card Apache) | Esegue `CmdCommands\sv_apache.bat` |
| `sv mysql` | Pulsante `▶ Avvia` (Card MySQL) | Esegue `CmdCommands\sv_mysql.bat` |
| `stop apache` | Pulsante `⏹ Ferma` (Card Apache) | Esegue `CmdCommands\stop_apache.bat` |
| `stop mysql` | Pulsante `⏹ Ferma` (Card MySQL) | Esegue `CmdCommands\stop_mysql.bat` |
| `exit` / `quit` | Chiusura finestra / Console Tab 2 | Arresta il listener HTTP e chiude OcchioDiFalco GUI |

### URL delle Risorse Web e Endpoint API Locali

| Risorsa / Servizio | URL Locale | Descrizione |
|---|---|---|
| **Landing Page Portale** | <http://127.0.0.1/> | Pagina iniziale con stato rapido e accesso ai 3 servizi |
| **Servizio #1 – Server Health Checker** | <http://127.0.0.1/occhio-di-falco/> | Dashboard web telemetria hardware, processi ed eventi |
| **Servizio #2 – My Cloud (File Server)** | <http://127.0.0.1/my-cloud/> | File manager locale, upload/download e link temporanei |
| **Servizio #3 – Discovery Server** | <http://127.0.0.1/discovery-server/> | Web Server Provider con catalogo automatico dei siti ospitati |
| **phpMyAdmin** | <http://127.0.0.1/phpmyadmin/> | Amministrazione database MySQL (`127.0.0.1:3306`) |
| **API Python – Health & Telemetria** | <http://127.0.0.1:5050/api/health> | JSON completo: CPU, RAM, Disco, Servizi WMI e Porte TCP |
| **API Python – Stato Servizi** | <http://127.0.0.1:5050/api/services> | JSON con stato e PID di Apache, MySQL, PHP e OcchioDiFalco |
| **API Python – Stato Porte** | <http://127.0.0.1:5050/api/ports> | JSON con stato socket e latenza porte `80`, `443`, `3306`, `5050` |
| **API Python – Esecuzione Comandi** | `http://127.0.0.1:5050/api/command?cmd=...` | Esecuzione remota locale dei comandi di `CUSTOM_COMMANDS` |

---

## Script batch (`CmdCommands`)

I comandi di avvio e stop richiamano gli script `.bat` situati nella cartella `CmdCommands/`:

- `execute_batch_command()` passa la posizione assoluta del servizio come **primo argomento** (`%~1`) e imposta le variabili d'ambiente `%SERVICE_POSITION%` e `%SERVICE_NAME%`.
- Gli script utilizzano questo parametro per avviare o arrestare i relativi binari:
  - `sv_apache.bat`: avvia `%SERVICE_DIR%\bin\httpd.exe` in background.
  - `sv_mysql.bat`: avvia `%SERVICE_DIR%\bin\mysqld.exe` specificando `--defaults-file="%SERVICE_DIR%\my.ini"`.
  - `stop_apache.bat`: termina il processo `httpd.exe` con `taskkill` (richiedendo elevazione UAC se necessario).
  - `stop_mysql.bat`: termina il processo `mysqld.exe` con `taskkill` (richiedendo elevazione UAC se necessario).

---

## Note di sicurezza

- Apache e il Listener Python sono in ascolto **esclusivamente** su `127.0.0.1`: i servizi non sono esposti ad altri host della rete locale o esterna.
- L'accesso al file system da Apache è negato di default (`<Directory />` → `Require all denied`); è consentita solo la `DocumentRoot` (`OcchioDiFalcoWebServer`).
- I file `.ht*` non sono serviti al client.
- `env.conf` e `.env` contengono configurazioni locali e **non** devono essere versionati.
- Con `mysqld --initialize-insecure` l'utente `root` non ha password: impostarne una prima di qualsiasi utilizzo non strettamente locale.
- `Options Indexes` abilita il listing delle directory prive di file indice; rimuoverlo se non necessario.
