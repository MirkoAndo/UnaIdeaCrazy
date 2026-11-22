"""
Tab 1 - Panoramica & Dati `main.py`:
Controllo rapido dei servizi (Apache, MySQL) tramite card dedicate,
indicatori CPU/RAM, tabella interattiva `services_status` e anteprima `Occhio_di_falco_table`.
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText

from .config import BASE_DIR, strip_ansi
from .services import format_occhio_di_falco_table
from .styles import ThemeColors


class OverviewTab(ttk.Frame):
    """Scheda 1: Panoramica dei servizi con card individuali, telemetria CPU/RAM e tabella OcchioDiFalco."""

    def __init__(self, parent, app):
        super().__init__(parent, padding=10)
        self.app = app
        self.service_search_var = tk.StringVar()
        self._build_ui()

    def _build_ui(self):
        # =====================================================================
        # RIGA SUPERIORE: CARDS DEI SERVIZI (APACHE, MYSQL, RISORSE DI SISTEMA)
        # =====================================================================
        top_row = ttk.Frame(self)
        top_row.pack(fill="x", pady=(0, 10))

        # ---------------------------------------------------------------------
        # 1. CARD APACHE HTTP SERVER
        # ---------------------------------------------------------------------
        apache_card = ttk.Frame(top_row, style="Card.TFrame", padding=12)
        apache_card.pack(side="left", fill="both", expand=True, padx=(0, 6))

        ap_header = ttk.Frame(apache_card, style="Card.TFrame")
        ap_header.pack(fill="x", pady=(0, 6))

        ttk.Label(
            ap_header,
            text="🪶 Apache HTTP Server",
            style="CardTitle.TLabel"
        ).pack(side="left")

        self.lbl_apache_badge = tk.Label(
            ap_header,
            text="●  OFFLINE  ·  PID —",
            bg="#45202a",
            fg="#fda4af",
            font=("Segoe UI", 9, "bold"),
            padx=8,
            pady=4
        )
        self.lbl_apache_badge.pack(side="right")

        ap_meta = ttk.Frame(apache_card, style="Card.TFrame")
        ap_meta.pack(fill="x", pady=(0, 8))
        ttk.Label(
            ap_meta,
            text="Binario: httpd.exe  ·  Porta: 127.0.0.1:80",
            style="Muted.TLabel"
        ).pack(anchor="w")
        ttk.Label(
            ap_meta,
            text="DocRoot: OcchioDiFalcoWebServer  (PHP DSO)",
            style="Muted.TLabel"
        ).pack(anchor="w", pady=(1, 0))

        ap_actions = ttk.Frame(apache_card, style="Card.TFrame")
        ap_actions.pack(fill="x", pady=(4, 0))

        ttk.Button(
            ap_actions,
            text="▶ Avvia",
            style="Success.TButton",
            command=lambda: self.app.run_custom_command("sv apache")
        ).pack(side="left", fill="x", expand=True, padx=(0, 3))

        ttk.Button(
            ap_actions,
            text="⏹ Ferma",
            style="Danger.TButton",
            command=lambda: self.app.run_custom_command("stop apache")
        ).pack(side="left", fill="x", expand=True, padx=3)

        ttk.Button(
            ap_actions,
            text="🌐 Web",
            command=lambda: self.app.open_url("http://127.0.0.1/")
        ).pack(side="left", fill="x", expand=True, padx=3)

        ttk.Button(
            ap_actions,
            text="📂 File",
            command=self._open_apache_folder
        ).pack(side="left", fill="x", expand=True, padx=(3, 0))

        # ---------------------------------------------------------------------
        # 2. CARD MYSQL DATABASE SERVER
        # ---------------------------------------------------------------------
        mysql_card = ttk.Frame(top_row, style="Card.TFrame", padding=12)
        mysql_card.pack(side="left", fill="both", expand=True, padx=(0, 6))

        my_header = ttk.Frame(mysql_card, style="Card.TFrame")
        my_header.pack(fill="x", pady=(0, 6))

        ttk.Label(
            my_header,
            text="🐬 MySQL Database Server",
            style="CardTitle.TLabel"
        ).pack(side="left")

        self.lbl_mysql_badge = tk.Label(
            my_header,
            text="●  OFFLINE  ·  PID —",
            bg="#45202a",
            fg="#fda4af",
            font=("Segoe UI", 9, "bold"),
            padx=8,
            pady=4
        )
        self.lbl_mysql_badge.pack(side="right")

        my_meta = ttk.Frame(mysql_card, style="Card.TFrame")
        my_meta.pack(fill="x", pady=(0, 8))
        ttk.Label(
            my_meta,
            text="Binario: mysqld.exe  ·  Porta: 127.0.0.1:3306",
            style="Muted.TLabel"
        ).pack(anchor="w")
        ttk.Label(
            my_meta,
            text="Admin: phpMyAdmin 5.2.3  ·  Storage: data/",
            style="Muted.TLabel"
        ).pack(anchor="w", pady=(1, 0))

        my_actions = ttk.Frame(mysql_card, style="Card.TFrame")
        my_actions.pack(fill="x", pady=(4, 0))

        ttk.Button(
            my_actions,
            text="▶ Avvia",
            style="Success.TButton",
            command=lambda: self.app.run_custom_command("sv mysql")
        ).pack(side="left", fill="x", expand=True, padx=(0, 3))

        ttk.Button(
            my_actions,
            text="⏹ Ferma",
            style="Danger.TButton",
            command=lambda: self.app.run_custom_command("stop mysql")
        ).pack(side="left", fill="x", expand=True, padx=3)

        ttk.Button(
            my_actions,
            text="🗄️ Admin",
            command=lambda: self.app.open_url("http://127.0.0.1/phpmyadmin")
        ).pack(side="left", fill="x", expand=True, padx=3)

        ttk.Button(
            my_actions,
            text="📂 File",
            command=self._open_mysql_folder
        ).pack(side="left", fill="x", expand=True, padx=(3, 0))

        # ---------------------------------------------------------------------
        # 3. CARD RISORSE DI SISTEMA & HARDWARE
        # ---------------------------------------------------------------------
        sys_card = ttk.Frame(top_row, style="Card.TFrame", padding=12)
        sys_card.pack(side="left", fill="both", expand=True, padx=(0, 0))

        sys_header = ttk.Frame(sys_card, style="Card.TFrame")
        sys_header.pack(fill="x", pady=(0, 6))

        ttk.Label(
            sys_header,
            text="💻 Risorse & Hardware",
            style="CardTitle.TLabel"
        ).pack(side="left")

        self.lbl_os_name = ttk.Label(
            sys_header,
            text="OS: Windows",
            style="Muted.TLabel"
        )
        self.lbl_os_name.pack(side="right")

        # CPU bar
        cpu_row = ttk.Frame(sys_card, style="Card.TFrame")
        cpu_row.pack(fill="x", pady=2)
        ttk.Label(cpu_row, text="CPU:", style="Card.TLabel", width=5).pack(side="left")
        self.cpu_prog = ttk.Progressbar(cpu_row, orient="horizontal", mode="determinate", maximum=100)
        self.cpu_prog.pack(side="left", fill="x", expand=True, padx=6)
        self.lbl_cpu_val = ttk.Label(cpu_row, text="0.0 %", style="Card.TLabel", width=7, anchor="e")
        self.lbl_cpu_val.pack(side="right")

        # RAM bar
        ram_row = ttk.Frame(sys_card, style="Card.TFrame")
        ram_row.pack(fill="x", pady=2)
        ttk.Label(ram_row, text="RAM:", style="Card.TLabel", width=5).pack(side="left")
        self.ram_prog = ttk.Progressbar(ram_row, orient="horizontal", mode="determinate", maximum=100)
        self.ram_prog.pack(side="left", fill="x", expand=True, padx=6)
        self.lbl_ram_val = ttk.Label(ram_row, text="0.00 GB", style="Card.TLabel", width=14, anchor="e")
        self.lbl_ram_val.pack(side="right")

        sys_footer = ttk.Frame(sys_card, style="Card.TFrame")
        sys_footer.pack(fill="x", pady=(5, 0))
        ttk.Label(
            sys_footer,
            text=f"OcchioDiFalco: PID {os.getpid()}",
            style="Muted.TLabel"
        ).pack(side="left")
        ttk.Label(
            sys_footer,
            text="Host: 127.0.0.1",
            style="Muted.TLabel"
        ).pack(side="right")

        # =====================================================================
        # PARTE CENTRALE: TABELLA SERVICES_STATUS + ISPETTORE OCCHIO_DI_FALCO
        # =====================================================================
        mid_pane = ttk.PanedWindow(self, orient="horizontal")
        mid_pane.pack(fill="both", expand=True)

        tree_card = ttk.Frame(mid_pane, style="Card.TFrame", padding=10)
        mid_pane.add(tree_card, weight=3)

        filter_row = ttk.Frame(tree_card, style="Card.TFrame")
        filter_row.pack(fill="x", pady=(0, 6))
        ttk.Label(
            filter_row,
            text="Dizionario `services_status` (Dati in Tempo Reale)",
            style="CardTitle.TLabel"
        ).pack(side="left")

        self.service_search_var.trace_add("write", lambda *_: self.populate_services_tree())
        ttk.Entry(filter_row, textvariable=self.service_search_var, width=22).pack(side="right", padx=4)
        ttk.Label(filter_row, text="🔍 Filtra:", style="Card.TLabel").pack(side="right")

        cols = ("key", "status", "pid", "process", "position", "exists", "link")
        self.services_tree = ttk.Treeview(tree_card, columns=cols, show="headings", height=7)
        self.services_tree.heading("key", text="SERVIZIO")
        self.services_tree.heading("status", text="STATUS")
        self.services_tree.heading("pid", text="PID")
        self.services_tree.heading("process", text="PROCESSO / MODULO")
        self.services_tree.heading("position", text="POSITION (main.py)")
        self.services_tree.heading("exists", text="DISCO")
        self.services_tree.heading("link", text="LINK WEB")

        self.services_tree.column("key", width=120, anchor="w")
        self.services_tree.column("status", width=95, anchor="center")
        self.services_tree.column("pid", width=70, anchor="center")
        self.services_tree.column("process", width=130, anchor="w")
        self.services_tree.column("position", width=215, anchor="w")
        self.services_tree.column("exists", width=75, anchor="center")
        self.services_tree.column("link", width=165, anchor="w")

        self.services_tree.tag_configure("online", foreground="#4ade80")
        self.services_tree.tag_configure("offline", foreground="#f87171")
        self.services_tree.tag_configure("module", foreground="#38bdf8")

        self.services_tree.pack(fill="both", expand=True)
        self.services_tree.bind("<<TreeviewSelect>>", self._on_service_selected)

        srv_actions = ttk.Frame(tree_card, style="Card.TFrame")
        srv_actions.pack(fill="x", pady=(8, 0))
        ttk.Button(
            srv_actions,
            text="📂 Apri Posizione in Esplora File",
            command=self._open_selected_service_folder
        ).pack(side="left", padx=3)
        ttk.Button(
            srv_actions,
            text="🌐 Apri Link Web Associato",
            command=self._open_selected_service_link
        ).pack(side="left", padx=3)

        # Pannello di dettaglio + anteprima `Occhio_di_falco_table`
        detail_card = ttk.Frame(mid_pane, style="Card.TFrame", padding=10)
        mid_pane.add(detail_card, weight=2)

        ttk.Label(
            detail_card,
            text="Ispettore Servizio & Tabella `Occhio_di_falco_table`",
            style="CardTitle.TLabel"
        ).pack(anchor="w", pady=(0, 6))

        self.service_detail_text = ScrolledText(
            detail_card,
            height=14,
            bg=ThemeColors.BG_INPUT,
            fg=ThemeColors.FG_TEXT,
            font=("Consolas", 9),
            relief="flat",
            wrap="none"
        )
        self.service_detail_text.pack(fill="both", expand=True)
        self.service_detail_text.configure(state="disabled")

    def update_overview_ui(self, services, metrics):
        """Aggiorna badge delle card, indicatori CPU/RAM e tabella dei servizi."""
        ap_clean = strip_ansi(services["APACHE"]["status"])
        ap_pid = services["APACHE"]["pid"]
        if "ONLINE" in ap_clean:
            self.lbl_apache_badge.configure(
                text=f"●  ONLINE  ·  PID {ap_pid}",
                bg="#163d2b", fg="#86efac", font=("Segoe UI", 9, "bold"),
                padx=8, pady=4
            )
        else:
            self.lbl_apache_badge.configure(
                text="●  OFFLINE  ·  PID —",
                bg="#45202a", fg="#fda4af", font=("Segoe UI", 9, "bold"),
                padx=8, pady=4
            )

        my_clean = strip_ansi(services["MYSQL"]["status"])
        my_pid = services["MYSQL"]["pid"]
        if "ONLINE" in my_clean:
            self.lbl_mysql_badge.configure(
                text=f"●  ONLINE  ·  PID {my_pid}",
                bg="#163d2b", fg="#86efac", font=("Segoe UI", 9, "bold"),
                padx=8, pady=4
            )
        else:
            self.lbl_mysql_badge.configure(
                text="●  OFFLINE  ·  PID —",
                bg="#45202a", fg="#fda4af", font=("Segoe UI", 9, "bold"),
                padx=8, pady=4
            )

        cpu = metrics["cpu_usage"]
        ram_mb = metrics["ram_usage"]
        tot_mb = metrics["total_memory_mb"]
        ram_pct = (ram_mb / tot_mb * 100.0) if tot_mb > 0 else 0.0

        self.lbl_os_name.configure(text=f"OS: {metrics['os_caption']}")
        self.cpu_prog["value"] = min(max(cpu, 0.0), 100.0)
        self.lbl_cpu_val.configure(text=f"{cpu:.1f} %")

        self.ram_prog["value"] = min(max(ram_pct, 0.0), 100.0)
        self.lbl_ram_val.configure(text=f"{ram_mb / 1024:.2f} / {tot_mb / 1024:.1f} GB ({ram_pct:.0f}%)")

        self.populate_services_tree()

    def populate_services_tree(self):
        selected = self.services_tree.selection()
        selected_key = selected[0] if selected else None

        for item in self.services_tree.get_children():
            self.services_tree.delete(item)

        query = self.service_search_var.get().strip().lower()
        for key, info in self.app.services.items():
            status_clean = strip_ansi(info["status"])
            pid_str = str(info["pid"])
            pos = info.get("position", "")
            proc = info.get("process", "")
            link = info.get("link", "")

            abs_pos = BASE_DIR if pos == "localset" else os.path.abspath(os.path.join(BASE_DIR, pos))
            exists_str = "✔ OK" if os.path.exists(abs_pos) else "✖ Assente"

            searchable = f"{key} {status_clean} {pid_str} {proc} {pos} {link}".lower()
            if query and query not in searchable:
                continue

            if "ONLINE" in status_clean:
                tag = "online"
            elif info["status"] is None:
                tag = "module"
            else:
                tag = "offline"

            self.services_tree.insert(
                "",
                "end",
                iid=key,
                values=(key, status_clean, pid_str, proc, pos, exists_str, link or "-"),
                tags=(tag,)
            )

        if selected_key and self.services_tree.exists(selected_key):
            self.services_tree.selection_set(selected_key)
            self._update_service_detail(selected_key)
        else:
            children = self.services_tree.get_children()
            if children:
                self.services_tree.selection_set(children[0])
                self._update_service_detail(children[0])

    def _on_service_selected(self, _event=None):
        sel = self.services_tree.selection()
        if sel:
            self._update_service_detail(sel[0])

    def _update_service_detail(self, service_key):
        info = self.app.services.get(service_key, {})
        pos = info.get("position", "")
        abs_pos = BASE_DIR if pos == "localset" else os.path.abspath(os.path.join(BASE_DIR, pos))
        status_clean = strip_ansi(info.get("status"))

        table_preview = format_occhio_di_falco_table(
            self.app.services,
            self.app.system_metrics["cpu_usage"],
            self.app.system_metrics["ram_usage"]
        )

        detail_str = (
            f"=== DETTAGLIO SERVIZIO: {service_key} ===\n"
            f"Ruolo        : {info.get('role', '-')}\n"
            f"Stato        : {status_clean}\n"
            f"PID          : {info.get('pid')}\n"
            f"Processo     : {info.get('process', '-')}\n"
            f"Position Rel : {pos}\n"
            f"Percorso Abs : {abs_pos}\n"
            f"Esiste Disco : {'Sì' if os.path.exists(abs_pos) else 'No'}\n"
            f"Link Web     : {info.get('link') or 'Nessuno'}\n\n"
            f"=== ANTEPRIMA OCCHIO_DI_FALCO_TABLE (main.py) ===\n"
            f"{table_preview}\n"
        )

        self.service_detail_text.configure(state="normal")
        self.service_detail_text.delete("1.0", "end")
        self.service_detail_text.insert("1.0", detail_str)
        self.service_detail_text.configure(state="disabled")

    def _open_apache_folder(self):
        pos = self.app.services.get("APACHE", {}).get("position", "")
        target = BASE_DIR if pos == "localset" else os.path.abspath(os.path.join(BASE_DIR, pos))
        self.app.open_folder(target)

    def _open_mysql_folder(self):
        pos = self.app.services.get("MYSQL", {}).get("position", "")
        target = BASE_DIR if pos == "localset" else os.path.abspath(os.path.join(BASE_DIR, pos))
        self.app.open_folder(target)

    def _open_selected_service_folder(self):
        sel = self.services_tree.selection()
        if not sel:
            return
        key = sel[0]
        pos = self.app.services[key].get("position", "")
        target = BASE_DIR if pos == "localset" else os.path.abspath(os.path.join(BASE_DIR, pos))
        self.app.open_folder(target)

    def _open_selected_service_link(self):
        sel = self.services_tree.selection()
        if not sel:
            return
        key = sel[0]
        link = self.app.services[key].get("link", "")
        if link:
            self.app.open_url(link)
        else:
            messagebox.showinfo("Nessun Link Web", f"Il servizio '{key}' non ha un URL HTTP associato.")
