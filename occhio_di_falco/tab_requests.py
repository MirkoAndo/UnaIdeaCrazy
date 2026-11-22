"""
Tab 4 - Listener Richieste Client, Script di Risposta & Console Live:
Ascolta su socket HTTP locale (default `127.0.0.1:5050`) le richieste provenienti
dai client web (es. `http://127.0.0.1/occhio-di-falco/` - Server Health Checker),
mostra in tempo reale la tabella delle richieste intercettate, lo script/payload
di risposta generato e la console live di ascolto e risposta.
"""

import os
import json
import time
import queue
import shutil
import threading
import urllib.request
import urllib.parse
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText

from .config import (
    BASE_DIR,
    WEB_SERVER_DIR,
    CUSTOM_COMMANDS,
    DEFAULT_API_HOST,
    DEFAULT_API_PORT,
    strip_ansi,
)
from .styles import ThemeColors


# =============================================================================
# CODICE SORGENTE DELLO SCRIPT DI RISPOSTA (VISUALIZZABILE NELL'ISPETTORE)
# =============================================================================
PYTHON_RESPONSE_SCRIPT_SOURCE = '''# === SCRIPT PYTHON DI ASCOLTO & RISPOSTA (OcchioDiFalco API Listener) ===
# In ascolto su http://127.0.0.1:5050 per richieste da http://127.0.0.1/occhio-di-falco/

def build_health_response_payload(app, endpoint="/api/health", query_params=None):
    """
    Costruisce il dizionario JSON di risposta per il client (Server Health Checker).
    Raccoglie stato processi WMI, telemetria CPU/RAM, spazio disco e stato porte TCP.
    """
    services_clean = {}
    for key, info in app.services.items():
        services_clean[key] = {
            "status": strip_ansi(info.get("status")) if info.get("status") else "MODULO",
            "pid": info.get("pid"),
            "process": info.get("process", ""),
            "position": info.get("position", ""),
            "link": info.get("link", ""),
            "role": info.get("role", ""),
        }

    # Calcolo utilizzo disco della partizione ospitante
    total_b, used_b, free_b = shutil.disk_usage(WEB_SERVER_DIR)
    disk_pct = round((used_b / total_b) * 100.0, 1) if total_b > 0 else 0.0

    # Stato porte socket (80, 443, 3306, 5050)
    ports_clean = {}
    for port, (is_open, latency_ms, detail) in app.port_results.items():
        ports_clean[str(port)] = {
            "open": is_open,
            "latency_ms": latency_ms,
            "detail": detail,
        }

    metrics = app.system_metrics
    tot_ram = metrics.get("total_memory_mb", 0.0)
    used_ram = metrics.get("ram_usage", 0.0)
    ram_pct = round((used_ram / tot_ram) * 100.0, 1) if tot_ram > 0 else 0.0

    return {
        "ok": True,
        "server": "OcchioDiFalco Python Listener",
        "endpoint": endpoint,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "host": {
            "os": metrics.get("os_caption", "Windows"),
            "listener_pid": os.getpid(),
            "cpu_percent": round(metrics.get("cpu_usage", 0.0), 1),
            "ram_used_mb": round(used_ram, 2),
            "ram_total_mb": round(tot_ram, 2),
            "ram_percent": ram_pct,
            "disk_used_gb": round(used_b / (1024 ** 3), 2),
            "disk_total_gb": round(total_b / (1024 ** 3), 2),
            "disk_free_gb": round(free_b / (1024 ** 3), 2),
            "disk_percent": disk_pct,
        },
        "services": services_clean,
        "ports": ports_clean,
    }
'''

CLIENT_PHP_JS_SNIPPET = '''<?php
/**
 * Esempio Client: OcchioDiFalcoWebServer/occhio-di-falco/index.php
 * Interrogazione del listener Python OcchioDiFalco (http://127.0.0.1:5050/api/health)
 */
$apiUrl = 'http://127.0.0.1:5050/api/health';
$ctx = stream_context_create([
    'http' => [
        'method'  => 'GET',
        'timeout' => 1.5,
        'header'  => "Accept: application/json\\r\\n" .
                     "Referer: http://127.0.0.1/occhio-di-falco/\\r\\n" .
                     "X-Client-Service: Server-Health-Checker\\r\\n"
    ]
]);

$rawJson = @file_get_contents($apiUrl, false, $ctx);
$healthData = $rawJson ? json_decode($rawJson, true) : null;
?>

<!-- Oppure via JavaScript fetch() in tempo reale dal browser: -->
<script>
async function fetchServerHealth() {
    const res = await fetch('http://127.0.0.1:5050/api/health', {
        headers: { 'X-Client-Service': 'Server-Health-Checker' }
    });
    const data = await res.json();
    console.log('Risposta da OcchioDiFalco Python:', data);
}
</script>
'''


