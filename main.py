"""
Mission Control (Entrypoint Principale)

L'architettura è suddivisa in moduli dedicati all'interno del pacchetto `mission_control/`:
- `mission_control/config.py`       : Percorsi, costanti ANSI, logo ASCII, `CUSTOM_COMMANDS` e parser config reali.
- `mission_control/services.py`     : Controllo processi WMI (`get_process_status`), stato servizi ed esecuzione `.bat`.
- `mission_control/monitoring.py`   : Telemetria hardware CPU/RAM (`get_system_metrics`) e verifica porte TCP (`socket`).
- `mission_control/styles.py`       : Palette colori `ThemeColors` e stili `ttk.Style`.
- `mission_control/tab_overview.py` : Tab 1 - Panoramica & Dati `main.py`.
- `mission_control/tab_commands.py` : Tab 2 - Comandi Custom & Script Batch (`CmdCommands`).
- `mission_control/tab_monitor.py`  : Tab 3 - Monitor Porte (`socket`) & Struttura Servizi Reale (XAMPP-like).
- `mission_control/app.py`          : Finestra principale `MissionControlGUI`.
"""

from mission_control import (
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
    format_mission_control_table,
    get_system_metrics,
    check_local_port,
    MissionControlGUI,
)

# Variabili di stato a livello di modulo (preservate per compatibilità con lo script originale)
user_input = ""
apachestatus = get_process_status("httpd.exe")
mysqlstatus = get_process_status("mysqld.exe")
services_status = build_services_status(apachestatus, mysqlstatus)


def main():
    """Avvia l'interfaccia grafica desktop di Mission Control."""
    app = MissionControlGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
