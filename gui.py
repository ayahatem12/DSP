"""Tkinter GUI for the DSP Signal Lab."""

import os
import math
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from Signal_Operations import (
    read_signal,
    add_signals,
    multiply_signal,
    subtract_signals,
    shift_signal,
    fold_signal,
)

# ---------- theme ----------
BG = "#0f1117"
PANEL = "#171a23"
CARD = "#1f2330"
SOFT = "#2a2f40"
SOFT_HOVER = "#353b50"
TEXT = "#e8eaf2"
MUTED = "#8c92a8"
ACCENT = "#7c5cff"
ACCENT_HOVER = "#957bff"
ACCENT_DARK = "#6246d8"
DANGER = "#fb7185"
SUCCESS = "#2dd4bf"
PLOT_COLORS = ["#7c5cff", "#2dd4bf", "#fb7185", "#fbbf24", "#60a5fa", "#a3e635"]
FONT = "Segoe UI"


class SignalApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Signal Lab — DSP Framework")
        self.root.geometry("1180x740")
        self.root.minsize(980, 640)
        self.root.configure(bg=BG)

        # Each item is (display name, (indices, samples)).
        self.signals = []

        self.setup_style()
        self.build_menu()
        self.build_header()
        self.build_status_bar()
        self.build_body()
        self.draw_empty()

    def build_menu(self):
        """Create the application menu, including the required Signal Generation menu."""
        menu_bar = tk.Menu(self.root, bg=PANEL, fg=TEXT, activebackground=ACCENT,
                           activeforeground="white", tearoff=False)
        file_menu = tk.Menu(menu_bar, tearoff=False, bg=PANEL, fg=TEXT,
                            activebackground=ACCENT, activeforeground="white")
        file_menu.add_command(label="Load signal from file...", command=self.load_signal)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.destroy)
        menu_bar.add_cascade(label="File", menu=file_menu)

        generation_menu = tk.Menu(menu_bar, tearoff=False, bg=PANEL, fg=TEXT,
                                  activebackground=ACCENT, activeforeground="white")
        generation_menu.add_command(label="Generate signal...", command=self.open_signal_generator)
        menu_bar.add_cascade(label="Signal Generation", menu=generation_menu)

        help_menu = tk.Menu(menu_bar, tearoff=False, bg=PANEL, fg=TEXT,
                            activebackground=ACCENT, activeforeground="white")
        help_menu.add_command(label="About", command=lambda: messagebox.showinfo(
            "About Signal Lab",
            "Signal Lab — DSP Task 1 and Task 2\n\n"
            "Generate sine/cosine signals and perform basic signal operations.\n"
            "Phase shift is entered in radians. Sampling must satisfy Fs >= 2f; equality is the Nyquist boundary."
        ))
        menu_bar.add_cascade(label="Help", menu=help_menu)
        self.root.config(menu=menu_bar)

    def open_signal_generator(self):
        """Open a form for entering the type and parameters of a sampled wave."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Generate Signal")
        dialog.configure(bg=BG)
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        frame = tk.Frame(dialog, bg=CARD, padx=20, pady=18)
        frame.pack(fill=tk.BOTH, expand=True, padx=14, pady=14)
        tk.Label(frame, text="Signal Generation Parameters", bg=CARD, fg=TEXT,
                 font=(FONT, 13, "bold")).grid(row=0, column=0, columnspan=2,
                                                sticky="w", pady=(0, 14))

        # Defaults match the two Task 2 test cases supplied by the user.
        tk.Label(frame, text="Type", bg=CARD, fg=TEXT, font=(FONT, 10)).grid(
            row=1, column=0, sticky="w", padx=(0, 18), pady=6)
        type_var = tk.StringVar(value="sin")
        type_combo = ttk.Combobox(
            frame, textvariable=type_var, values=("sin", "cos"),
            state="readonly", width=16, style="Dark.TCombobox"
        )
        type_combo.grid(row=1, column=1, sticky="ew", pady=6)

        fields = [
            ("A", "3"),
            ("AnalogFrequency", "360"),
            ("SamplingFrequency", "720"),
            ("PhaseShift", "1.96349540849362"),
        ]
        entries = {}
        for row, (label, default) in enumerate(fields, start=2):
            tk.Label(frame, text=label, bg=CARD, fg=TEXT, font=(FONT, 10)).grid(
                row=row, column=0, sticky="w", padx=(0, 18), pady=6)
            entry = ttk.Entry(frame, width=22, style="Dark.TEntry", justify="right")
            entry.insert(0, default)
            entry.grid(row=row, column=1, sticky="ew", pady=6)
            entries[label] = entry

        def update_defaults(event=None):
            """Switch the parameter defaults when the user selects sin or cos."""
            defaults = (
                {"A": "3", "AnalogFrequency": "360", "SamplingFrequency": "720",
                 "PhaseShift": "1.96349540849362"}
                if type_var.get() == "sin"
                else {"A": "3", "AnalogFrequency": "200", "SamplingFrequency": "500",
                      "PhaseShift": "2.35619449019235"}
            )
            for key, value in defaults.items():
                entries[key].delete(0, tk.END)
                entries[key].insert(0, value)

        type_combo.bind("<<ComboboxSelected>>", update_defaults)

        tk.Label(
            frame,
            text="PhaseShift is in radians. SamplingFrequency should be at least 2 × AnalogFrequency.",
            bg=CARD, fg=MUTED, font=(FONT, 9), wraplength=350, justify="left"
        ).grid(row=6, column=0, columnspan=2, sticky="w", pady=(8, 12))

        def generate():
            try:
                wave_type = type_var.get()
                amplitude = float(entries["A"].get().strip())
                frequency = float(entries["AnalogFrequency"].get().strip())
                sampling_frequency = float(entries["SamplingFrequency"].get().strip())
                phase = float(entries["PhaseShift"].get().strip())
                values = (amplitude, frequency, sampling_frequency, phase)
                if not all(math.isfinite(v) for v in values):
                    raise ValueError("All parameters must be finite numbers.")
                if amplitude < 0:
                    raise ValueError("A must be zero or greater.")
                if frequency <= 0:
                    raise ValueError("AnalogFrequency must be greater than zero.")
                if sampling_frequency <= 0:
                    raise ValueError("SamplingFrequency must be greater than zero.")
                if sampling_frequency < 2 * frequency:
                    raise ValueError(
                        "IT'S ALIAS.\n"
                        "Sampling theorem not satisfied: SamplingFrequency must be at least "
                        "twice AnalogFrequency.\n"
                        f"Here, SamplingFrequency = {sampling_frequency:g} and "
                        f"2 × AnalogFrequency = {2 * frequency:g}."
                    )

                # Generate one second of samples, matching n = np.arange(0, SamplingFrequency).
                sample_count = int(math.ceil(sampling_frequency))
                if sample_count > 20000:
                    raise ValueError(
                        f"These settings require {sample_count:,} samples for one second. "
                        "Please use a sampling frequency of 20,000 Hz or less."
                    )
                indices = list(range(sample_count))
                function = math.sin if wave_type == "sin" else math.cos
                samples = [
                    amplitude * function(2 * math.pi * frequency * n / sampling_frequency + phase)
                    for n in indices
                ]
                name = f"{wave_type}_{frequency:g}Hz_Fs{sampling_frequency:g}"
                self.add_result(name, (indices, samples))
                status_message = (
                    f"Generated {wave_type} signal: A={amplitude:g}, "
                    f"AnalogFrequency={frequency:g} Hz, "
                    f"SamplingFrequency={sampling_frequency:g} Hz, "
                    f"PhaseShift={phase:g} rad ({sample_count} samples)."
                )
                if math.isclose(sampling_frequency, 2 * frequency, rel_tol=1e-12, abs_tol=1e-12):
                    status_message += " Warning: SamplingFrequency = 2 × AnalogFrequency (Nyquist boundary)."
                self.set_status(status_message, "ok")
                dialog.destroy()
            except ValueError as error:
                messagebox.showerror("Invalid signal parameters", str(error), parent=dialog)

        buttons = tk.Frame(frame, bg=CARD)
        buttons.grid(row=7, column=0, columnspan=2, sticky="ew")
        ttk.Button(buttons, text="Generate signal", style="Accent.TButton",
                   command=generate).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        ttk.Button(buttons, text="Cancel", style="Soft.TButton",
                   command=dialog.destroy).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 0))
        entries["A"].focus_set()
        dialog.bind("<Return>", lambda event: generate())

    # ---------- styling ----------
    def setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        base = {
            "borderwidth": 0,
            "focusthickness": 0,
            "focuscolor": CARD,
            "padding": (10, 8),
            "font": (FONT, 10, "bold"),
            "relief": "flat",
        }
        style.configure("Accent.TButton", background=ACCENT, foreground="white", **base)
        style.map("Accent.TButton", background=[("pressed", ACCENT_DARK), ("active", ACCENT_HOVER)])
        style.configure("Soft.TButton", background=SOFT, foreground=TEXT, **base)
        style.map("Soft.TButton", background=[("pressed", ACCENT_DARK), ("active", SOFT_HOVER)])
        style.configure("Danger.TButton", background=CARD, foreground=DANGER, **base)
        style.map("Danger.TButton", background=[("active", SOFT)])
        style.configure(
            "Dark.TEntry",
            fieldbackground=BG,
            foreground=TEXT,
            insertcolor=TEXT,
            bordercolor=SOFT,
            lightcolor=SOFT,
            darkcolor=SOFT,
            padding=7,
        )
        style.map(
            "Dark.TEntry",
            bordercolor=[("focus", ACCENT)],
            lightcolor=[("focus", ACCENT)],
            darkcolor=[("focus", ACCENT)],
        )
        style.configure(
            "Dark.TCombobox",
            fieldbackground=BG,
            background=SOFT,
            foreground=TEXT,
            arrowcolor=TEXT,
            padding=6,
        )
        style.map(
            "Dark.TCombobox",
            fieldbackground=[("readonly", BG)],
            foreground=[("readonly", TEXT)],
            selectbackground=[("readonly", BG)],
            selectforeground=[("readonly", TEXT)],
        )

    def card(self, parent, title):
        frame = tk.Frame(parent, bg=CARD, padx=14, pady=12)
        frame.pack(fill=tk.X, pady=(0, 10))
        tk.Label(
            frame,
            text=title.upper(),
            bg=CARD,
            fg=MUTED,
            font=(FONT, 8, "bold"),
        ).pack(anchor="w", pady=(0, 8))
        return frame

    # ---------- layout ----------
    def build_header(self):
        header = tk.Frame(self.root, bg=PANEL, padx=20, pady=14)
        header.pack(fill=tk.X)
        tk.Label(
            header, text="Signal Lab", bg=PANEL, fg=TEXT, font=(FONT, 18, "bold")
        ).pack(side=tk.LEFT)
        tk.Label(
            header,
            text="  discrete-time signal processing",
            bg=PANEL,
            fg=MUTED,
            font=(FONT, 10),
        ).pack(side=tk.LEFT, pady=(6, 0))

    def build_status_bar(self):
        self.status = tk.Label(
            self.root,
            text="Load a signal to get started.",
            bg=PANEL,
            fg=MUTED,
            anchor="w",
            padx=20,
            pady=8,
            font=(FONT, 9),
        )
        self.status.pack(fill=tk.X, side=tk.BOTTOM)

    def build_body(self):
        body = tk.Frame(self.root, bg=BG)
        body.pack(fill=tk.BOTH, expand=True, padx=14, pady=14)

        # Keep the left controls scrollable so every operation remains reachable
        # on smaller screens and at lower window heights.
        side = tk.Frame(body, bg=BG, width=310)
        side.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 14))
        side.pack_propagate(False)

        side_canvas = tk.Canvas(side, bg=BG, highlightthickness=0, borderwidth=0)
        side_scrollbar = ttk.Scrollbar(side, orient="vertical", command=side_canvas.yview)
        side_canvas.configure(yscrollcommand=side_scrollbar.set)
        side_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        side_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        controls = tk.Frame(side_canvas, bg=BG, width=290)
        controls_window = side_canvas.create_window((0, 0), window=controls, anchor="nw")

        def update_controls_scrollregion(event=None):
            side_canvas.configure(scrollregion=side_canvas.bbox("all"))

        def resize_controls_width(event):
            side_canvas.itemconfigure(controls_window, width=event.width)

        controls.bind("<Configure>", update_controls_scrollregion)
        side_canvas.bind("<Configure>", resize_controls_width)

        # Mouse wheel scrolling for Windows/macOS and Linux.
        def scroll_controls(event):
            if getattr(event, "delta", 0):
                side_canvas.yview_scroll(int(-event.delta / 120), "units")
            elif getattr(event, "num", None) == 4:
                side_canvas.yview_scroll(-1, "units")
            elif getattr(event, "num", None) == 5:
                side_canvas.yview_scroll(1, "units")

        side_canvas.bind_all("<MouseWheel>", scroll_controls)
        side_canvas.bind_all("<Button-4>", scroll_controls)
        side_canvas.bind_all("<Button-5>", scroll_controls)

        plot_card = tk.Frame(body, bg=CARD, padx=12, pady=12)
        plot_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Signals
        card = self.card(controls, "Signals")
        ttk.Button(
            card,
            text="＋  Load signal from file",
            style="Accent.TButton",
            command=self.load_signal,
        ).pack(fill=tk.X)

        self.listbox = tk.Listbox(
            card,
            selectmode=tk.EXTENDED,
            height=7,
            exportselection=False,
            bg=BG,
            fg=TEXT,
            selectbackground=ACCENT,
            selectforeground="white",
            highlightthickness=0,
            borderwidth=0,
            relief="flat",
            activestyle="none",
            font=(FONT, 10),
        )
        self.listbox.pack(fill=tk.X, pady=(10, 4), ipady=4)
        self.listbox.bind("<<ListboxSelect>>", self.on_select)

        tk.Label(
            card,
            text="Tip: Ctrl-click (or Shift-click) to select multiple signals.",
            bg=CARD,
            fg=MUTED,
            font=(FONT, 8),
            wraplength=270,
            justify="left",
        ).pack(fill=tk.X, pady=(0, 8))

        ttk.Button(
            card,
            text="Display selected signals together",
            style="Accent.TButton",
            command=self.display_selected_signals,
        ).pack(fill=tk.X, pady=(0, 8))

        ttk.Button(
            card,
            text="Remove selected",
            style="Danger.TButton",
            command=self.remove_selected,
        ).pack(fill=tk.X)

        # Combine signals
        card = self.card(controls, "Combine selected")
        row = tk.Frame(card, bg=CARD)
        row.pack(fill=tk.X)
        ttk.Button(
            row, text="Add", style="Soft.TButton", command=self.add
        ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 4))
        ttk.Button(
            row, text="Subtract", style="Soft.TButton", command=self.subtract
        ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(4, 0))

        # Transform a single signal
        card = self.card(controls, "Transform one signal")
        row = tk.Frame(card, bg=CARD)
        row.pack(fill=tk.X, pady=(0, 8))
        tk.Label(
            row, text="Scale by", bg=CARD, fg=TEXT, font=(FONT, 10), width=9, anchor="w"
        ).pack(side=tk.LEFT)
        self.constant_entry = ttk.Entry(row, width=7, style="Dark.TEntry", justify="center")
        self.constant_entry.insert(0, "2")
        self.constant_entry.pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(row, text="Apply", style="Soft.TButton", command=self.scale).pack(
            side=tk.LEFT, expand=True, fill=tk.X
        )

        row = tk.Frame(card, bg=CARD)
        row.pack(fill=tk.X, pady=(0, 8))
        tk.Label(
            row, text="Shift by k", bg=CARD, fg=TEXT, font=(FONT, 10), width=9, anchor="w"
        ).pack(side=tk.LEFT)
        self.k_entry = ttk.Entry(row, width=7, style="Dark.TEntry", justify="center")
        self.k_entry.insert(0, "3")
        self.k_entry.pack(side=tk.LEFT, padx=(0, 8))
        tk.Label(row, text="steps", bg=CARD, fg=MUTED, font=(FONT, 9)).pack(side=tk.LEFT)

        row = tk.Frame(card, bg=CARD)
        row.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(row, text="Delay", style="Soft.TButton", command=self.delay).pack(
            side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 4)
        )
        ttk.Button(row, text="Advance", style="Soft.TButton", command=self.advance).pack(
            side=tk.LEFT, expand=True, fill=tk.X, padx=(4, 0)
        )
        ttk.Button(card, text="Fold  x(−n)", style="Soft.TButton", command=self.fold).pack(
            fill=tk.X
        )

        # Plot toolbar and canvas
        toolbar = tk.Frame(plot_card, bg=CARD)
        toolbar.pack(fill=tk.X, pady=(0, 10))
        tk.Label(
            toolbar,
            text="Signal representation:",
            bg=CARD,
            fg=TEXT,
            font=(FONT, 10, "bold"),
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.display_mode = tk.StringVar(value="Discrete")
        self.display_selector = ttk.Combobox(
            toolbar,
            textvariable=self.display_mode,
            values=("Discrete", "Continuous"),
            state="readonly",
            width=14,
            style="Dark.TCombobox",
        )
        self.display_selector.pack(side=tk.LEFT)
        self.display_selector.bind("<<ComboboxSelected>>", self.on_display_mode_change)

        tk.Label(
            toolbar,
            text="Discrete = stems  •  Continuous = connected samples",
            bg=CARD,
            fg=MUTED,
            font=(FONT, 9),
        ).pack(side=tk.LEFT, padx=(12, 0))

        self.figure = Figure(figsize=(7, 5), facecolor=CARD, layout="constrained")
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=plot_card)
        self.canvas.get_tk_widget().configure(bg=CARD, highlightthickness=0)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # ---------- helpers ----------
    def set_status(self, message, kind="info"):
        colors = {"info": MUTED, "ok": SUCCESS, "error": DANGER}
        self.status.config(text=message, fg=colors.get(kind, MUTED))

    def style_axes(self):
        self.ax.set_facecolor(CARD)
        for spine in self.ax.spines.values():
            spine.set_color(SOFT)
        self.ax.tick_params(colors=MUTED)
        self.ax.xaxis.label.set_color(MUTED)
        self.ax.yaxis.label.set_color(MUTED)
        self.ax.title.set_color(TEXT)
        self.ax.grid(True, color=SOFT, alpha=0.6, linewidth=0.8)
        self.ax.set_axisbelow(True)

    def draw_empty(self):
        self.ax.clear()
        self.style_axes()
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.ax.text(
            0.5,
            0.5,
            "No signal to display",
            color=MUTED,
            fontsize=13,
            ha="center",
            va="center",
            transform=self.ax.transAxes,
        )
        self.canvas.draw()

    def selected(self):
        return [self.signals[i] for i in self.listbox.curselection()]

    def need(self, count, exact=True):
        chosen = self.selected()
        if exact and len(chosen) != count:
            self.set_status(f"Select exactly {count} signal(s) first.", "error")
            return None
        if not exact and len(chosen) < count:
            self.set_status(f"Select at least {count} signal(s) first.", "error")
            return None
        return chosen

    def add_result(self, name, signal):
        self.signals.append((name, signal))
        self.listbox.insert(tk.END, name)
        self.listbox.selection_clear(0, tk.END)
        new_index = len(self.signals) - 1
        self.listbox.selection_set(new_index)
        self.listbox.activate(new_index)
        self.plot([(name, signal)])
        self.set_status(f"Created: {name}", "ok")

    # ---------- plotting ----------
    def plot(self, chosen):
        self.ax.clear()
        mode = self.display_mode.get() if hasattr(self, "display_mode") else "Discrete"
        handles = []

        for i, (name, (indices, samples)) in enumerate(chosen):
            color = PLOT_COLORS[i % len(PLOT_COLORS)]

            if mode == "Discrete":
                container = self.ax.stem(indices, samples)
                container.stemlines.set_color(color)
                container.stemlines.set_linewidth(2)
                container.markerline.set_color(color)
                container.markerline.set_markerfacecolor(color)
                container.markerline.set_markeredgecolor(color)
                container.markerline.set_markersize(7)
                container.baseline.set_visible(False)
                handles.append(
                    Line2D(
                        [0], [0], color=color, marker="o",
                        linestyle="None", label=name
                    )
                )
            else:
                self.ax.plot(
                    indices,
                    samples,
                    color=color,
                    marker="o",
                    markersize=5,
                    linewidth=2,
                    label=name,
                )

        self.style_axes()
        self.ax.axhline(0, color=MUTED, linewidth=1)
        self.ax.set_xlabel("Sample index n")
        self.ax.set_ylabel("Amplitude")
        self.ax.set_title(f"{mode} representation")
        self.ax.xaxis.set_major_locator(MaxNLocator(integer=True))

        if chosen:
            if mode == "Discrete":
                self.ax.legend(
                    handles=handles,
                    facecolor=PANEL,
                    edgecolor=SOFT,
                    labelcolor=TEXT,
                    loc="best",
                )
            else:
                legend = self.ax.legend(
                    facecolor=PANEL,
                    edgecolor=SOFT,
                    loc="best",
                )
                if legend:
                    for label in legend.get_texts():
                        label.set_color(TEXT)

        self.canvas.draw()

    def on_select(self, event=None):
        chosen = self.selected()
        if chosen:
            self.plot(chosen)
            names = ", ".join(name for name, _ in chosen)
            self.set_status(f"Showing together: {names}", "info")
        else:
            self.draw_empty()

    def display_selected_signals(self):
        chosen = self.selected()
        if len(chosen) < 2:
            self.set_status(
                "Select at least two signals in the list (Ctrl-click or Shift-click), then display them together.",
                "error",
            )
            messagebox.showinfo(
                "Display two signals",
                "Select at least two signals in the Signals list.\n"
                "Hold Ctrl while clicking each signal (or use Shift for a range), "
                "then click 'Display selected signals together'.",
                parent=self.root,
            )
            return
        self.plot(chosen)
        names = ", ".join(name for name, _ in chosen)
        self.set_status(f"Displaying {len(chosen)} signals together: {names}", "ok")

    def on_display_mode_change(self, event=None):
        chosen = self.selected()
        if chosen:
            self.plot(chosen)
            self.set_status(f"Display mode: {self.display_mode.get()}", "info")
        else:
            self.draw_empty()
            self.set_status(f"Display mode set to {self.display_mode.get()}. Load a signal to begin.")

    # ---------- button actions ----------
    def load_signal(self):
        path = filedialog.askopenfilename(
            title="Choose a signal text file",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            signal = read_signal(path)
        except Exception as error:
            messagebox.showerror("Load failed", f"Could not read the file:\n{error}")
            self.set_status("Failed to load signal.", "error")
            return
        self.add_result(os.path.basename(path), signal)

    def add(self):
        chosen = self.need(2, exact=False)
        if not chosen:
            return
        try:
            result = add_signals(*[signal for _, signal in chosen])
        except Exception as error:
            messagebox.showerror("Addition failed", str(error))
            return
        name = " + ".join(name for name, _ in chosen)
        self.add_result(name, result)

    def subtract(self):
        chosen = self.need(2)
        if not chosen:
            return
        (name1, signal1), (name2, signal2) = chosen
        self.add_result(f"{name1} - {name2}", subtract_signals(signal1, signal2))

    def scale(self):
        chosen = self.need(1)
        if not chosen:
            return
        try:
            constant = float(self.constant_entry.get())
        except ValueError:
            self.set_status("The scale constant must be a number.", "error")
            messagebox.showwarning("Invalid input", "The scale constant must be a number.")
            return
        name, signal = chosen[0]
        self.add_result(f"{constant:g} × {name}", multiply_signal(signal, constant))

    def read_k(self):
        try:
            return int(self.k_entry.get())
        except ValueError:
            self.set_status("k must be an integer.", "error")
            messagebox.showwarning("Invalid input", "k must be an integer.")
            return None

    def delay(self):
        chosen = self.need(1)
        if not chosen:
            return
        k = self.read_k()
        if k is None:
            return
        name, signal = chosen[0]
        # x[n-k] moves each sample index to the right by k.
        self.add_result(f"{name} delayed by {k}", shift_signal(signal, -k))

    def advance(self):
        chosen = self.need(1)
        if not chosen:
            return
        k = self.read_k()
        if k is None:
            return
        name, signal = chosen[0]
        # x[n+k] moves each sample index to the left by k.
        self.add_result(f"{name} advanced by {k}", shift_signal(signal, k))

    def fold(self):
        chosen = self.need(1)
        if not chosen:
            return
        name, signal = chosen[0]
        self.add_result(f"fold({name})", fold_signal(signal))

    def remove_selected(self):
        indexes = list(self.listbox.curselection())
        if not indexes:
            self.set_status("Select a signal to remove.", "error")
            return

        for index in reversed(indexes):
            del self.signals[index]
            self.listbox.delete(index)

        remaining = self.selected()
        if remaining:
            self.plot(remaining)
        else:
            self.draw_empty()
        self.set_status(f"Removed {len(indexes)} signal(s).", "info")


def main():
    root = tk.Tk()
    SignalApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
