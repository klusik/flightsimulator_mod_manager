"""Main Tkinter window."""

import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from fs24_mod_manager.config import Config
from fs24_mod_manager.models.package_info import PackageInfo


class MainView:
    """Render application state and expose user-intent callbacks."""

    def __init__(self, root: tk.Tk) -> None:
        """Build the main window.

        @param root: Tk application root.
        """
        self.root = root
        root.title(Config.APP_NAME)
        self.community_var = tk.StringVar()
        self.disabled_var = tk.StringVar()
        self.search_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready")
        self._packages: dict[str, PackageInfo] = {}
        self._build()

    def bind_actions(
        self,
        choose_community: Callable[[], None],
        choose_disabled: Callable[[], None],
        refresh: Callable[[], None],
        enable: Callable[[], None],
        disable: Callable[[], None],
        close: Callable[[], None],
    ) -> None:
        """Connect controller commands.

        @param choose_community: Community picker command.
        @param choose_disabled: Disabled-root picker command.
        @param refresh: Scan command.
        @param enable: Enable selection command.
        @param disable: Disable selection command.
        @param close: Window-close command.
        """
        self.community_button.configure(command=choose_community)
        self.disabled_button.configure(command=choose_disabled)
        self.refresh_button.configure(command=refresh)
        self.enable_button.configure(command=enable)
        self.disable_button.configure(command=disable)
        self.search_var.trace_add("write", lambda *_: self._filter())
        self.root.protocol("WM_DELETE_WINDOW", close)

    def show_packages(self, packages: list[PackageInfo]) -> None:
        """Replace table contents.

        @param packages: Current package snapshot.
        """
        self._packages = {str(index): package for index, package in enumerate(packages)}
        self._filter()

    def selected_packages(self) -> list[PackageInfo]:
        """Return selected visible packages.

        @return: Selected package models.
        """
        return [self._packages[item] for item in self.tree.selection() if item in self._packages]

    def choose_directory(self, initial: Path | None) -> Path | None:
        """Open a directory picker.

        @param initial: Initial directory.
        @return: Selected path or `None`.
        """
        value = filedialog.askdirectory(initialdir=str(initial) if initial else None)
        return Path(value) if value else None

    def confirm(self, title: str, message: str) -> bool:
        """Ask for safe-default confirmation.

        @param title: Dialog title.
        @param message: Requested operation summary.
        @return: Whether the user approved.
        """
        return messagebox.askokcancel(title, message, default=messagebox.CANCEL)

    def show_error(self, message: str) -> None:
        """Display an actionable error.

        @param message: User-facing error.
        """
        messagebox.showerror(Config.APP_NAME, message)

    def set_busy(self, busy: bool) -> None:
        """Enable or disable conflicting controls.

        @param busy: Whether work is active.
        """
        state = tk.DISABLED if busy else tk.NORMAL
        for widget in (
            self.community_button,
            self.disabled_button,
            self.refresh_button,
            self.enable_button,
            self.disable_button,
        ):
            widget.configure(state=state)

    def _build(self) -> None:
        """Construct widgets and layout."""
        frame = ttk.Frame(self.root, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        for row, (label, variable) in enumerate(
            (("Community", self.community_var), ("Disabled", self.disabled_var))
        ):
            ttk.Label(frame, text=label).grid(row=row, column=0, sticky=tk.W, padx=(0, 8), pady=3)
            ttk.Entry(frame, textvariable=variable, state="readonly").grid(
                row=row, column=1, sticky=tk.EW, pady=3
            )
        self.community_button = ttk.Button(frame, text="Choose…")
        self.community_button.grid(row=0, column=2, padx=(8, 0))
        self.disabled_button = ttk.Button(frame, text="Choose…")
        self.disabled_button.grid(row=1, column=2, padx=(8, 0))
        ttk.Label(frame, text="Search").grid(row=2, column=0, sticky=tk.W, pady=(8, 3))
        ttk.Entry(frame, textvariable=self.search_var).grid(
            row=2, column=1, sticky=tk.EW, pady=(8, 3)
        )
        self.refresh_button = ttk.Button(frame, text="Refresh")
        self.refresh_button.grid(row=2, column=2, padx=(8, 0), pady=(8, 3))
        self.tree = ttk.Treeview(
            frame,
            columns=("name", "version", "creator", "directory", "status"),
            show="headings",
            selectmode="extended",
        )
        for key, title, width in (
            ("name", "Name", 240),
            ("version", "Version", 80),
            ("creator", "Creator", 150),
            ("directory", "Directory", 230),
            ("status", "Status", 90),
        ):
            self.tree.heading(key, text=title)
            self.tree.column(key, width=width, stretch=True)
        self.tree.grid(row=3, column=0, columnspan=3, sticky=tk.NSEW, pady=8)
        actions = ttk.Frame(frame)
        actions.grid(row=4, column=0, columnspan=3, sticky=tk.EW)
        self.enable_button = ttk.Button(actions, text="Enable")
        self.enable_button.pack(side=tk.LEFT)
        self.disable_button = ttk.Button(actions, text="Disable")
        self.disable_button.pack(side=tk.LEFT, padx=8)
        ttk.Label(actions, textvariable=self.status_var).pack(side=tk.RIGHT)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(3, weight=1)

    def _filter(self) -> None:
        """Apply the current case-insensitive search text."""
        query = self.search_var.get().casefold().strip()
        self.tree.delete(*self.tree.get_children())
        for key, package in self._packages.items():
            searchable = " ".join(
                (
                    package.title,
                    package.directory_name,
                    package.creator,
                    package.manufacturer,
                    package.version,
                )
            ).casefold()
            if query and query not in searchable:
                continue
            self.tree.insert(
                "",
                tk.END,
                iid=key,
                values=(
                    package.title,
                    package.version,
                    package.creator,
                    package.directory_name,
                    package.status.value,
                ),
            )
