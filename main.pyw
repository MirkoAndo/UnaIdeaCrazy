"""
OcchioDiFalco (Entrypoint Principale)

L'architettura è suddivisa in moduli dedicati all'interno del pacchetto `occhio_di_falco/`:
- `occhio_di_falco/config.py`       : Percorsi, costanti ANSI, logo ASCII, `CUSTOM_COMMANDS` e parser config reali.
- `occhio_di_falco/services.py`     : Controllo processi WMI (`get_process_status`), stato servizi ed esecuzione `.bat`.
- `occhio_di_falco/monitoring.py`   : Telemetria hardware CPU/RAM (`get_system_metrics`) e verifica porte TCP (`socket`).
- `occhio_di_falco/styles.py`       : Palette colori `ThemeColors` e stili `ttk.Style`.
- `occhio_di_falco/tab_overview.py` : Tab 1 - Panoramica & Dati `main.pyw`.
- `occhio_di_falco/tab_commands.py` : Tab 2 - Comandi Custom & Script Batch (`CmdCommands`).
- `occhio_di_falco/tab_monitor.py`  : Tab 3 - Monitor Porte (`socket`) & Struttura Servizi Reale (XAMPP-like).
- `occhio_di_falco/tab_requests.py` : Tab 4 - Listener Richieste Client, Script di Risposta & Console Live.
- `occhio_di_falco/app.py`          : Finestra principale `OcchioDiFalcoGUI`.
"""

from occhio_di_falco import (
    BASE_DIR,
    CMD_COMMANDS_DIR,
    WEB_SERVER_DIR,
    OBBIETTIVI_DIR,
    RED,
    WHITE,
    GREEN,
    BLUE,
    LIGHTYELLOW,
    RESET,
    ASCII_logo_service,
    CUSTOM_COMMANDS,
    strip_ansi,
    read_real_service_configs,
    get_process_status,
    build_services_status,
    execute_batch_command,
    format_occhio_di_falco_table,
    get_system_metrics,
    check_local_port,
    OcchioDiFalcoGUI,
)

# Variabili di stato a livello di modulo (preservate per compatibilità con lo script originale)
user_input = ""
apachestatus = get_process_status("httpd.exe")
mysqlstatus = get_process_status("mysqld.exe")
services_status = build_services_status(apachestatus, mysqlstatus)


def main():
    """Avvia l'interfaccia grafica desktop di OcchioDiFalco."""
    app = OcchioDiFalcoGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