class ReusableThreadingHTTPServer(ThreadingHTTPServer):
    """Server HTTP multi-thread con riutilizzo immediato della porta locale."""
    allow_reuse_address = True
    daemon_threads = True


class RequestsTab(ttk.Frame):
    """
    Scheda 4: Controllo richieste client (es. da http://127.0.0.1/occhio-di-falco/),
    ispettore dello script/payload di risposta e console live del listener HTTP.
    """

    def __init__(self, parent, app):
        super().__init__(parent, padding=10)
        self.app = app

        # Stato del server listener HTTP
        self.host_var = tk.StringVar(value=DEFAULT_API_HOST)
        self.port_var = tk.StringVar(value=str(DEFAULT_API_PORT))
        self.endpoint_test_var = tk.StringVar(value="/api/health")
        self.search_req_var = tk.StringVar()
        self.inspector_mode_var = tk.StringVar(value="PAYLOAD")
        self.auto_scroll_console_var = tk.BooleanVar(value=True)

        self.http_server = None
        self.server_thread = None
        self.is_listening = False

        # Archivio richieste intercettate in memoria e coda thread-safe per la UI
        self.requests_history = []
        self.request_counter = 0
        self._ui_queue = queue.Queue()

        self._build_ui()
        self._update_inspector_view()
        self._poll_ui_queue()

    def _poll_ui_queue(self):
        """Processa nel main thread di Tkinter tutti gli eventi accodati dai thread HTTP."""
        try:
            while True:
                callback = self._ui_queue.get_nowait()
                try:
                    callback()
                except Exception:
                    pass
        except queue.Empty:
            pass
        if self.winfo_exists():
            self.after(100, self._poll_ui_queue)

    # =========================================================================
    # COSTRUZIONE INTERFACCIA GRAFICA DELLA TAB 4
    # =========================================================================
    def _build_ui(self):
        # ---------------------------------------------------------------------
        # 1. BARRA SUPERIORE: CONTROLLO LISTENER & SIMULATORE RICHIESTE CLIENT
        # ---------------------------------------------------------------------
        top_card = ttk.Frame(self, style="Card.TFrame", padding=12)
        top_card.pack(fill="x", pady=(0, 10))

        header_row = ttk.Frame(top_card, style="Card.TFrame")
        header_row.pack(fill="x", pady=(0, 8))

        ttk.Label(
            header_row,
            text="📡 Listener Richieste Client & API Server (per /occhio-di-falco/)",
            style="CardTitle.TLabel"
        ).pack(side="left")

        self.lbl_listener_badge = tk.Label(
            header_row,
            text="●  LISTENER FERMO",
            bg="#45202a",
            fg="#fda4af",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=4
        )
        self.lbl_listener_badge.pack(side="right")

        self.lbl_stats_counter = ttk.Label(
            header_row,
            text="Richieste ricevute: 0  ·  Ultima: —",
            style="Muted.TLabel"
        )
        self.lbl_stats_counter.pack(side="right", padx=12)

        controls_row = ttk.Frame(top_card, style="Card.TFrame")
        controls_row.pack(fill="x")

        ttk.Label(controls_row, text="Bind Host:", style="Card.TLabel").pack(side="left", padx=(0, 4))
        ttk.Entry(controls_row, textvariable=self.host_var, width=12, state="readonly").pack(side="left", padx=(0, 8))

        ttk.Label(controls_row, text="Porta TCP:", style="Card.TLabel").pack(side="left", padx=(0, 4))
        ttk.Entry(controls_row, textvariable=self.port_var, width=7).pack(side="left", padx=(0, 10))

        self.btn_start_listener = ttk.Button(
            controls_row,
            text="▶ Avvia Listener",
            style="Success.TButton",
            command=self.start_listener
        )
        self.btn_start_listener.pack(side="left", padx=3)

        self.btn_stop_listener = ttk.Button(
            controls_row,
            text="⏹ Ferma Listener",
            style="Danger.TButton",
            command=self.stop_listener
        )
        self.btn_stop_listener.pack(side="left", padx=3)

        ttk.Separator(controls_row, orient="vertical").pack(side="left", fill="y", padx=10)

        ttk.Label(controls_row, text="Endpoint Test:", style="Card.TLabel").pack(side="left", padx=(0, 4))
        ep_combo = ttk.Combobox(
            controls_row,
            textvariable=self.endpoint_test_var,
            values=[
                "/api/health",
                "/api/services",
                "/api/ports",
                "/api/ping",
                "/api/command?cmd=test+command"
            ],
            width=24
        )
        ep_combo.pack(side="left", padx=(0, 6))

        ttk.Button(
            controls_row,
            text="🧪 Simula Richiesta Client",
            style="Primary.TButton",
            command=self.simulate_client_request
        ).pack(side="left", padx=3)

        ttk.Button(
            controls_row,
            text="🌐 Apri /occhio-di-falco/",
            command=lambda: self.app.open_url("http://127.0.0.1/occhio-di-falco/")
        ).pack(side="left", padx=3)

        # ---------------------------------------------------------------------
        # PANED WINDOW VERTICALE: (TABELLA + SCRIPT RISPOSTA) SOPRA, CONSOLE SOTTO
        # ---------------------------------------------------------------------
        main_v_pane = ttk.PanedWindow(self, orient="vertical")
        main_v_pane.pack(fill="both", expand=True)

        # =====================================================================
        # 2. SEZIONE CENTRALE: TABELLA RICHIESTE + ISPETTORE SCRIPT DI RISPOSTA
        # =====================================================================
        mid_h_pane = ttk.PanedWindow(main_v_pane, orient="horizontal")
        main_v_pane.add(mid_h_pane, weight=3)

        # --- Pannello Sinistro: Tabella Richieste Client ---
        req_card = ttk.Frame(mid_h_pane, style="Card.TFrame", padding=10)
        mid_h_pane.add(req_card, weight=3)

        req_top = ttk.Frame(req_card, style="Card.TFrame")
        req_top.pack(fill="x", pady=(0, 6))

        ttk.Label(
            req_top,
            text="📥 Richieste Effettuate dal Client (Intercettate in Tempo Reale)",
            style="CardTitle.TLabel"
        ).pack(side="left")

        ttk.Button(
            req_top,
            text="🧹 Pulisci",
            command=self.clear_requests_history
        ).pack(side="right", padx=(4, 0))

        self.search_req_var.trace_add("write", lambda *_: self.populate_requests_tree())
        ttk.Entry(req_top, textvariable=self.search_req_var, width=16).pack(side="right", padx=4)
        ttk.Label(req_top, text="🔍 Filtra:", style="Card.TLabel").pack(side="right")

        r_cols = ("id", "time", "method", "endpoint", "origin", "status", "latency", "bytes")
        self.req_tree = ttk.Treeview(req_card, columns=r_cols, show="headings", height=8)
        self.req_tree.heading("id", text="#")
        self.req_tree.heading("time", text="ORARIO")
        self.req_tree.heading("method", text="METODO")
        self.req_tree.heading("endpoint", text="ENDPOINT RICHIESTO")
        self.req_tree.heading("origin", text="CLIENT / ORIGINE")
        self.req_tree.heading("status", text="RISPOSTA")
        self.req_tree.heading("latency", text="TEMPO")
        self.req_tree.heading("bytes", text="PAYLOAD")

        self.req_tree.column("id", width=45, anchor="center")
        self.req_tree.column("time", width=80, anchor="center")
        self.req_tree.column("method", width=65, anchor="center")
        self.req_tree.column("endpoint", width=155, anchor="w")
        self.req_tree.column("origin", width=190, anchor="w")
        self.req_tree.column("status", width=85, anchor="center")
        self.req_tree.column("latency", width=65, anchor="center")
        self.req_tree.column("bytes", width=75, anchor="e")

        self.req_tree.tag_configure("ok", foreground="#4ade80")
        self.req_tree.tag_configure("warn", foreground="#fbbf24")
        self.req_tree.tag_configure("err", foreground="#f87171")

        self.req_tree.pack(fill="both", expand=True)
        self.req_tree.bind("<<TreeviewSelect>>", self._on_request_selected)

        # --- Pannello Destro: Visualizzatore Script di Risposta & Payload JSON ---
        script_card = ttk.Frame(mid_h_pane, style="Card.TFrame", padding=10)
        mid_h_pane.add(script_card, weight=3)

        script_top = ttk.Frame(script_card, style="Card.TFrame")
        script_top.pack(fill="x", pady=(0, 6))

        ttk.Label(
            script_top,
            text="📜 Script di Risposta & Payload Restituito al Client",
            style="CardTitle.TLabel"
        ).pack(side="left")

        mode_bar = ttk.Frame(script_card, style="Card.TFrame")
        mode_bar.pack(fill="x", pady=(0, 6))

        for lbl_txt, mode_val in [
            ("📦 Payload JSON Risposta", "PAYLOAD"),
            ("🐍 Script Python Handler", "PYTHON_SCRIPT"),
            ("🐘 Script Client PHP/JS", "CLIENT_SCRIPT"),
        ]:
            ttk.Radiobutton(
                mode_bar,
                text=lbl_txt,
                value=mode_val,
                variable=self.inspector_mode_var,
                command=self._update_inspector_view
            ).pack(side="left", padx=(0, 12))

        self.response_script_text = ScrolledText(
            script_card,
            height=9,
            bg=ThemeColors.BG_INPUT,
            fg=ThemeColors.FG_TEXT,
            font=("Consolas", 9),
            relief="flat",
            wrap="none"
        )
        self.response_script_text.pack(fill="both", expand=True)
        self.response_script_text.configure(state="disabled")

        # =====================================================================
        # 3. SEZIONE INFERIORE: CONSOLE LIVE DI ASCOLTO E RISPOSTA
        # =====================================================================
        console_card = ttk.Frame(main_v_pane, style="Card.TFrame", padding=10)
        main_v_pane.add(console_card, weight=2)

        console_top = ttk.Frame(console_card, style="Card.TFrame")
        console_top.pack(fill="x", pady=(0, 6))

        ttk.Label(
            console_top,
            text="🖥️ Console Listener in Tempo Reale (Ascolto Socket & Risposte HTTP/JSON)",
            style="CardTitle.TLabel"
        ).pack(side="left")

        ttk.Button(
            console_top,
            text="🧹 Pulisci Console",
            command=self.clear_listener_console
        ).pack(side="right", padx=(6, 0))

        ttk.Checkbutton(
            console_top,
            text="Auto-Scroll",
            style="Card.TCheckbutton",
            variable=self.auto_scroll_console_var
        ).pack(side="right", padx=6)

        self.console_text = ScrolledText(
            console_card,
            height=7,
            bg="#060b16",
            fg=ThemeColors.FG_TEXT,
            font=("Consolas", 9),
            relief="flat",
            state="disabled"
        )
        self.console_text.pack(fill="both", expand=True)

        self.console_text.tag_config("LISTEN", foreground="#38bdf8")
        self.console_text.tag_config("REQ_IN", foreground="#fbbf24")
        self.console_text.tag_config("RES_OUT", foreground="#4ade80")
        self.console_text.tag_config("WARN", foreground="#f59e0b")
        self.console_text.tag_config("ERROR", foreground="#f87171")
        self.console_text.tag_config("INFO", foreground="#cbd5e1")

    # =========================================================================
    # LOGICA DEL SERVER LISTENER HTTP (ASCOLTO E RISPOSTA ALLE RICHIESTE)
    # =========================================================================
    def build_health_payload(self, endpoint="/api/health", query_params=None):
        """
        Genera il payload reale di risposta con stato dei servizi, CPU, RAM, Disco e Porte.
        """
        services_clean = {}
        for key, info in self.app.services.items():
            raw_st = info.get("status")
            services_clean[key] = {
                "status": strip_ansi(raw_st) if raw_st is not None else "MODULO",
                "pid": info.get("pid"),
                "process": info.get("process", ""),
                "position": info.get("position", ""),
                "link": info.get("link", ""),
                "role": info.get("role", ""),
            }

        try:
            total_b, used_b, free_b = shutil.disk_usage(WEB_SERVER_DIR)
            disk_pct = round((used_b / total_b) * 100.0, 1) if total_b > 0 else 0.0
        except Exception:
            total_b, used_b, free_b, disk_pct = 0, 0, 0, 0.0

        ports_clean = {}
        for port, p_info in self.app.port_results.items():
            is_open, latency_ms, detail = p_info
            ports_clean[str(port)] = {
                "open": is_open,
                "latency_ms": latency_ms,
                "detail": detail,
            }

        metrics = self.app.system_metrics
        tot_ram = metrics.get("total_memory_mb", 0.0)
        used_ram = metrics.get("ram_usage", 0.0)
        free_ram = metrics.get("free_memory_mb", 0.0)
        ram_pct = round((used_ram / tot_ram) * 100.0, 1) if tot_ram > 0 else 0.0

        return {
            "ok": True,
            "server": "OcchioDiFalco Python Listener",
            "endpoint": endpoint,
            "query": query_params or {},
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "host": {
                "os": metrics.get("os_caption", "Windows"),
                "listener_pid": os.getpid(),
                "cpu_percent": round(metrics.get("cpu_usage", 0.0), 1),
                "ram_used_mb": round(used_ram, 2),
                "ram_total_mb": round(tot_ram, 2),
                "ram_free_mb": round(free_ram, 2),
                "ram_percent": ram_pct,
                "disk_used_gb": round(used_b / (1024 ** 3), 2),
                "disk_total_gb": round(total_b / (1024 ** 3), 2),
                "disk_free_gb": round(free_b / (1024 ** 3), 2),
                "disk_percent": disk_pct,
            },
            "services": services_clean,
            "ports": ports_clean,
        }

    def _create_request_handler(self):
        """Crea la classe handler collegata all'istanza di `RequestsTab`."""
        tab_ref = self

        class OcchioDiFalcoRequestHandler(BaseHTTPRequestHandler):
            def log_message(self, format_str, *args):
                # Disabilita il log su stderr standard perche' gestito dalla Console GUI
                pass

            def _send_cors_headers(self):
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Client-Service, X-Requested-With")
                self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")

            def do_OPTIONS(self):
                t0 = time.perf_counter()
                self.send_response(204)
                self._send_cors_headers()
                self.end_headers()
                elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
                tab_ref._record_client_transaction(
                    method="OPTIONS",
                    raw_path=self.path,
                    client_addr=f"{self.client_address[0]}:{self.client_address[1]}",
                    req_headers=dict(self.headers),
                    req_body="",
                    status_code=204,
                    res_payload={"cors_preflight": "OK"},
                    elapsed_ms=elapsed_ms
                )

            def do_GET(self):
                self._handle_http_request(method="GET")

            def do_POST(self):
                content_len = int(self.headers.get("Content-Length", 0) or 0)
                raw_body = self.rfile.read(content_len).decode("utf-8", errors="ignore") if content_len > 0 else ""
                self._handle_http_request(method="POST", raw_body=raw_body)

            def _handle_http_request(self, method="GET", raw_body=""):
                t0 = time.perf_counter()
                parsed_url = urllib.parse.urlparse(self.path)
                route = parsed_url.path.rstrip("/") or "/"
                query_params = {
                    k: v[0] if len(v) == 1 else v
                    for k, v in urllib.parse.parse_qs(parsed_url.query).items()
                }

                client_ip, client_port = self.client_address
                origin_hdr = (
                    self.headers.get("Referer")
                    or self.headers.get("Origin")
                    or self.headers.get("X-Client-Service")
                    or self.headers.get("User-Agent", "Client HTTP")
                )

                tab_ref.console_log(
                    f"[REQ <<] {method} {self.path} da {client_ip}:{client_port} | Origine: {origin_hdr}",
                    "REQ_IN"
                )

                status_code = 200
                if route in ("/", "/health", "/api/health"):
                    payload = tab_ref.build_health_payload(endpoint=route, query_params=query_params)
                elif route in ("/services", "/api/services"):
                    full = tab_ref.build_health_payload(endpoint=route, query_params=query_params)
                    payload = {
                        "ok": True,
                        "endpoint": route,
                        "timestamp": full["timestamp"],
                        "services": full["services"],
                    }
                elif route in ("/ports", "/api/ports"):
                    full = tab_ref.build_health_payload(endpoint=route, query_params=query_params)
                    payload = {
                        "ok": True,
                        "endpoint": route,
                        "timestamp": full["timestamp"],
                        "ports": full["ports"],
                    }
                elif route in ("/ping", "/api/ping"):
                    payload = {
                        "ok": True,
                        "status": "ONLINE",
                        "service": "OcchioDiFalco",
                        "pid": os.getpid(),
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    }
                elif route in ("/command", "/api/command"):
                    cmd_str = query_params.get("cmd", "")
                    if not cmd_str and raw_body:
                        try:
                            body_json = json.loads(raw_body)
                            cmd_str = body_json.get("cmd", "")
                        except Exception:
                            pass
                    clean_cmd = str(cmd_str).strip().lower()
                    if clean_cmd in CUSTOM_COMMANDS:
                        tab_ref.app.run_custom_command(clean_cmd)
                        payload = {
                            "ok": True,
                            "endpoint": route,
                            "executed_command": clean_cmd,
                            "target_service": CUSTOM_COMMANDS[clean_cmd]["service"],
                            "message": f"Comando '{clean_cmd}' avviato da OcchioDiFalco.",
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        }
                    else:
                        status_code = 400
                        payload = {
                            "ok": False,
                            "error": f"Comando non valido o non autorizzato: '{clean_cmd}'",
                            "allowed_commands": list(CUSTOM_COMMANDS.keys()),
                        }
                else:
                    status_code = 404
                    payload = {
                        "ok": False,
                        "error": f"Endpoint '{route}' non trovato su OcchioDiFalco Listener.",
                        "available_endpoints": [
                            "/api/health",
                            "/api/services",
                            "/api/ports",
                            "/api/ping",
                            "/api/command?cmd=<comando>",
                        ],
                    }

                body_bytes = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
                self.send_response(status_code)
                self._send_cors_headers()
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body_bytes)))
                self.end_headers()
                self.wfile.write(body_bytes)

                elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
                lvl = "RES_OUT" if status_code == 200 else "WARN"
                tab_ref.console_log(
                    f"[RES >>] HTTP {status_code} per {method} {route} ({len(body_bytes)} bytes in {elapsed_ms} ms)",
                    lvl
                )

                tab_ref._record_client_transaction(
                    method=method,
                    raw_path=self.path,
                    client_addr=f"{client_ip}:{client_port}",
                    req_headers=dict(self.headers),
                    req_body=raw_body,
                    status_code=status_code,
                    res_payload=payload,
                    elapsed_ms=elapsed_ms
                )

        return OcchioDiFalcoRequestHandler

    def start_listener(self, silent=False):
        """Avvia il server HTTP listener in un thread dedicato su 127.0.0.1:<porta>."""
        if self.is_listening and self.http_server is not None:
            if not silent:
                self.console_log("Il listener è già attivo e in ascolto.", "WARN")
            return

        host = self.host_var.get().strip() or DEFAULT_API_HOST
        raw_port = self.port_var.get().strip()
        if not raw_port.isdigit() or not (1024 <= int(raw_port) <= 65535):
            messagebox.showwarning("Porta non valida", "Inserisci una porta TCP valida tra 1024 e 65535 (es. 5050).")
            return
        port = int(raw_port)

        try:
            handler_cls = self._create_request_handler()
            self.http_server = ReusableThreadingHTTPServer((host, port), handler_cls)
            self.is_listening = True

            self.server_thread = threading.Thread(
                target=self.http_server.serve_forever,
                name="OcchioDiFalcoHTTPListener",
                daemon=True
            )
            self.server_thread.start()

            self.lbl_listener_badge.configure(
                text=f"●  IN ASCOLTO  ·  {host}:{port}",
                bg="#163d2b",
                fg="#86efac"
            )
            self.console_log(
                f"[LISTEN] Listener OcchioDiFalco avviato su http://{host}:{port} "
                f"(Endpoint: /api/health, /api/services, /api/ports, /api/command)",
                "LISTEN"
            )
            self.app.log_message(
                f"Listener Richieste Client attivo su http://{host}:{port}/api/health",
                "SUCCESS"
            )
        except Exception as exc:
            self.is_listening = False
            self.http_server = None
            self.lbl_listener_badge.configure(
                text="●  ERRORE PORTA",
                bg="#45202a",
                fg="#fda4af"
            )
            self.console_log(f"[ERROR] Impossibile avviare il listener su {host}:{port}: {exc}", "ERROR")
            self.app.log_message(f"Errore avvio listener su {host}:{port}: {exc}", "ERROR")

    def stop_listener(self):
        """Ferma il server HTTP listener attivo."""
        if not self.is_listening or self.http_server is None:
            self.console_log("Il listener è già fermo.", "INFO")
            return

        srv = self.http_server
        self.http_server = None
        self.is_listening = False

        def _shutdown_worker():
            try:
                srv.shutdown()
                srv.server_close()
            except Exception:
                pass

        threading.Thread(target=_shutdown_worker, daemon=True).start()

        self.lbl_listener_badge.configure(
            text="●  LISTENER FERMO",
            bg="#45202a",
            fg="#fda4af"
        )
        self.console_log("[LISTEN] Listener HTTP arrestato correttamente.", "WARN")
        self.app.log_message("Listener Richieste Client fermato.", "WARN")

    def simulate_client_request(self):
        """
        Simula una richiesta HTTP reale dal client `/occhio-di-falco/` verso il listener Python
        così da testare e visualizzare subito la richiesta, lo script di risposta e la console.
        """
        if not self.is_listening:
            self.start_listener(silent=True)
            time.sleep(0.15)

        host = self.host_var.get().strip() or DEFAULT_API_HOST
        port = self.port_var.get().strip() or str(DEFAULT_API_PORT)
        endpoint = self.endpoint_test_var.get().strip() or "/api/health"
        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint

        url = f"http://{host}:{port}{endpoint}"

        def _client_worker():
            try:
                req = urllib.request.Request(
                    url,
                    headers={
                        "Accept": "application/json",
                        "Referer": "http://127.0.0.1/occhio-di-falco/",
                        "X-Client-Service": "Server-Health-Checker (Test GUI)",
                        "User-Agent": "OcchioDiFalco-HealthChecker/1.0",
                    },
                    method="GET"
                )
                with urllib.request.urlopen(req, timeout=2.5) as resp:
                    _ = resp.read()
            except urllib.error.HTTPError as http_err:
                # Anche un 400/404 viene registrato dal listener nella tabella
                try:
                    _ = http_err.read()
                except Exception:
                    pass
            except Exception as exc:
                self.console_log(f"[ERROR] Richiesta di test fallita verso {url}: {exc}", "ERROR")

        threading.Thread(target=_client_worker, daemon=True).start()

    # =========================================================================
    # REGISTRAZIONE TRANSAZIONI, TABELLA RICHIESTE E ISPETTORE SCRIPT
    # =========================================================================
    def _record_client_transaction(
        self,
        method,
        raw_path,
        client_addr,
        req_headers,
        req_body,
        status_code,
        res_payload,
        elapsed_ms
    ):
        """Registra una richiesta intercettata e aggiorna la UI nel thread principale."""
        self.request_counter += 1
        req_id = self.request_counter
        ts_str = datetime.now().strftime("%H:%M:%S")
        origin = (
            req_headers.get("Referer")
            or req_headers.get("X-Client-Service")
            or req_headers.get("Origin")
            or client_addr
        )
        json_pretty = json.dumps(res_payload, indent=2, ensure_ascii=False)
        size_bytes = len(json_pretty.encode("utf-8"))

        record = {
            "id": req_id,
            "time": ts_str,
            "method": method,
            "endpoint": raw_path,
            "client_addr": client_addr,
            "origin": origin,
            "status_code": status_code,
            "latency_ms": elapsed_ms,
            "size_bytes": size_bytes,
            "req_headers": req_headers,
            "req_body": req_body,
            "res_json": json_pretty,
        }
        self.requests_history.append(record)

        def _update_ui():
            if not self.winfo_exists():
                return
            self.lbl_stats_counter.configure(
                text=f"Richieste ricevute: {len(self.requests_history)}  ·  Ultima: {ts_str} ({raw_path})"
            )
            self.populate_requests_tree(select_id=str(req_id))

        self._ui_queue.put(_update_ui)

    def populate_requests_tree(self, select_id=None):
        """Popola la tabella Treeview delle richieste client (dalla più recente)."""
        current_sel = self.req_tree.selection()
        chosen_id = select_id or (current_sel[0] if current_sel else None)

        for item in self.req_tree.get_children():
            self.req_tree.delete(item)

        q = self.search_req_var.get().strip().lower()
        for rec in reversed(self.requests_history):
            rid = str(rec["id"])
            status_str = f"{rec['status_code']} OK" if rec["status_code"] < 300 else f"HTTP {rec['status_code']}"
            searchable = f"#{rid} {rec['time']} {rec['method']} {rec['endpoint']} {rec['origin']} {status_str}".lower()
            if q and q not in searchable:
                continue

            if rec["status_code"] < 300:
                tag = "ok"
            elif rec["status_code"] < 500:
                tag = "warn"
            else:
                tag = "err"

            self.req_tree.insert(
                "",
                "end",
                iid=rid,
                values=(
                    f"#{rid}",
                    rec["time"],
                    rec["method"],
                    rec["endpoint"],
                    rec["origin"],
                    status_str,
                    f"{rec['latency_ms']} ms",
                    f"{rec['size_bytes']} B",
                ),
                tags=(tag,)
            )

        if chosen_id and self.req_tree.exists(chosen_id):
            self.req_tree.selection_set(chosen_id)
            self._update_inspector_view()
        else:
            children = self.req_tree.get_children()
            if children:
                self.req_tree.selection_set(children[0])
                self._update_inspector_view()

    def _on_request_selected(self, _event=None):
        self._update_inspector_view()

    def _update_inspector_view(self):
        """Aggiorna il pannello destro con il payload JSON della risposta o con gli script di risposta."""
        mode = self.inspector_mode_var.get()

        if mode == "PYTHON_SCRIPT":
            content = PYTHON_RESPONSE_SCRIPT_SOURCE
        elif mode == "CLIENT_SCRIPT":
            content = CLIENT_PHP_JS_SNIPPET
        else:
            sel = self.req_tree.selection()
            selected_record = None
            if sel:
                sel_id = int(sel[0])
                for rec in self.requests_history:
                    if rec["id"] == sel_id:
                        selected_record = rec
                        break

            if selected_record is not None:
                hdr_lines = "\n".join(f"  {k}: {v}" for k, v in selected_record["req_headers"].items())
                content = (
                    f"=== DETTAGLIO RICHIESTA CLIENT #{selected_record['id']} ({selected_record['time']}) ===\n"
                    f"Metodo & Endpoint : {selected_record['method']} {selected_record['endpoint']}\n"
                    f"Socket Client     : {selected_record['client_addr']}\n"
                    f"Origine / Referer : {selected_record['origin']}\n"
                    f"Stato Risposta    : HTTP {selected_record['status_code']} ({selected_record['latency_ms']} ms, {selected_record['size_bytes']} bytes)\n\n"
                    f"--- HEADERS RICHIESTA CLIENT ---\n{hdr_lines}\n\n"
                    f"--- PAYLOAD JSON DI RISPOSTA INVIATO AL CLIENT ---\n"
                    f"{selected_record['res_json']}\n"
                )
            else:
                live_preview = json.dumps(self.build_health_payload(), indent=2, ensure_ascii=False)
                content = (
                    "=== ANTEPRIMA LIVE PAYLOAD DI RISPOSTA (/api/health) ===\n"
                    "(Nessuna richiesta selezionata — clicca su '🧪 Simula Richiesta Client' o apri /occhio-di-falco/)\n\n"
                    f"{live_preview}\n"
                )

        self.response_script_text.configure(state="normal")
        self.response_script_text.delete("1.0", "end")
        self.response_script_text.insert("1.0", content)
        self.response_script_text.configure(state="disabled")

    def clear_requests_history(self):
        self.requests_history.clear()
        self.populate_requests_tree()
        self.lbl_stats_counter.configure(text="Richieste ricevute: 0  ·  Ultima: —")
        self._update_inspector_view()
        self.console_log("Storico tabella richieste ripulito.", "INFO")

    # =========================================================================
    # CONSOLE LIVE DEL LISTENER
    # =========================================================================
    def console_log(self, message, level="INFO"):
        """Scrive una riga con timestamp nella console dedicata del listener HTTP."""
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        line = f"[{ts}] {message}\n"

        def _append():
            if not self.winfo_exists():
                return
            self.console_text.configure(state="normal")
            self.console_text.insert("end", line, level)
            if self.auto_scroll_console_var.get():
                self.console_text.see("end")
            self.console_text.configure(state="disabled")

        if threading.current_thread() is threading.main_thread():
            _append()
        else:
            self._ui_queue.put(_append)

    def clear_listener_console(self):
        self.console_text.configure(state="normal")
        self.console_text.delete("1.0", "end")
        self.console_text.configure(state="disabled")
        self.console_log("Console listener ripulita.", "INFO")
