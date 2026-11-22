"""
Tab 3 - Monitor Porte & Struttura Servizi (Stile XAMPP con Valori Reali):
Verifica porte TCP locali (127.0.0.1:80, 127.0.0.1:443, 127.0.0.1:3306) tramite `socket`
ed esploratore interattivo della gerarchia cartelle e configurazioni reali.
"""

import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText

from .config import BASE_DIR, CMD_COMMANDS_DIR, WEB_SERVER_DIR, OBBIETTIVI_DIR, DEFAULT_API_PORT, strip_ansi
from .monitoring import check_local_port
from .styles import ThemeColors


class MonitorTab(ttk.Frame):
    """Scheda 3: Verifica porte locali via `socket` ed esplorazione struttura reale dello stack."""

    def __init__(self, parent, app):
        super().__init__(parent, padding=10)
        self.app = app
        self.custom_port_var = tk.StringVar(value="8080")
        self._build_ui()

    def _build_ui(self):
        # Sezione Superiore: Verifica Porte Locali tramite libreria `socket`
        port_card = ttk.Frame(self, style="Card.TFrame", padding=12)
        port_card.pack(fill="x", pady=(0, 10))

        port_header = ttk.Frame(port_card, style="Card.TFrame")
        port_header.pack(fill="x", pady=(0, 6))

        ttk.Label(
            port_header,
            text="🔌 Verifica Porte Locali via `socket` (127.0.0.1:80, 127.0.0.1:443, 127.0.0.1:3306)",
            style="CardTitle.TLabel"
        ).pack(side="left")

        custom_port_box = ttk.Frame(port_header, style="Card.TFrame")
        custom_port_box.pack(side="right")

        ttk.Label(custom_port_box, text="Test Porta Custom 127.0.0.1:", style="Card.TLabel").pack(side="left", padx=4)
        ttk.Entry(custom_port_box, textvariable=self.custom_port_var, width=8).pack(side="left", padx=4)
        ttk.Button(
            custom_port_box,
            text="Testa Porta",
            command=self.test_custom_port
        ).pack(side="left", padx=4)
        ttk.Button(
            custom_port_box,
            text="🔍 Scansiona Porte Standard",
            style="Primary.TButton",
            command=self.scan_standard_ports
        ).pack(side="left", padx=4)

        p_cols = ("endpoint", "service", "socket_status", "latency", "wmi_process", "config_source")
        self.ports_tree = ttk.Treeview(port_card, columns=p_cols, show="headings", height=4)
        self.ports_tree.heading("endpoint", text="ENDPOINT (HOST:PORT)")
        self.ports_tree.heading("service", text="SERVIZIO ASSOCIATO")
        self.ports_tree.heading("socket_status", text="STATO SOCKET")
        self.ports_tree.heading("latency", text="LATENZA")
        self.ports_tree.heading("wmi_process", text="PROCESSO WMI (PID)")
        self.ports_tree.heading("config_source", text="CONFIGURAZIONE REALE")

        self.ports_tree.column("endpoint", width=145, anchor="center")
        self.ports_tree.column("service", width=185, anchor="w")
        self.ports_tree.column("socket_status", width=150, anchor="center")
        self.ports_tree.column("latency", width=90, anchor="center")
        self.ports_tree.column("wmi_process", width=170, anchor="center")
        self.ports_tree.column("config_source", width=360, anchor="w")

        self.ports_tree.tag_configure("open", foreground="#4ade80")
        self.ports_tree.tag_configure("closed", foreground="#f87171")

        self.ports_tree.pack(fill="x")

        # Sezione Inferiore: Esploratore Gerarchia Cartelle Reali
        struct_pane = ttk.PanedWindow(self, orient="horizontal")
        struct_pane.pack(fill="both", expand=True)

        tree_frame = ttk.Frame(struct_pane, style="Card.TFrame", padding=10)
        struct_pane.add(tree_frame, weight=3)

        tree_top = ttk.Frame(tree_frame, style="Card.TFrame")
        tree_top.pack(fill="x", pady=(0, 6))
        ttk.Label(
            tree_top,
            text="📁 Gerarchia Reale Stack (`Servizi_UnaIdeaCrazy` & `OcchioDiFalcoWebServer`)",
            style="CardTitle.TLabel"
        ).pack(side="left")

        ttk.Button(
            tree_top,
            text="🔄 Ricarica Albero",
            command=self.populate_structure_tree
        ).pack(side="right", padx=3)

        f_cols = ("role", "equiv_xampp", "abs_path")
        self.struct_tree = ttk.Treeview(tree_frame, columns=f_cols, show="tree headings", height=11)
        self.struct_tree.heading("#0", text="ELEMENTO / CARTELLA / FILE")
        self.struct_tree.heading("role", text="RUOLO NELLO STACK")
        self.struct_tree.heading("equiv_xampp", text="EQUIVALENTE XAMPP")
        self.struct_tree.heading("abs_path", text="PERCORSO REALE SU DISCO")

        self.struct_tree.column("#0", width=250, anchor="w")
        self.struct_tree.column("role", width=210, anchor="w")
        self.struct_tree.column("equiv_xampp", width=140, anchor="w")
        self.struct_tree.column("abs_path", width=280, anchor="w")

        self.struct_tree.pack(fill="both", expand=True)
        self.struct_tree.bind("<<TreeviewSelect>>", self._on_structure_node_selected)

        struct_btn_bar = ttk.Frame(tree_frame, style="Card.TFrame")
        struct_btn_bar.pack(fill="x", pady=(8, 0))
        ttk.Button(
            struct_btn_bar,
            text="📂 Apri Elemento in Esplora File",
            command=self._open_selected_structure_path
        ).pack(side="left", padx=3)

        inspector_frame = ttk.Frame(struct_pane, style="Card.TFrame", padding=10)
        struct_pane.add(inspector_frame, weight=2)

        ttk.Label(
            inspector_frame,
            text="📄 Ispettore Configurazioni & File (`env.conf`, `httpd.conf`, `my.ini`, `php.ini`)",
            style="CardTitle.TLabel"
        ).pack(anchor="w", pady=(0, 6))

        self.struct_preview_text = ScrolledText(
            inspector_frame,
            height=14,
            bg=ThemeColors.BG_INPUT,
            fg=ThemeColors.FG_TEXT,
            font=("Consolas", 9),
            relief="flat"
        )
        self.struct_preview_text.pack(fill="both", expand=True)
        self.struct_preview_text.configure(state="disabled")

        self.populate_structure_tree()

    def update_ports_tree(self):
        for item in self.ports_tree.get_children():
            self.ports_tree.delete(item)

        ap_clean = strip_ansi(self.app.services["APACHE"]["status"])
        ap_pid = self.app.services["APACHE"]["pid"]
        my_clean = strip_ansi(self.app.services["MYSQL"]["status"])
        my_pid = self.app.services["MYSQL"]["pid"]

        cfg = self.app.real_configs
        port_specs = [
            (
                80,
                "Apache HTTP Server",
                f"httpd.exe ({ap_clean}, PID {ap_pid})",
                f"Apache24/conf/env.conf -> Listen {cfg['apache_host']}:{cfg['apache_port']}"
            ),
            (
                443,
                "Apache HTTPS / SSL",
                f"httpd.exe ({ap_clean}, PID {ap_pid})",
                "Porta standard HTTPS (443) — non abilitata in env.conf (solo porta 80)"
            ),
            (
                3306,
                "MySQL Server",
                f"mysqld.exe ({my_clean}, PID {my_pid})",
                f"mysql-26.10.0/my.ini -> port={cfg['mysql_port']}"
            ),
            (
                DEFAULT_API_PORT,
                "OcchioDiFalco Python API Listener",
                f"python.exe (ONLINE, PID {os.getpid()})",
                f"occhio_di_falco/tab_requests.py -> http://127.0.0.1:{DEFAULT_API_PORT}/api/health"
            ),
        ]

        for port, srv_name, wmi_info, cfg_src in port_specs:
            is_open, latency_ms, _msg = self.app.port_results.get(port, (False, 0.0, ""))
            status_txt = "🟢 APERTA (IN ASCOLTO)" if is_open else "🔴 CHIUSA / OFFLINE"
            tag = "open" if is_open else "closed"
            self.ports_tree.insert(
                "",
                "end",
                iid=str(port),
                values=(
                    f"127.0.0.1:{port}",
                    srv_name,
                    status_txt,
                    f"{latency_ms} ms",
                    wmi_info,
                    cfg_src
                ),
                tags=(tag,)
            )

    def scan_standard_ports(self):
        """Esegue una verifica immediata su 127.0.0.1:80, 443, 3306, 5050."""
        self.app.log_message(f"Avvio scansione socket su 127.0.0.1:80, 443, 3306, {DEFAULT_API_PORT}...", "CMD")

        def _worker():
            results = {}
            for p in (80, 443, 3306, DEFAULT_API_PORT):
                is_open, lat, detail = check_local_port("127.0.0.1", p)
                results[p] = (is_open, lat, detail)
                state_lbl = "APERTA" if is_open else "CHIUSA"
                lvl = "SUCCESS" if is_open else "WARN"
                self.app.log_message(f"Socket 127.0.0.1:{p} -> {state_lbl} ({lat} ms) | {detail}", lvl)

            def _apply():
                if not self.winfo_exists():
                    return
                self.app.port_results = results
                self.update_ports_tree()

            self.app.enqueue_ui(_apply)

        threading.Thread(target=_worker, daemon=True).start()

    def test_custom_port(self):
        raw = self.custom_port_var.get().strip()
        if not raw.isdigit() or not (1 <= int(raw) <= 65535):
            messagebox.showwarning("Porta non valida", "Inserisci un numero di porta TCP valido (1 - 65535).")
            return
        port = int(raw)
        is_open, lat, detail = check_local_port("127.0.0.1", port)
        lvl = "SUCCESS" if is_open else "WARN"
        state_str = "APERTA (IN ASCOLTO)" if is_open else "CHIUSA"
        self.app.log_message(f"Test porta custom 127.0.0.1:{port} -> {state_str} ({lat} ms) - {detail}", lvl)
        messagebox.showinfo(
            f"Verifica Socket 127.0.0.1:{port}",
            f"Endpoint: 127.0.0.1:{port}\nStato: {state_str}\nLatenza: {lat} ms\nDettaglio: {detail}"
        )

    def populate_structure_tree(self):
        for item in self.struct_tree.get_children():
            self.struct_tree.delete(item)

        apache_abs = os.path.abspath(os.path.join(BASE_DIR, self.app.services["APACHE"]["position"]))
        mysql_abs = os.path.abspath(os.path.join(BASE_DIR, self.app.services["MYSQL"]["position"]))
        php_abs = os.path.abspath(os.path.join(BASE_DIR, self.app.services["PHP"]["position"]))
        servizi_root = os.path.dirname(apache_abs)

        repo_node = self.struct_tree.insert(
            "", "end",
            text="📦 UnaIdeaCrazy (Repository Principale)",
            values=("Orchestratore, DocumentRoot & Script Batch", "xampp/ ( Control & htdocs )", BASE_DIR),
            open=True
        )

        docroot_node = self.struct_tree.insert(
            repo_node, "end",
            text="🌐 OcchioDiFalcoWebServer/",
            values=("DocumentRoot di Apache (definita in env.conf)", "htdocs/", WEB_SERVER_DIR),
            open=True
        )
        for sub_name, role_desc, xampp_eq in [
            ("index.php", "Landing page principale PHP (DirectoryIndex)", "htdocs/index.php"),
            (os.path.join("style-root", "landing.css"), "Foglio di stile CSS della landing page", "htdocs/style-root/landing.css"),
            ("occhio-di-falco", "Servizio #1: Server Health Checker & Telemetria", "htdocs/occhio-di-falco/"),
            ("my-cloud", "Servizio #2: My Cloud / FTP File Server", "htdocs/my-cloud/"),
            ("discovery-server", "Servizio #3: Discovery Server (Web Server Provider)", "htdocs/discovery-server/"),
            ("phpmyadmin", "phpMyAdmin 5.2.3 (Gestione MySQL via Web)", "htdocs/phpmyadmin/"),
        ]:
            sub_path = os.path.join(WEB_SERVER_DIR, sub_name)
            self.struct_tree.insert(
                docroot_node, "end",
                text=f"{'📁' if os.path.isdir(sub_path) else '📄'} {sub_name}",
                values=(role_desc, xampp_eq, sub_path)
            )

        pma_cfg = os.path.join(WEB_SERVER_DIR, "phpmyadmin", "config.inc.php")
        if os.path.exists(pma_cfg):
            self.struct_tree.insert(
                docroot_node, "end",
                text="⚙️ phpmyadmin/config.inc.php",
                values=("Configurazione phpMyAdmin", "phpmyadmin/config.inc.php", pma_cfg)
            )

        cmd_node = self.struct_tree.insert(
            repo_node, "end",
            text="⚡ CmdCommands/",
            values=("Script Batch eseguiti da execute_batch_command()", "xampp/*.bat", CMD_COMMANDS_DIR),
            open=True
        )
        for bat_f in ("sv_apache.bat", "stop_apache.bat", "sv_mysql.bat", "stop_mysql.bat"):
            bp = os.path.join(CMD_COMMANDS_DIR, bat_f)
            self.struct_tree.insert(
                cmd_node, "end",
                text=f"⚙️ {bat_f}",
                values=("Script avvio/arresto servizio", f"xampp/{bat_f}", bp)
            )

        self.struct_tree.insert(
            repo_node, "end",
            text="🐍 main.pyw",
            values=("Entrypoint principale OcchioDiFalco (GUI)", "xampp-control.exe", os.path.join(BASE_DIR, "main.pyw"))
        )
        self.struct_tree.insert(
            repo_node, "end",
            text="🧩 occhio_di_falco/",
            values=("Pacchetto Python modulare (GUI, servizi, monitoraggio)", "src/", os.path.join(BASE_DIR, "occhio_di_falco"))
        )
        self.struct_tree.insert(
            repo_node, "end",
            text="📘 readme.md",
            values=("Documentazione tecnica architettura e setup", "readme_it.txt", os.path.join(BASE_DIR, "readme.md"))
        )
        self.struct_tree.insert(
            repo_node, "end",
            text="🎯 Obbiettivi/",
            values=("Specifiche progettuali (OcchioDiFalco & My Cloud)", "docs/", OBBIETTIVI_DIR)
        )

        srv_root_node = self.struct_tree.insert(
            "", "end",
            text="🛠️ Servizi_UnaIdeaCrazy (Stack Portabile)",
            values=("Contenitore binari portabili (Apache, MySQL, PHP)", "xampp/ (apache, mysql, php)", servizi_root),
            open=True
        )

        ap_node = self.struct_tree.insert(
            srv_root_node, "end",
            text="🪶 Apache24/",
            values=("Apache HTTP Server 2.4 Win64", "apache/", apache_abs),
            open=True
        )
        for rel_p, desc_p, x_eq in [
            (os.path.join("bin", "httpd.exe"), "Binario server Apache monitorato via WMI", "apache/bin/httpd.exe"),
            (os.path.join("conf", "env.conf"), "Variabili locali (SRVROOT, DOCUMENT_ROOT, PHP_DIR, 127.0.0.1:80)", "apache/conf/extra/httpd-xampp.conf"),
            (os.path.join("conf", "httpd.conf"), "Configurazione principale Apache + LoadModule PHP", "apache/conf/httpd.conf"),
            ("logs", "Directory log di Apache (error_log, access_log)", "apache/logs/"),
            ("modules", "Moduli dinamici DSO (.so)", "apache/modules/"),
        ]:
            full_p = os.path.join(apache_abs, rel_p)
            icon = "📁" if os.path.isdir(full_p) else "📄"
            self.struct_tree.insert(ap_node, "end", text=f"{icon} {rel_p}", values=(desc_p, x_eq, full_p))

        my_node = self.struct_tree.insert(
            srv_root_node, "end",
            text="🐬 mysql-26.10.0/",
            values=("MySQL Community Server 26.10.0", "mysql/", mysql_abs),
            open=True
        )
        for rel_p, desc_p, x_eq in [
            (os.path.join("bin", "mysqld.exe"), "Demone MySQL Server monitorato via WMI", "mysql/bin/mysqld.exe"),
            ("my.ini", "Configurazione MySQL (basedir, datadir, port=3306)", "mysql/bin/my.ini"),
            ("data", "Directory fisica dei database MySQL", "mysql/data/"),
        ]:
            full_p = os.path.join(mysql_abs, rel_p)
            icon = "📁" if os.path.isdir(full_p) else "📄"
            self.struct_tree.insert(my_node, "end", text=f"{icon} {rel_p}", values=(desc_p, x_eq, full_p))

        php_node = self.struct_tree.insert(
            srv_root_node, "end",
            text="🐘 php-8.5.12x64/",
            values=("PHP 8.5.12 x64 Thread Safe (TS)", "php/", php_abs),
            open=True
        )
        for rel_p, desc_p, x_eq in [
            ("php8apache2_4.dll", "Modulo nativo caricato da Apache (LoadModule php_module)", "php/php8apache2_4.dll"),
            ("php.ini", "Configurazione PHP (extension_dir, mysqli, mbstring, openssl, zip)", "php/php.ini"),
            ("php.exe", "Interprete PHP CLI", "php/php.exe"),
            ("ext", "Estensioni dinamiche PHP (.dll)", "php/ext/"),
        ]:
            full_p = os.path.join(php_abs, rel_p)
            icon = "📁" if os.path.isdir(full_p) else "📄"
            self.struct_tree.insert(php_node, "end", text=f"{icon} {rel_p}", values=(desc_p, x_eq, full_p))

    def _on_structure_node_selected(self, _event=None):
        sel = self.struct_tree.selection()
        if not sel:
            return
        item_id = sel[0]
        item_text = self.struct_tree.item(item_id, "text")
        vals = self.struct_tree.item(item_id, "values")
        if not vals or len(vals) < 3:
            return
        role, xampp_eq, abs_path = vals[0], vals[1], vals[2]
        exists = os.path.exists(abs_path)

        header = (
            f"=== ISPEZIONE ELEMENTO ARCHITETTURA ===\n"
            f"Elemento          : {item_text}\n"
            f"Ruolo             : {role}\n"
            f"Equivalente XAMPP : {xampp_eq}\n"
            f"Percorso Reale    : {abs_path}\n"
            f"Stato sul Disco   : {'✔ Presente' if exists else '✖ Non trovato'}\n"
            f"{'─' * 62}\n"
        )

        body = ""
        if exists and os.path.isfile(abs_path):
            ext = os.path.splitext(abs_path)[1].lower()
            if ext in (".conf", ".ini", ".bat", ".php", ".html", ".md", ".txt", ".py"):
                try:
                    with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read(6000)
                    body = f"--- ANTEPRIMA CONTENUTO FILE ---\n{content}"
                except Exception as e:
                    body = f"Impossibile leggere il file: {e}"
            else:
                size_kb = os.path.getsize(abs_path) / 1024
                body = f"File binario/eseguibile ({size_kb:.1f} KB)."
        elif exists and os.path.isdir(abs_path):
            try:
                entries = os.listdir(abs_path)
                preview_items = entries[:35]
                formatted_items = "\n".join(
                    f"  {'[DIR] ' if os.path.isdir(os.path.join(abs_path, e)) else '[FILE]'} {e}"
                    for e in preview_items
                )
                body = f"Contenuto cartella ({len(entries)} elementi totali):\n{formatted_items}"
            except Exception as e:
                body = f"Impossibile elencare la cartella: {e}"

        self.struct_preview_text.configure(state="normal")
        self.struct_preview_text.delete("1.0", "end")
        self.struct_preview_text.insert("1.0", header + body)
        self.struct_preview_text.configure(state="disabled")

    def _open_selected_structure_path(self):
        sel = self.struct_tree.selection()
        if not sel:
            return
        vals = self.struct_tree.item(sel[0], "values")
        if vals and len(vals) >= 3:
            self.app.open_folder(vals[2])
