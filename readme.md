# UnaIdeaCrazy – Mission Control

Web application locale per Windows che unisce due moduli:

- **My Cloud** – gestione di file sul file system locale.
- **Mission Control** – monitoraggio dello stato dei servizi (Apache, MySQL, Python).

Lo stack è composto da **Apache HTTP Server 2.4**, **PHP 8.5** (caricato come modulo Apache), **MySQL** e uno script **Python** di monitoraggio (`main.py`). Tutti i servizi sono eseguiti in modalità portabile, senza installazione di sistema, e sono raggiungibili esclusivamente da `localhost`.

---

## Indice

1. [Requisiti](#requisiti)
2. [Struttura delle directory](#struttura-delle-directory)
3. [Configurazione di Apache](#configurazione-di-apache)
4. [Configurazione di PHP](#configurazione-di-php)
5. [Avvio dei servizi](#avvio-dei-servizi)
6. [Note di sicurezza](#note-di-sicurezza)

---

## Requisiti

| Componente | Versione | Note |
|---|---|---|
| Windows | 10 / 11 x64 | |
| Apache HTTP Server | 2.4 (`Apache24`) | Build Win64 (es. Apache Lounge) |
| PHP | 8.5.12 x64 (`php-8.5.12x64`) | Build **Thread Safe (TS)**, necessaria per `php8apache2_4.dll` |
| MySQL | 26.10.0 (`mysql-26.10.0`) | Distribuzione ZIP |
| Microsoft Visual C++ Redistributable | 2015–2022 x64 | Richiesto da Apache e PHP |
| Python | 3.x | Dipendenza: `wmi` (`pip install wmi`) |
| phpMyAdmin | 5.2.3 | Già incluso in `MissionControlWebServer/phpmyadmin` |

> **Nota:** la versione Non Thread Safe (NTS) di PHP **non** contiene `php8apache2_4.dll` e non può essere caricata come modulo Apache.

---

## Struttura delle directory

Il progetto presuppone che i servizi siano estratti in una cartella `Servizi`, allo stesso livello del repository:

```text
GitHub/
├── Servizi/
│   ├── Apache24/
│   │   └── conf/
│   │       ├── env.conf        # variabili d'ambiente locali (non versionato)
│   │       └── httpd.conf
│   ├── mysql-26.10.0/
│   └── php-8.5.12x64/
│       └── php.ini
└── UnaIdeaCrazy/
    ├── MissionControlWebServer/    # DocumentRoot di Apache
    │   ├── index.php
    │   ├── index.html
    │   └── phpmyadmin/
    ├── Obbiettivi/                 # specifiche di progetto
    ├── main.py                     # monitor dei servizi
    ├── .env                        # non versionato
    └── readme.md
```

---

## Configurazione di Apache

La configurazione è suddivisa in due file:

- `env.conf` – contiene i percorsi e i parametri specifici della macchina. È escluso dal versionamento (`.gitignore`).
- `httpd.conf` – configurazione principale, indipendente dalla macchina, che importa `env.conf`.

### `Apache24/conf/env.conf`

Adattare i percorsi alla propria installazione. In Apache è consigliato usare `/` come separatore anche su Windows.

```apache
# ==========================================
# VARIABILI D'AMBIENTE LOCALI (APACHE)
# ==========================================

Define SRVROOT       "C:/Users/salvo/Documents/GitHub/Servizi/Apache24"
Define DOCUMENT_ROOT "C:/Users/salvo/Documents/GitHub/UnaIdeaCrazy/MissionControlWebServer"
Define PHP_DIR       "C:/Users/salvo/Documents/GitHub/Servizi/php-8.5.12x64"

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

Verifica della sintassi:

```powershell
..\Servizi\Apache24\bin\httpd.exe -t
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

> **Nota:** un percorso relativo in `extension_dir` (es. `"./ext"`) viene risolto rispetto alla directory di lavoro del processo `httpd.exe`, non a quella di PHP. In caso di errori di caricamento delle estensioni, usare il percorso assoluto, ad esempio `extension_dir = "C:/Users/salvo/Documents/GitHub/Servizi/php-8.5.12x64/ext"`.

Verifica dei moduli caricati:

```powershell
..\Servizi\php-8.5.12x64\php.exe -m
```

---

## Avvio dei servizi

1. **MySQL** – al primo avvio inizializzare la data directory, poi avviare il server:

   ```powershell
   cd ..\Servizi\mysql-26.10.0\bin
   .\mysqld.exe --initialize-insecure --console   # solo al primo avvio
   .\mysqld.exe --console
   ```

2. **Apache**:

   ```powershell
   ..\Servizi\Apache24\bin\httpd.exe
   ```

3. **Monitor dei servizi** (Mission Control CLI):

   ```powershell
   pip install wmi
   python main.py
   ```

4. Aprire nel browser:

   | Risorsa | URL |
   |---|---|
   | Mission Control | <http://127.0.0.1/> |
   | phpMyAdmin | <http://127.0.0.1/phpmyadmin/> |

---

## Note di sicurezza

- Apache è in ascolto **solo** su `127.0.0.1`: il server non è raggiungibile da altri host della rete.
- L'accesso all'intero file system è negato di default (`<Directory />` → `Require all denied`); è consentita solo la `DocumentRoot`.
- I file `.ht*` non sono serviti al client.
- `env.conf` e `.env` contengono configurazioni locali e **non** devono essere versionati.
- Con `mysqld --initialize-insecure` l'utente `root` non ha password: impostarne una prima di qualsiasi utilizzo non strettamente locale.
- `Options Indexes` abilita il listing delle directory prive di file indice; rimuoverlo se non necessario.

```ini
extension=mbstring
extension=openssl
extension=zip
```

> **Nota:** un percorso relativo in `extension_dir` (es. `"./ext"`) viene risolto rispetto alla directory di lavoro del processo `httpd.exe`, non a quella di PHP. In caso di errori di caricamento delle estensioni, usare il percorso assoluto, ad esempio `extension_dir = "C:/Users/salvo/Documents/GitHub/Servizi/php-8.5.12x64/ext"`.

Verifica dei moduli caricati:

```powershell
..\Servizi\php-8.5.12x64\php.exe -m
```

---
