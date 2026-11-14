"""
Gestione dei servizi (Apache, MySQL, PHP, Mission Control), verifica processi WMI,
esecuzione degli script batch (.bat) e formattazione della tabella Mission Control.
"""

import os
import subprocess
import wmi

from .config import (
    BASE_DIR,
    CMD_COMMANDS_DIR,
    SERVICE_POSITIONS,
    GREEN,
    RED,
    RESET,
    strip_ansi,
)


def get_process_status(process_name):
    """
    Verifica lo stato di un processo Windows tramite WMI (funzione originale preservata).
    Supporta anche l'invocazione da thread secondari tramite inizializzazione COM.
    """
    try:
        try:
            import pythoncom
            pythoncom.CoInitialize()
        except Exception:
            pass
        c = wmi.WMI()
        for process in c.Win32_Process(name=process_name):
            # Keep the rendered status width equal to OFFLINE so the links stay aligned.
            return f"{GREEN}ONLINE  {RESET}", process.ProcessId
    except Exception:
        # Fallback rapido tramite tasklist qualora WMI fosse occupato nel thread
        try:
            out = subprocess.check_output(
                ["tasklist", "/FI", f"IMAGENAME eq {process_name}", "/FO", "CSV", "/NH"],
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                text=True,
                stderr=subprocess.DEVNULL
            ).strip()
            if out and not out.startswith("INFO:") and process_name.lower() in out.lower():
                parts = [p.strip('"') for p in out.splitlines()[0].split('","')]
                if len(parts) >= 2 and parts[1].isdigit():
                    return f"{GREEN}ONLINE  {RESET}", int(parts[1])
        except Exception:
            pass
    finally:
        try:
            import pythoncom
            pythoncom.CoUninitialize()
        except Exception:
            pass
    return f"{RED}OFFLINE {RESET}", None


def build_services_status(apachestatus, mysqlstatus):
    """Costruisce e restituisce il dizionario services_status originale."""
    return {
        "mission_control": {
            "status": f"{GREEN}ONLINE {RESET}",
            "pid": os.getpid(),
            "position": SERVICE_POSITIONS["mission_control"],
            "process": "python.exe",
            "link": "",
            "role": "Orchestratore Python & GUI Mission Control"
        },
        "APACHE": {
            "status": apachestatus[0],
            "pid": apachestatus[1],
            "position": SERVICE_POSITIONS["APACHE"],
            "process": "httpd.exe",
            "link": "http://127.0.0.1/",
            "role": "Apache HTTP Server 2.4 (DocumentRoot: MissionControlWebServer)"
        },
        "MYSQL": {
            "status": mysqlstatus[0],
            "pid": mysqlstatus[1],
            "position": SERVICE_POSITIONS["MYSQL"],
            "process": "mysqld.exe",
            "link": "http://127.0.0.1/phpmyadmin",
            "role": "MySQL Server 26.10.0 (Gestito via phpMyAdmin 5.2.3)"
        },
        "PHP": {
            "status": None,
            "pid": None,
            "position": SERVICE_POSITIONS["PHP"],
            "process": "php8apache2_4.dll",
            "link": "",
            "role": "PHP 8.5.12 x64 Thread Safe (Modulo DSO integrato in Apache)"
        }
    }


def execute_batch_command(cmd_name, service_key, services, log_callback=None):
    """
    Esegue lo script .bat corrispondente in CmdCommands/ passando la posizione assoluta
    del servizio sia come argomento (%1) sia tramite variabili d'ambiente.
    """
    bat_filename = f"{cmd_name.replace(' ', '_')}.bat"
    bat_path = os.path.join(CMD_COMMANDS_DIR, bat_filename)

    if not os.path.exists(bat_path):
        msg = f"File di comando non trovato: {bat_path}"
        if log_callback:
            log_callback(msg, "ERROR")
        return False

    service_info = services.get(service_key, {})
    service_pos = service_info.get("position", "")
    service_pos_abs = os.path.abspath(os.path.join(BASE_DIR, service_pos)) if service_pos else ""

    # Prepariamo le variabili d'ambiente per il .bat
    env = os.environ.copy()
    if service_pos_abs:
        env["SERVICE_POSITION"] = service_pos_abs
    if service_key:
        env["SERVICE_NAME"] = service_key

    try:
        if log_callback:
            log_callback(
                f"Esecuzione '{bat_filename}' per {service_key} (Percorso: {service_pos_abs})...",
                "CMD"
            )
        # Passiamo la posizione del file come argomento (%1)
        result = subprocess.run(
            [bat_path, service_pos_abs],
            env=env,
            shell=True,
            capture_output=True,
            text=True
        )
        if result.stdout and result.stdout.strip() and log_callback:
            log_callback(result.stdout.strip(), "INFO")
        if result.stderr and result.stderr.strip() and log_callback:
            log_callback(result.stderr.strip(), "WARN")
        if log_callback:
            log_callback(f"Comando '{cmd_name}' completato (exit code: {result.returncode}).", "SUCCESS")
        return True
    except Exception as e:
        msg = f"Errore durante l'esecuzione di {bat_filename}: {e}"
        if log_callback:
            log_callback(msg, "ERROR")
        return False


def format_mission_control_table(services, cpu_usage, ram_usage):
    """Genera la tabella testuale Mission_control_table originale (senza codici ANSI)."""
    mc_status = strip_ansi(services['mission_control']['status'])
    mc_pid = services['mission_control']['pid']
    ap_status = strip_ansi(services['APACHE']['status'])
    ap_pid = str(services['APACHE']['pid'])
    my_status = strip_ansi(services['MYSQL']['status'])
    my_pid = str(services['MYSQL']['pid'])

    return (
        f"┌──────────────────────────────────────────────────────────────────────┐\n"
        f"│  MISSION CONTROL  ● {mc_status:<8}     PID {mc_pid:<31}│\n"
        f"├──────────────────────────────────────────────────────────────────────┤\n"
        f"│  SERVIZI                                                             │\n"
        f"│                                                                      │\n"
        f"│  {'SERVICE':<12}{'STATUS':<12}{'PID':<10}{'LINK':<34}│\n"
        f"│  {'APACHE':<12}● {ap_status:<10}{ap_pid:<10}{'http://127.0.0.1/':<34}│\n"
        f"│  {'MYSQL':<12}● {my_status:<10}{my_pid:<10}{'http://127.0.0.1/phpmyadmin':<34}│\n"
        f"│  {'PHP':<12}● {'MODULO':<10}{'N/A':<10}{'php8apache2_4.dll (Apache DSO)':<34}│\n"
        f"├──────────────────────────────────────────────────────────────────────┤\n"
        f"│  /help  - lista comandi custom                                       │\n"
        f"├──────────────────────────────────────────────────────────────────────┤\n"
        f"│  SISTEMA                                                             │\n"
        f"│  CPU      {cpu_usage:>5.1f} %                                                    │\n"
        f"│  RAM      {ram_usage / 1024:>5.2f} GB                                                   │\n"
        f"└──────────────────────────────────────────────────────────────────────┘"
    )
