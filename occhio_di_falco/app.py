"""
Finestra principale `OcchioDiFalcoGUI(tk.Tk)`:
Coordina l'header, il `ttk.Notebook` con le 4 schede modulari,
il pannello di log scorrevole, la barra di stato e il ciclo di aggiornamento in background.
"""

import os
import time
import queue
import threading
import subprocess
import webbrowser
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText

from .config import (
    BASE_DIR,
    ASCII_logo_service,
    CUSTOM_COMMANDS,
    DEFAULT_API_PORT,
    strip_ansi,
    read_real_service_configs,
)
from .services import (
    get_process_status,
    build_services_status,
    execute_batch_command,
)
from .monitoring import get_system_metrics, check_local_port
from .styles import ThemeColors, apply_theme_styles
from .tab_overview import OverviewTab
from .tab_commands import CommandsTab
from .tab_monitor import MonitorTab
from .tab_requests import RequestsTab


class OcchioDiFalcoGUI(tk.Tk):
    """
    Applicazione Desktop GUI per UnaIdeaCrazy - OcchioDiFalco.
    Assembla i moduli separati mantenendo il 100% della logica di `main.py`.
    """

    def __init__(self):
        super().__init__()
        self.title("UnaIdeaCrazy — OcchioDiFalco & Stack Monitor (GUI)")
        self.geometry("1280x860")
        self.minsize(1080, 740)
        self.configure(bg=ThemeColors.BG_MAIN)

        # Stato iniziale
        ap_init = get_process_status("httpd.exe")
        my_init = get_process_status("mysqld.exe")
        self.services = build_services_status(ap_init, my_init)
        self.real_configs = read_real_service_configs()
        self.system_metrics = {
            "cpu_usage": 0.0,
            "total_memory_mb": 0.0,
            "free_memory_mb": 0.0,
            "ram_usage": 0.0,
            "os_caption": "Windows"
        }
        self.auto_refresh_var = tk.BooleanVar(value=True)
        self.wmi_hardware_var = tk.BooleanVar(value=True)
        self.is_refreshing = False
        self.port_results = {}
        self.last_user_input = ""
        self._app_ui_queue = queue.Queue()

        # Configurazione stili e componenti UI
        self.style = apply_theme_styles(self)
        self._build_header()
        self._build_notebook()
        self._build_log_and_statusbar()
        self._poll_app_ui_queue()

        # Avvio log, avvio automatico Listener HTTP e primo ciclo di lettura
        self.log_message("OcchioDiFalco GUI avviato con successo (architettura modulare).", "SUCCESS")
        self.log_message(
            f"Directory base progetto: {BASE_DIR} | PID OcchioDiFalco: {os.getpid()}",
            "INFO"
        )
        self.tab_requests.start_listener(silent=True)
        self.protocol("WM_DELETE_WINDOW", self._on_window_close)
        self.refresh_all_data(initial=True)
        self._schedule_auto_refresh()

    def enqueue_ui(self, callback):
        """Accoda una funzione da eseguire in modo thread-safe nel main loop di Tkinter."""
        if threading.current_thread() is threading.main_thread():
            try:
                callback()
            except Exception:
                pass
        else:
            self._app_ui_queue.put(callback)

    def _poll_app_ui_queue(self):
        try:
            while True:
                cb = self._app_ui_queue.get_nowait()
                try:
                    cb()
                except Exception:
                    pass
        except queue.Empty:
            pass
        if self.winfo_exists():
            self.after(100, self._poll_app_ui_queue)

    def _on_window_close(self):
        """Arresta il listener HTTP in background prima di chiudere la finestra GUI."""
        try:
            self.tab_requests.stop_listener()
        except Exception:
            pass
        self.destroy()

    # =========================================================================
    # HEADER SUPERIORE
    # =========================================================================
    def _build_header(self):
        header_frame = ttk.Frame(self, padding=(14, 8, 14, 4))
        header_frame.pack(fill="x")

        left_box = ttk.Frame(header_frame)
        left_box.pack(side="left", fill="x", expand=True)

        title_row = ttk.Frame(left_box)
        title_row.pack(fill="x")

        ttk.Label(
            title_row,
            text="🦅 OCCHIO DI FALCO — UnaIdeaCrazy",
            style="Header.TLabel"
        ).pack(side="left")

        self.mc_badge_lbl = tk.Label(
            title_row,
            text=f"●  ONLINE  ·  PID {os.getpid()}",
            bg="#163d2b",
            fg="#86efac",
            font=("Segoe UI", 9, "bold"),
            padx=8,
            pady=4
        )
        self.mc_badge_lbl.pack(side="left", padx=10)

        ascii_lbl = tk.Label(
            left_box,
            text=ASCII_logo_service.strip("\n"),
            bg=ThemeColors.BG_MAIN,
            fg="#f87171",
            font=("Consolas", 5),
            justify="left",
            anchor="w"
        )
        ascii_lbl.pack(fill="x", pady=(2, 0))

        right_box = ttk.Frame(header_frame)
        right_box.pack(side="right", anchor="ne")

        btn_row = ttk.Frame(right_box)
        btn_row.pack(anchor="e", pady=(0, 4))

        ttk.Button(
            btn_row,
            text="🔄 Aggiorna Stato",
            style="Primary.TButton",
            command=self.refresh_all_data
        ).pack(side="left", padx=3)

        ttk.Button(
            btn_row,
            text="🌐 Apri Localhost",
            command=lambda: self.open_url("http://127.0.0.1/")
        ).pack(side="left", padx=3)

        ttk.Button(
            btn_row,
            text="🗄️ Apri phpMyAdmin",
            command=lambda: self.open_url("http://127.0.0.1/phpmyadmin")
        ).pack(side="left", padx=3)

        ttk.Button(
            btn_row,
            text="❓ /help",
            command=self.show_help_command
        ).pack(side="left", padx=3)

        opt_row = ttk.Frame(right_box)
        opt_row.pack(anchor="e")

        ttk.Checkbutton(
            opt_row,
            text="Auto-Refresh (4s)",
            variable=self.auto_refresh_var
        ).pack(side="left", padx=6)

        ttk.Checkbutton(
            opt_row,
            text="Telemetria WMI (CPU/RAM)",
            variable=self.wmi_hardware_var
        ).pack(side="left", padx=6)

    # =========================================================================
    # NOTEBOOK CON LE 4 SCHEDE SEPARATE
    # =========================================================================
    def _build_notebook(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=14, pady=(4, 6))

        self.tab_overview = OverviewTab(self.notebook, app=self)
        self.notebook.add(
            self.tab_overview,
            text="📊 Tab 1 - Panoramica & Dati main.pyw"
        )

        self.tab_commands = CommandsTab(self.notebook, app=self)
        self.notebook.add(
            self.tab_commands,
            text="⚡ Tab 2 - Comandi Custom & Script Batch"
        )

        self.tab_monitor = MonitorTab(self.notebook, app=self)
        self.notebook.add(
            self.tab_monitor,
            text="🔍 Tab 3 - Monitor Porte & Struttura Servizi"
        )

        self.tab_requests = RequestsTab(self.notebook, app=self)
        self.notebook.add(
            self.tab_requests,
            text="📡 Tab 4 - Listener Richieste & Console Risposte"
        )

    # =========================================================================
    # PANNELLO DI LOG SCORREVOLE & BARRA DI STATO INFERIORE
    # =========================================================================
    def _build_log_and_statusbar(self):
        bottom_container = ttk.Frame(self, padding=(14, 0, 14, 10))
        bottom_container.pack(fill="x")

        log_card = ttk.Frame(bottom_container, style="Card.TFrame", padding=8)
        log_card.pack(fill="x")

        log_top = ttk.Frame(log_card, style="Card.TFrame")
        log_top.pack(fill="x", pady=(0, 4))

        ttk.Label(
            log_top,
            text="📜 Log Operazioni in Tempo Reale (Sola Lettura)",
            style="CardTitle.TLabel"
        ).pack(side="left")

        ttk.Button(
            log_top,
            text="🧹 Pulisci Log",
            command=self.clear_log
        ).pack(side="right")

        self.log_box = ScrolledText(
            log_card,
            height=6,
            bg=ThemeColors.BG_INPUT,
            fg=ThemeColors.FG_TEXT,
            font=("Consolas", 9),
            relief="flat",
            state="disabled"
        )
        self.log_box.pack(fill="x")

        self.log_box.tag_config("INFO", foreground="#cbd5e1")
        self.log_box.tag_config("SUCCESS", foreground="#4ade80")
        self.log_box.tag_config("WARN", foreground="#fbbf24")
        self.log_box.tag_config("ERROR", foreground="#f87171")
        self.log_box.tag_config("CMD", foreground="#38bdf8")

        status_bar = tk.Frame(bottom_container, bg="#020617", padx=10, pady=4)
        status_bar.pack(fill="x", pady=(6, 0))

        self.status_left_lbl = tk.Label(
            status_bar,
            text="Pronto.",
            bg="#020617",
            fg="#94a3b8",
            font=("Segoe UI", 9)
        )
        self.status_left_lbl.pack(side="left")

        self.status_right_lbl = tk.Label(
            status_bar,
            text="",
            bg="#020617",
            fg="#38bdf8",
            font=("Consolas", 9)
        )
        self.status_right_lbl.pack(side="right")

    # =========================================================================
    # FUNZIONI DI LOGGING, NAVIGAZIONE E COMANDI
    # =========================================================================
    def log_message(self, message, level="INFO"):
        """Aggiunge una riga con timestamp nel pannello ScrolledText in sola lettura."""
        ts = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{ts}] [{level}] {message}\n"

        def _append():
            if not self.winfo_exists():
                return
            self.log_box.configure(state="normal")
            self.log_box.insert("end", formatted, level)
            self.log_box.see("end")
            self.log_box.configure(state="disabled")
            self.status_left_lbl.configure(text=f"Ultima operazione ({ts}): {message[:110]}")

        if threading.current_thread() is threading.main_thread():
            _append()
        else:
            self.enqueue_ui(_append)

    def clear_log(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")
        self.log_message("Log ripulito.", "INFO")

    def open_url(self, url):
        if not url:
            return
        self.log_message(f"Apertura URL nel browser: {url}", "INFO")
        webbrowser.open(url)

    def open_folder(self, path):
        abs_p = os.path.abspath(path)
        if not os.path.exists(abs_p):
            messagebox.showwarning("Percorso non trovato", f"Il percorso non esiste sul disco:\n{abs_p}")
            self.log_message(f"Percorso non trovato: {abs_p}", "WARN")
            return
        self.log_message(f"Apertura percorso in Esplora File: {abs_p}", "INFO")
        if os.path.isfile(abs_p):
            subprocess.Popen(["explorer", "/select,", abs_p])
        else:
            os.startfile(abs_p)

    def show_help_command(self):
        """Stampa nel log la guida `/help` esattamente come nello script originale."""
        self.log_message("Lista comandi custom (/help):", "CMD")
        self.log_message("  /help - mostra questa lista", "INFO")
        for cmd, info in CUSTOM_COMMANDS.items():
            self.log_message(f"  {cmd} - {info['desc']} (processo: {info['process']})", "INFO")

    def run_custom_command(self, clean_input):
        """Esegue un comando di `CUSTOM_COMMANDS` in un thread dedicato e aggiorna lo stato."""
        if clean_input not in CUSTOM_COMMANDS:
            return
        cmd_info = CUSTOM_COMMANDS[clean_input]

        def _worker():
            execute_batch_command(clean_input, cmd_info["service"], self.services, log_callback=self.log_message)
            time.sleep(0.8)
            self.enqueue_ui(self.refresh_all_data)

        threading.Thread(target=_worker, daemon=True).start()

    def execute_user_input_command(self, raw_input=None):
        """
        Riproduce integralmente la logica di gestione di `user_input` del ciclo originale
        senza bloccare l'interfaccia grafica.
        """
        if raw_input is None:
            raw_input = self.tab_commands.cmd_entry_var.get()
        self.last_user_input = raw_input
        clean_input = raw_input.strip().lower()

        if not clean_input:
            return

        if clean_input in ("exit", "quit"):
            if messagebox.askyesno("Conferma Uscita", "Vuoi chiudere OcchioDiFalco?"):
                self.log_message("Exiting the program.", "INFO")
                self.destroy()
            return

        if clean_input == "/help":
            self.show_help_command()
            return

        if clean_input in CUSTOM_COMMANDS:
            self.run_custom_command(clean_input)
            return

        raw_cmd = raw_input.strip()
        self.log_message(f"Esecuzione comando di sistema: {raw_cmd}", "CMD")

        def _shell_worker():
            try:
                res = subprocess.run(
                    raw_cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    cwd=BASE_DIR
                )
                if res.stdout and res.stdout.strip():
                    for line in res.stdout.strip().splitlines():
                        self.log_message(line, "INFO")
                if res.stderr and res.stderr.strip():
                    for line in res.stderr.strip().splitlines():
                        self.log_message(line, "WARN")
                self.log_message(f"Comando terminato (codice {res.returncode}).", "SUCCESS")
            except Exception as e:
                self.log_message(f"Error executing command: {e}", "ERROR")

        threading.Thread(target=_shell_worker, daemon=True).start()

    # =========================================================================
    # CICLO DI AGGIORNAMENTO DATI IN TEMPO REALE
    # =========================================================================
    def _schedule_auto_refresh(self):
        if not self.winfo_exists():
            return
        if self.auto_refresh_var.get() and not self.is_refreshing:
            self.refresh_all_data(silent=True)
        self.after(4000, self._schedule_auto_refresh)

    def refresh_all_data(self, initial=False, silent=False):
        if self.is_refreshing:
            return
        self.is_refreshing = True
        use_wmi_hw = self.wmi_hardware_var.get()

        def _worker():
            try:
                ap_stat = get_process_status("httpd.exe")
                my_stat = get_process_status("mysqld.exe")
                new_services = build_services_status(ap_stat, my_stat)
                metrics = get_system_metrics(include_wmi_cpu=use_wmi_hw)
                configs = read_real_service_configs()

                p80 = check_local_port("127.0.0.1", 80)
                p443 = check_local_port("127.0.0.1", 443)
                p3306 = check_local_port("127.0.0.1", 3306)
                p5050 = check_local_port("127.0.0.1", DEFAULT_API_PORT)
                ports_data = {80: p80, 443: p443, 3306: p3306, DEFAULT_API_PORT: p5050}

                self.enqueue_ui(
                    lambda: self._apply_refreshed_data(
                        new_services, metrics, configs, ports_data, initial, silent
                    )
                )
            finally:
                self.is_refreshing = False

        threading.Thread(target=_worker, daemon=True).start()

    def _apply_refreshed_data(self, new_services, metrics, configs, ports_data, initial, silent):
        if not self.winfo_exists():
            return
        self.services = new_services
        self.system_metrics = metrics
        self.real_configs = configs
        self.port_results = ports_data

        # Aggiorna Scheda 1 (Panoramica) e Scheda 3 (Porte Socket)
        self.tab_overview.update_overview_ui(new_services, metrics)
        self.tab_monitor.update_ports_tree()

        ap_clean = strip_ansi(new_services["APACHE"]["status"])
        ap_pid = new_services["APACHE"]["pid"]
        my_clean = strip_ansi(new_services["MYSQL"]["status"])
        my_pid = new_services["MYSQL"]["pid"]
        cpu = metrics["cpu_usage"]
        ram_mb = metrics["ram_usage"]

        now_str = datetime.now().strftime("%H:%M:%S")
        self.status_right_lbl.configure(
            text=f"APACHE: {ap_clean} | MYSQL: {my_clean} | CPU: {cpu:.0f}% | RAM: {ram_mb / 1024:.2f} GB | Aggiornato: {now_str}"
        )

        if not silent and not initial:
            self.log_message(
                f"Stato aggiornato — APACHE: {ap_clean} (PID {ap_pid}), MYSQL: {my_clean} (PID {my_pid})",
                "INFO"
            )
