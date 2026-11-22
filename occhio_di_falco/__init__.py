"""
Pacchetto `occhio_di_falco` per UnaIdeaCrazy.
Raccoglie configurazione, logica servizi WMI/Batch, monitoraggio hardware/porte
e componenti dell'interfaccia grafica `tkinter`/`ttk`.
"""

from .config import (
    BASE_DIR,
    CMD_COMMANDS_DIR,
    WEB_SERVER_DIR,
    OBBIETTIVI_DIR,
    DEFAULT_API_HOST,
    DEFAULT_API_PORT,
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
)
from .services import (
    get_process_status,
    build_services_status,
    execute_batch_command,
    format_occhio_di_falco_table,
)
from .monitoring import get_system_metrics, check_local_port
from .tab_requests import RequestsTab
from .app import OcchioDiFalcoGUI

__all__ = [
    "BASE_DIR",
    "CMD_COMMANDS_DIR",
    "WEB_SERVER_DIR",
    "OBBIETTIVI_DIR",
    "DEFAULT_API_HOST",
    "DEFAULT_API_PORT",
    "RED",
    "WHITE",
    "GREEN",
    "BLUE",
    "LIGHTYELLOW",
    "RESET",
    "ASCII_logo_service",
    "CUSTOM_COMMANDS",
    "strip_ansi",
    "read_real_service_configs",
    "get_process_status",
    "build_services_status",
    "execute_batch_command",
    "format_occhio_di_falco_table",
    "get_system_metrics",
    "check_local_port",
    "RequestsTab",
    "OcchioDiFalcoGUI",
]
