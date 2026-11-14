"""
Tab 2 - Comandi Custom & Script Batch (`CmdCommands`):
Console interattiva sostitutiva di `input()`, catalogo `CUSTOM_COMMANDS`
con filtri di ricerca e ispettore del codice sorgente dei file `.bat`.
"""

import os
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

from .config import BASE_DIR, CMD_COMMANDS_DIR, CUSTOM_COMMANDS
from .styles import ThemeColors


class CommandsTab(ttk.Frame):
    """Scheda 2: Gestione ed esecuzione comandi custom, script .bat e comandi di sistema."""

    def __init__(self, parent, app):
        super().__init__(parent, padding=10)
        self.app = app
        self.cmd_entry_var = tk.StringVar(value="/help")
        self.cmd_filter_service_var = tk.StringVar(value="TUTTI")
        self.cmd_search_var = tk.StringVar()
        self._build_ui()

    def _build_ui(self):
        # Barra di esecuzione comando interattiva
        exec_card = ttk.Frame(self, style="Card.TFrame", padding=12)
        exec_card.pack(fill="x", pady=(0, 10))

        ttk.Label(
            exec_card,
            text="Console Comandi Interattiva (Sostituisce `user_input = input(...)`)",
            style="CardTitle.TLabel"
        ).pack(anchor="w", pady=(0, 6))

        cmd_bar = ttk.Frame(exec_card, style="Card.TFrame")
        cmd_bar.pack(fill="x")

        ttk.Label(cmd_bar, text="Comando:", style="Card.TLabel").pack(side="left", padx=(0, 6))

        preset_cmds = ["/help"] + list(CUSTOM_COMMANDS.keys()) + [
            "tasklist /FI \"IMAGENAME eq httpd.exe\"",
            "tasklist /FI \"IMAGENAME eq mysqld.exe\"",
            "exit"
        ]
        self.cmd_combo = ttk.Combobox(cmd_bar, textvariable=self.cmd_entry_var, values=preset_cmds, width=42)
        self.cmd_combo.pack(side="left", padx=(0, 8), fill="x", expand=True)
        self.cmd_combo.bind("<Return>", lambda _e: self.app.execute_user_input_command(self.cmd_entry_var.get()))

        ttk.Button(
            cmd_bar,
            text="▶ Esegui Comando",
            style="Primary.TButton",
            command=lambda: self.app.execute_user_input_command(self.cmd_entry_var.get())
        ).pack(side="left", padx=4)

        ttk.Button(
            cmd_bar,
            text="📖 Mostra /help",
            command=self.app.show_help_command
        ).pack(side="left", padx=4)

        ttk.Button(
            cmd_bar,
            text="📂 Apri Cartella CmdCommands",
            command=lambda: self.app.open_folder(CMD_COMMANDS_DIR)
        ).pack(side="left", padx=4)

        # Pannello diviso: Tabella CUSTOM_COMMANDS + Ispettore file .bat
        cmd_pane = ttk.PanedWindow(self, orient="horizontal")
        cmd_pane.pack(fill="both", expand=True)

        left_cmd = ttk.Frame(cmd_pane, style="Card.TFrame", padding=10)
        cmd_pane.add(left_cmd, weight=3)

        filter_bar = ttk.Frame(left_cmd, style="Card.TFrame")
        filter_bar.pack(fill="x", pady=(0, 6))
        ttk.Label(
            filter_bar,
            text="Catalogo `CUSTOM_COMMANDS` & Comandi di Sistema",
            style="CardTitle.TLabel"
        ).pack(side="left")

        srv_cb = ttk.Combobox(
            filter_bar,
            textvariable=self.cmd_filter_service_var,
            values=["TUTTI", "APACHE", "MYSQL", "SISTEMA"],
            state="readonly",
            width=12
        )
        srv_cb.pack(side="right", padx=4)
        srv_cb.bind("<<ComboboxSelected>>", lambda _e: self.populate_commands_tree())

        self.cmd_search_var.trace_add("write", lambda *_: self.populate_commands_tree())
        ttk.Entry(filter_bar, textvariable=self.cmd_search_var, width=18).pack(side="right", padx=4)
        ttk.Label(filter_bar, text="🔍 Cerca:", style="Card.TLabel").pack(side="right")

        c_cols = ("cmd", "service", "desc", "process", "bat_file", "exists")
        self.commands_tree = ttk.Treeview(left_cmd, columns=c_cols, show="headings", height=10)
        self.commands_tree.heading("cmd", text="COMANDO")
        self.commands_tree.heading("service", text="SERVIZIO")
        self.commands_tree.heading("desc", text="DESCRIZIONE")
        self.commands_tree.heading("process", text="PROCESSO TARGET")
        self.commands_tree.heading("bat_file", text="SCRIPT BATCH")
        self.commands_tree.heading("exists", text="STATO .BAT")

        self.commands_tree.column("cmd", width=110, anchor="w")
        self.commands_tree.column("service", width=90, anchor="center")
        self.commands_tree.column("desc", width=165, anchor="w")
        self.commands_tree.column("process", width=110, anchor="center")
        self.commands_tree.column("bat_file", width=140, anchor="w")
        self.commands_tree.column("exists", width=90, anchor="center")

        self.commands_tree.pack(fill="both", expand=True)
        self.commands_tree.bind("<<TreeviewSelect>>", self._on_command_selected)
        self.commands_tree.bind("<Double-1>", lambda _e: self._run_selected_tree_command())

        btn_cmd_bar = ttk.Frame(left_cmd, style="Card.TFrame")
        btn_cmd_bar.pack(fill="x", pady=(8, 0))
        ttk.Button(
            btn_cmd_bar,
            text="▶ Esegui Comando Selezionato",
            style="Success.TButton",
            command=self._run_selected_tree_command
        ).pack(side="left", padx=3)

        right_cmd = ttk.Frame(cmd_pane, style="Card.TFrame", padding=10)
        cmd_pane.add(right_cmd, weight=2)

        ttk.Label(
            right_cmd,
            text="Ispezione Script Batch (`CmdCommands/*.bat`) & Variabili",
            style="CardTitle.TLabel"
        ).pack(anchor="w", pady=(0, 6))

        self.bat_preview_text = ScrolledText(
            right_cmd,
            height=14,
            bg=ThemeColors.BG_INPUT,
            fg=ThemeColors.FG_TEXT,
            font=("Consolas", 9),
            relief="flat"
        )
        self.bat_preview_text.pack(fill="both", expand=True)
        self.bat_preview_text.configure(state="disabled")

        self.populate_commands_tree()

    def populate_commands_tree(self):
        for item in self.commands_tree.get_children():
            self.commands_tree.delete(item)

        search_q = self.cmd_search_var.get().strip().lower()
        srv_filter = self.cmd_filter_service_var.get()

        all_rows = []
        for cmd, info in CUSTOM_COMMANDS.items():
            bat_name = f"{cmd.replace(' ', '_')}.bat"
            bat_path = os.path.join(CMD_COMMANDS_DIR, bat_name)
            exists = "✔ Presente" if os.path.exists(bat_path) else "✖ Mancante"
            all_rows.append((cmd, info["service"], info["desc"], info["process"], bat_name, exists))

        all_rows.append(("/help", "SISTEMA", "mostra la lista dei comandi custom", "MissionControlGUI", "-", "Integrato"))
        all_rows.append(("exit / quit", "SISTEMA", "chiude l'applicazione Mission Control", "MissionControlGUI", "-", "Integrato"))

        for row in all_rows:
            cmd, srv, desc, proc, bat_name, exists = row
            if srv_filter != "TUTTI" and srv != srv_filter:
                continue
            if search_q and search_q not in f"{cmd} {srv} {desc} {proc} {bat_name}".lower():
                continue
            self.commands_tree.insert("", "end", iid=cmd, values=row)

        children = self.commands_tree.get_children()
        if children:
            self.commands_tree.selection_set(children[0])
            self._on_command_selected()

    def _on_command_selected(self, _event=None):
        sel = self.commands_tree.selection()
        if not sel:
            return
        cmd = sel[0]
        self.cmd_entry_var.set("exit" if cmd == "exit / quit" else cmd)

        if cmd in CUSTOM_COMMANDS:
            info = CUSTOM_COMMANDS[cmd]
            srv_key = info["service"]
            srv_pos = self.app.services.get(srv_key, {}).get("position", "")
            srv_abs = os.path.abspath(os.path.join(BASE_DIR, srv_pos))
            bat_name = f"{cmd.replace(' ', '_')}.bat"
            bat_path = os.path.join(CMD_COMMANDS_DIR, bat_name)
            bat_content = "File .bat non trovato."
            if os.path.exists(bat_path):
                try:
                    with open(bat_path, "r", encoding="utf-8", errors="ignore") as f:
                        bat_content = f.read()
                except Exception as e:
                    bat_content = f"Errore lettura file: {e}"

            preview = (
                f"=== COMANDO CUSTOM: '{cmd}' ===\n"
                f"Servizio Target    : {srv_key}\n"
                f"Descrizione        : {info['desc']}\n"
                f"Processo Monitorato: {info['process']}\n"
                f"File Batch         : {bat_path}\n\n"
                f"=== PARAMETRI PASSATI DA execute_batch_command() ===\n"
                f"Argomento %1       : \"{srv_abs}\"\n"
                f"SERVICE_POSITION   : \"{srv_abs}\"\n"
                f"SERVICE_NAME       : \"{srv_key}\"\n\n"
                f"=== CONTENUTO REALE DI {bat_name} ===\n"
                f"{bat_content}\n"
            )
        elif cmd == "/help":
            lines = ["Lista comandi custom:", "  /help - mostra questa lista"]
            for k, v in CUSTOM_COMMANDS.items():
                lines.append(f"  {k} - {v['desc']}")
            preview = "=== COMANDO INTEGRATO: /help ===\n\n" + "\n".join(lines)
        else:
            preview = (
                "=== COMANDO INTEGRATO: exit / quit ===\n\n"
                "Termina l'esecuzione di Mission Control (equivalente a `if clean_input in ('exit', 'quit'): break`)."
            )

        self.bat_preview_text.configure(state="normal")
        self.bat_preview_text.delete("1.0", "end")
        self.bat_preview_text.insert("1.0", preview)
        self.bat_preview_text.configure(state="disabled")

    def _run_selected_tree_command(self):
        sel = self.commands_tree.selection()
        if not sel:
            return
        cmd = sel[0]
        if cmd == "exit / quit":
            cmd = "exit"
        self.cmd_entry_var.set(cmd)
        self.app.execute_user_input_command(cmd)
