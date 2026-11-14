"""
Configurazione globale, percorsi del progetto, costanti ANSI, logo ASCII,
dizionario CUSTOM_COMMANDS e lettura delle configurazioni reali (Apache/MySQL).
"""

import os

# Enable ANSI escape sequences in Windows console (preservato dallo script originale)
os.system('')

# Percorsi principali del progetto (rispetto alla radice del repository)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CMD_COMMANDS_DIR = os.path.join(BASE_DIR, "CmdCommands")
WEB_SERVER_DIR = os.path.join(BASE_DIR, "MissionControlWebServer")
OBBIETTIVI_DIR = os.path.join(BASE_DIR, "Obbiettivi")

# Codici ANSI originali (preservati per compatibilità)
RED = "\033[91m"
WHITE = "\033[97m"
GREEN = "\033[92m"
BLUE = "\033[94m"
LIGHTYELLOW = "\033[93m"
RESET = "\033[0m"

# Posizioni relative dei servizi (come definite nello script originale)
SERVICE_POSITIONS = {
    "mission_control": "localset",
    "APACHE": "../Servizi_UnaIdeaCrazy/Apache24",
    "MYSQL": "../Servizi_UnaIdeaCrazy/mysql-26.10.0",
    "PHP": "../Servizi_UnaIdeaCrazy/php-8.5.12x64",
}

# Logo ASCII originale
ASCII_logo_service = r"""
 __       __  __            __                         ______                   __           __        _______    ______          ______    ______    ______    ______  
/  \     /  |/  |          /  |                       /      \                 /  |         /  |      /       |  /      \        /      \  /      \  /      \  /      \ 
$$  \   /$$ |$$/   ______  $$ |   __   ______        /$$$$$$  | _______    ____$$ |  ______ $$/       $$$$$$$/  /$$$$$$  |      /$$$$$$  |/$$$$$$  |/$$$$$$  |/$$$$$$  |
$$$  \ /$$$ |/  | /      \ $$ |  /  | /      \       $$ |__$$ |/       \  /    $$ | /      \$/        $$ |____  $$ |  $$/       $$____$$ |$$$  \$$ |$$____$$ |$$ \__$$/ 
$$$$  /$$$$ |$$ |/$$$$$$  |$$ |_/$$/ /$$$$$$  |      $$    $$ |$$$$$$$  |/$$$$$$$ |/$$$$$$  |         $$      \ $$ |             /    $$/ $$$$  $$ | /    $$/ $$      \ 
$$ $$ $$/$$ |$$ |$$ |  $$/ $$   $$<  $$ |  $$ |      $$$$$$$$ |$$ |  $$ |$$ |  $$ |$$ |  $$ |         $$$$$$$  |$$ |   __       /$$$$$$/  $$ $$ $$ |/$$$$$$/  $$$$$$$  |
$$ |$$$/ $$ |$$ |$$ |      $$$$$$  \ $$ \__$$ |      $$ |  $$ |$$ |  $$ |$$ \__$$ |$$ \__$$ |         /  \__$$ |$$ \__/  |      $$ |_____ $$ \$$$$ |$$ |_____ $$ \__$$ |
$$ | $/  $$ |$$ |$$ |      $$ | $$  |$$    $$/       $$ |  $$ |$$ |  $$ |$$    $$ |$$    $$/          $$    $$/ $$    $$/       $$       |$$   $$$/ $$       |$$    $$/ 
$$/      $$/ $$/ $$/       $$/   $$/  $$$$$$/        $$/   $$/ $$/   $$/  $$$$$$$/  $$$$$$/            $$$$$$/   $$$$$$/        $$$$$$$$/  $$$$$$/  $$$$$$$$/  $$$$$$/  
"""

# Dizionario comandi custom originale
CUSTOM_COMMANDS = {
    'sv apache': {
        'service': 'APACHE',
        'desc': 'avvia Apache',
        'process': 'httpd.exe'
    },
    'sv mysql': {
        'service': 'MYSQL',
        'desc': 'avvia MySQL',
        'process': 'mysqld.exe'
    },
    'stop apache': {
        'service': 'APACHE',
        'desc': 'ferma Apache',
        'process': 'httpd.exe'
    },
    'stop mysql': {
        'service': 'MYSQL',
        'desc': 'ferma MySQL',
        'process': 'mysqld.exe'
    },
    'test command': {
        'service': 'TEST',
        'desc': 'comando di test',
        'process': ''
    }
}


def strip_ansi(text):
    """Rimuove i codici di escape ANSI per la visualizzazione pulita nella GUI."""
    if text is None:
        return "N/A (Modulo)"
    cleaned = str(text)
    for code in (RED, WHITE, GREEN, BLUE, LIGHTYELLOW, RESET):
        cleaned = cleaned.replace(code, "")
    return cleaned.strip()


def read_real_service_configs():
    """
    Legge i file di configurazione reali (env.conf, my.ini) dalle posizioni
    definite in SERVICE_POSITIONS per mostrare i valori effettivi nella GUI.
    """
    info = {
        "apache_host": "127.0.0.1",
        "apache_port": 80,
        "apache_srvroot": "",
        "apache_docroot": WEB_SERVER_DIR,
        "php_dir": "",
        "mysql_port": 3306,
        "mysql_basedir": "",
        "mysql_datadir": "",
    }

    apache_abs = os.path.abspath(os.path.join(BASE_DIR, SERVICE_POSITIONS["APACHE"]))
    env_conf_path = os.path.join(apache_abs, "conf", "env.conf")
    if os.path.exists(env_conf_path):
        try:
            with open(env_conf_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line_s = line.strip()
                    if line_s.startswith("Define "):
                        parts = line_s.split(None, 2)
                        if len(parts) == 3:
                            key = parts[1].strip()
                            val = parts[2].strip().strip('"')
                            if key == "HOST_IP":
                                info["apache_host"] = val
                            elif key == "HOST_PORT" and val.isdigit():
                                info["apache_port"] = int(val)
                            elif key == "SRVROOT":
                                info["apache_srvroot"] = val
                            elif key == "DOCUMENT_ROOT":
                                info["apache_docroot"] = val
                            elif key == "PHP_DIR":
                                info["php_dir"] = val
        except Exception:
            pass

    mysql_abs = os.path.abspath(os.path.join(BASE_DIR, SERVICE_POSITIONS["MYSQL"]))
    my_ini_path = os.path.join(mysql_abs, "my.ini")
    if os.path.exists(my_ini_path):
        try:
            with open(my_ini_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line_s = line.strip()
                    if "=" in line_s and not line_s.startswith("#"):
                        k, v = line_s.split("=", 1)
                        k, v = k.strip().lower(), v.strip().strip('"')
                        if k == "port" and v.isdigit():
                            info["mysql_port"] = int(v)
                        elif k == "basedir":
                            info["mysql_basedir"] = v
                        elif k == "datadir":
                            info["mysql_datadir"] = v
        except Exception:
            pass

    return info
