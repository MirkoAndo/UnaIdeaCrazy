"""
Definizione della palette colori e configurazione degli stili grafici `ttk.Style`.
"""

from tkinter import ttk


class ThemeColors:
    """Palette colori moderna (Dark/Slate ad alto contrasto)."""
    BG_MAIN = "#0f172a"       # Slate 900
    BG_CARD = "#1e293b"       # Slate 800
    BG_INPUT = "#0b1120"      # Slate 950
    FG_TEXT = "#f8fafc"       # Slate 50
    FG_MUTED = "#94a3b8"      # Slate 400
    ACCENT_BLUE = "#38bdf8"   # Sky 400
    ACCENT_GREEN = "#22c55e"  # Green 500
    ACCENT_RED = "#ef4444"    # Red 500
    ACCENT_AMBER = "#f59e0b"  # Amber 500
    BORDER_COLOR = "#334155"  # Slate 700


def apply_theme_styles(root):
    """Applica il tema moderno e tutti gli stili personalizzati a `ttk.Style`."""
    style = ttk.Style(root)
    if "clam" in style.theme_names():
        style.theme_use("clam")

    c = ThemeColors

    style.configure(".", background=c.BG_MAIN, foreground=c.FG_TEXT, font=("Segoe UI", 10))
    style.configure("TFrame", background=c.BG_MAIN)
    style.configure("Card.TFrame", background=c.BG_CARD, relief="flat")
    style.configure("TLabel", background=c.BG_MAIN, foreground=c.FG_TEXT, font=("Segoe UI", 10))
    style.configure("Card.TLabel", background=c.BG_CARD, foreground=c.FG_TEXT, font=("Segoe UI", 10))
    style.configure("Muted.TLabel", background=c.BG_CARD, foreground=c.FG_MUTED, font=("Segoe UI", 9))
    style.configure("Header.TLabel", background=c.BG_MAIN, foreground=c.ACCENT_BLUE, font=("Segoe UI", 13, "bold"))
    style.configure("CardTitle.TLabel", background=c.BG_CARD, foreground=c.ACCENT_BLUE, font=("Segoe UI", 11, "bold"))

    # Notebook (Schede)
    style.configure(
        "TNotebook",
        background=c.BG_MAIN,
        borderwidth=0,
        tabmargins=[4, 4, 4, 0]
    )
    style.configure(
        "TNotebook.Tab",
        background=c.BG_CARD,
        foreground=c.FG_MUTED,
        padding=[16, 8],
        font=("Segoe UI", 10, "bold"),
        borderwidth=0
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", "#0284c7"), ("active", "#334155")],
        foreground=[("selected", "#ffffff"), ("active", "#ffffff")]
    )

    # Pulsanti
    style.configure(
        "TButton",
        background="#334155",
        foreground=c.FG_TEXT,
        padding=[10, 5],
        font=("Segoe UI", 9, "bold"),
        borderwidth=0
    )
    style.map(
        "TButton",
        background=[("active", "#475569"), ("disabled", "#1e293b")],
        foreground=[("disabled", "#64748b")]
    )

    style.configure("Primary.TButton", background="#0284c7", foreground="#ffffff")
    style.map("Primary.TButton", background=[("active", "#0369a1")])

    style.configure("Success.TButton", background="#16a34a", foreground="#ffffff")
    style.map("Success.TButton", background=[("active", "#15803d")])

    style.configure("Danger.TButton", background="#dc2626", foreground="#ffffff")
    style.map("Danger.TButton", background=[("active", "#b91c1c")])

    style.configure("Warning.TButton", background="#d97706", foreground="#ffffff")
    style.map("Warning.TButton", background=[("active", "#b45309")])

    # Treeview
    style.configure(
        "Treeview",
        background=c.BG_INPUT,
        fieldbackground=c.BG_INPUT,
        foreground=c.FG_TEXT,
        rowheight=28,
        font=("Segoe UI", 9),
        borderwidth=0
    )
    style.configure(
        "Treeview.Heading",
        background="#334155",
        foreground="#ffffff",
        font=("Segoe UI", 9, "bold"),
        padding=[6, 5],
        relief="flat"
    )
    style.map(
        "Treeview",
        background=[("selected", "#0369a1")],
        foreground=[("selected", "#ffffff")]
    )

    # Entry & Combobox
    style.configure(
        "TEntry",
        fieldbackground=c.BG_INPUT,
        foreground=c.FG_TEXT,
        insertcolor=c.FG_TEXT,
        padding=5
    )
    style.configure(
        "TCombobox",
        fieldbackground=c.BG_INPUT,
        background="#334155",
        foreground=c.FG_TEXT,
        arrowcolor=c.FG_TEXT,
        padding=4
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", c.BG_INPUT)],
        foreground=[("readonly", c.FG_TEXT)],
        selectbackground=[("readonly", "#0369a1")],
        selectforeground=[("readonly", "#ffffff")]
    )

    # Checkbutton, Radiobutton & Progressbar
    style.configure(
        "TCheckbutton",
        background=c.BG_MAIN,
        foreground=c.FG_TEXT,
        font=("Segoe UI", 9)
    )
    style.map("TCheckbutton", background=[("active", c.BG_MAIN)])

    style.configure(
        "Card.TCheckbutton",
        background=c.BG_CARD,
        foreground=c.FG_TEXT,
        font=("Segoe UI", 9)
    )
    style.map("Card.TCheckbutton", background=[("active", c.BG_CARD)])

    style.configure(
        "TRadiobutton",
        background=c.BG_CARD,
        foreground=c.FG_TEXT,
        font=("Segoe UI", 9, "bold")
    )
    style.map(
        "TRadiobutton",
        background=[("active", c.BG_CARD)],
        foreground=[("selected", c.ACCENT_BLUE), ("active", "#ffffff")]
    )

    style.configure(
        "Horizontal.TProgressbar",
        troughcolor=c.BG_INPUT,
        background=c.ACCENT_BLUE,
        thickness=10
    )
    return style
