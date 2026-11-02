# UnaIdeaCrazy – Mission Control

Web application locale per Windows che unisce due moduli:

- **My Cloud** – gestione di file sul file system locale.
- **Mission Control** – monitoraggio dello stato e gestione dei servizi (Apache, MySQL, Python).

Lo stack è composto da **Apache HTTP Server 2.4**, **PHP 8.5** (caricato come modulo Apache), **MySQL** e uno script **Python** interattivo di monitoraggio (`main.py`). Tutti i servizi sono eseguiti in modalità portabile, senza installazione di sistema, e sono raggiungibili esclusivamente da `localhost`.

---

## Indice

1. [Requisiti e Download](#requisiti-e-download)
2. [Struttura delle directory](#struttura-delle-directory)
3. [Configurazione di Apache](#configurazione-di-apache)
4. [Configurazione di PHP](#configurazione-di-php)
5. [Configurazione di MySQL (`my.ini`)](#configurazione-di-mysql-myini)
6. [Avvio dei servizi e comandi CLI](#avvio-dei-servizi-e-comandi-cli)
7. [Script batch (`CmdCommands`)](#script-batch-cmdcommands)
8. [Note di sicurezza](#note-di-sicurezza)

---

## Requisiti e Download

| Componente | Versione | Link Download | Note |
|---|---|---|---|
| Windows | 10 / 11 x64 | - | Sistema operativo |
| Visual C++ Redistributable | 2015–2022 x64 | [Download VC++ x64](https://aka.ms/vs/17/release/vc_redist.x64.exe) | Richiesto da Apache, PHP e MySQL |
| Apache HTTP Server | 2.4 (`Apache24`) | [Apache Lounge Downloads](https://www.apachelounge.com/download/) | Build Win64 (ZIP portabile) |
| PHP | 8.5.x x64 (`php-8.5.12x64`) | [PHP for Windows](https://windows.php.net/download/) | Build **VS17 x64 Thread Safe (TS)**, necessaria per `php8apache2_4.dll` |
| MySQL Server | 8.x / 26.x (`mysql-26.10.0`) | [MySQL Community Server](https://dev.mysql.com/downloads/mysql/) | Selezionare **Windows (x86, 64-bit), ZIP Archive** |
| phpMyAdmin | 5.2.3 | [phpMyAdmin Downloads](https://www.phpmyadmin.net/downloads/) | Già presente in `MissionControlWebServer/phpmyadmin` |
| Python | 3.10+ | [Python Official Site](https://www.python.org/downloads/) | Richiede `wmi` (`pip install wmi`) |

> [!IMPORTANT]
> La versione **Non Thread Safe (NTS)** di PHP **non** contiene `php8apache2_4.dll` e non può essere caricata come modulo nativo di Apache. Scaricare sempre la variante **Thread Safe (TS)**.

---

## Struttura delle directory

Il progetto presuppone che i servizi siano estratti in una cartella `Servizi_UnaIdeaCrazy`, posizionata allo stesso livello del repository `UnaIdeaCrazy`:

```text
GitHub/
├── Servizi_UnaIdeaCrazy/
│   ├── Apache24/
│   │   └── conf/
│   │       ├── env.conf                # Variabili d'ambiente locali (non versionato)
│   │       └── httpd.conf              # Configurazione principale Apache
│   ├── mysql-26.10.0/
│   │   ├── bin/
│   │   ├── data/                       # Directory dei database
│   │   └── my.ini                      # Configurazione MySQL
│   └── php-8.5.12x64/
│       ├── ext/
│       └── php.ini                     # Configurazione PHP
└── UnaIdeaCrazy/
    ├── CmdCommands/                    # Script batch eseguiti da main.py
    │   ├── sv_apache.bat
    │   ├── sv_mysql.bat
    │   ├── stop_apache.bat
    │   └── stop_mysql.bat
    ├── MissionControlWebServer/        # DocumentRoot di Apache
    │   ├── index.php
    │   ├── index.html
    │   └── phpmyadmin/
    ├── Obbiettivi/                     # Specifiche di progetto
    ├── main.py                         # Monitor CLI e pannello di controllo
    ├── .env                            # Variabili locali (non versionato)
    └── readme.md
```

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
Define DOCUMENT_ROOT "C:/Users/salvo/Documents/GitHub/UnaIdeaCrazy/MissionControlWebServer"
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

# Cartella principale del progetto (MissionControlWebServer)
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

## Avvio dei servizi e comandi CLI

È possibile avviare e monitorare l'intero ambiente tramite la CLI interattiva di `main.py`:

```powershell
pip install wmi
python main.py
```

### Comandi disponibili in `main.py`

Digitando `/help` all'interno della console interattiva, vengono mostrati i comandi disponibili:

| Comando | Descrizione | Azione eseguita |
|---|---|---|
| `/help` | Mostra la lista dei comandi custom | Stampa la guida a video |
| `sv apache` | Avvia Apache HTTP Server | Esegue `CmdCommands\sv_apache.bat` |
| `sv mysql` | Avvia MySQL Server | Esegue `CmdCommands\sv_mysql.bat` |
| `stop apache` | Ferma Apache | Esegue `CmdCommands\stop_apache.bat` |
| `stop mysql` | Ferma MySQL | Esegue `CmdCommands\stop_mysql.bat` |
| `exit` / `quit` | Esce dalla console | Termina l'interfaccia di monitoraggio |

### URL delle risorse Web

| Risorsa | URL |
|---|---|
| Mission Control | <http://127.0.0.1/> |
| phpMyAdmin | <http://127.0.0.1/phpmyadmin/> |

---

## Script batch (`CmdCommands`)

I comandi di avvio e stop eseguiti da `main.py` richiamano direttamente gli script `.bat` situati nella cartella `CmdCommands/`:

- `main.py` passa la posizione assoluta del servizio come **primo argomento** (`%~1`) e imposta la variabile d'ambiente `%SERVICE_POSITION%`.
- Gli script utilizzano questo parametro per avviare o arrestare i relativi binari:
  - `sv_apache.bat`: avvia `%SERVICE_DIR%\bin\httpd.exe` in background.
  - `sv_mysql.bat`: avvia `%SERVICE_DIR%\bin\mysqld.exe` specificando `--defaults-file="%SERVICE_DIR%\my.ini"`.
  - `stop_apache.bat`: termina il processo `httpd.exe` con `taskkill`.
  - `stop_mysql.bat`: termina il processo `mysqld.exe` con `taskkill`.

---

## Note di sicurezza

- Apache è in ascolto **esclusivamente** su `127.0.0.1`: il server non è raggiungibile da altri host della rete locale o esterna.
- L'accesso al file system è negato di default (`<Directory />` → `Require all denied`); è consentita solo la `DocumentRoot`.
- I file `.ht*` non sono serviti al client.
- `env.conf` e `.env` contengono configurazioni locali e **non** devono essere versionati.
- Con `mysqld --initialize-insecure` l'utente `root` non ha password: impostarne una prima di qualsiasi utilizzo non strettamente locale.
- `Options Indexes` abilita il listing delle directory prive di file indice; rimuoverlo se non necessario.
