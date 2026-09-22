"""Main Tkinter window."""

import tkinter as tk
from collections.abc import Callable
from functools import partial
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from fs24_mod_manager.config import Config
from fs24_mod_manager.models.package_info import PackageInfo, PackageStatus


class MainView:
    """Render application state and expose user-intent callbacks."""

    def __init__(self, root: tk.Tk) -> None:
        """Build the main window.

        @param root: Tk application root.
        """
        self.root = root
        root.title(f"{Config.APP_NAME} {Config.APP_VERSION}")
        root.minsize(820, 520)
        self.community_var = tk.StringVar()
        self.disabled_var = tk.StringVar()
        self.search_var = tk.StringVar()
        self.filter_var = tk.StringVar(value="All")
        self.status_var = tk.StringVar(value="Ready")
        self.summary_var = tk.StringVar(value="No packages loaded")
        self.selection_var = tk.StringVar(value="0 selected")
        self._packages: dict[str, PackageInfo] = {}
        self._busy = False
        self._sort_column = "name"
        self._sort_reverse = False
        self._column_titles: dict[str, str] = {}
        self._build()
        self._configure_styles()

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
        self.select_all_button.configure(command=self.select_all)
        self.clear_selection_button.configure(command=self.unselect_all)
        self.search_var.trace_add("write", lambda *_: self._filter())
        self.filter_var.trace_add("write", lambda *_: self._filter())
        self.tree.bind("<<TreeviewSelect>>", self._on_selection_changed)
        self.root.bind("<Control-a>", self._select_all_event)
        self.root.bind("<Control-A>", self._select_all_event)
        self.root.bind("<Escape>", self._unselect_all_event)
        self.root.bind("<F5>", lambda _event: refresh())
        self.root.protocol("WM_DELETE_WINDOW", close)

    def show_packages(self, packages: list[PackageInfo]) -> None:
        """Replace table contents while preserving matching selections.

        @param packages: Current package snapshot.
        """
        selected_identities = {package.identity for package in self.selected_packages()}
        self._packages = {str(index): package for index, package in enumerate(packages)}
        self._filter()
        preserved = [
            key for key, item in self._packages.items() if item.identity in selected_identities
        ]
        self.tree.selection_set(preserved)
        self._update_summary()
        self._update_action_states()

    def selected_packages(self) -> list[PackageInfo]:
        """Return selected visible packages.

        @return: Selected package models.
        """
        return [self._packages[item] for item in self.tree.selection() if item in self._packages]

    def select_all(self) -> None:
        """Select every package currently visible after filtering."""
        self.tree.selection_set(self.tree.get_children())
        self._update_action_states()

    def unselect_all(self) -> None:
        """Clear the current package selection."""
        self.tree.selection_remove(self.tree.selection())
        self._update_action_states()

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
        self._busy = busy
        state = tk.DISABLED if busy else tk.NORMAL
        for widget in (self.community_button, self.disabled_button, self.refresh_button):
            widget.configure(state=state)
        self._update_action_states()

    def _build(self) -> None:
        """Construct the structured, resizable main-window layout."""
        outer = ttk.Frame(self.root, padding=12)
        outer.pack(fill=tk.BOTH, expand=True)
        heading = ttk.Frame(outer)
        heading.grid(row=0, column=0, sticky=tk.EW, pady=(0, 10))
        ttk.Label(
            heading,
            text=f"{Config.APP_NAME} {Config.APP_VERSION}",
            style="Title.TLabel",
        ).pack(side=tk.LEFT)
        ttk.Label(heading, textvariable=self.summary_var, style="Summary.TLabel").pack(
            side=tk.RIGHT
        )
        paths = ttk.LabelFrame(outer, text="Package locations", padding=10)
        paths.grid(row=1, column=0, sticky=tk.EW)
        for row, (label, variable) in enumerate(
            (("Community", self.community_var), ("Disabled mods", self.disabled_var))
        ):
            ttk.Label(paths, text=label).grid(row=row, column=0, sticky=tk.W, padx=(0, 8), pady=3)
            ttk.Entry(paths, textvariable=variable, state="readonly").grid(
                row=row, column=1, sticky=tk.EW, pady=3
            )
        self.community_button = ttk.Button(paths, text="Browse…")
        self.community_button.grid(row=0, column=2, padx=(8, 0))
        self.disabled_button = ttk.Button(paths, text="Browse…")
        self.disabled_button.grid(row=1, column=2, padx=(8, 0))
        paths.columnconfigure(1, weight=1)
        toolbar = ttk.Frame(outer)
        toolbar.grid(row=2, column=0, sticky=tk.EW, pady=(10, 6))
        ttk.Label(toolbar, text="Search").pack(side=tk.LEFT)
        self.search_entry = ttk.Entry(toolbar, textvariable=self.search_var, width=32)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 12))
        ttk.Label(toolbar, text="Show").pack(side=tk.LEFT)
        self.filter_combo = ttk.Combobox(
            toolbar,
            textvariable=self.filter_var,
            values=("All", "Enabled", "Disabled", "Conflicted", "Invalid"),
            state="readonly",
            width=11,
        )
        self.filter_combo.pack(side=tk.LEFT, padx=(6, 12))
        self.select_all_button = ttk.Button(toolbar, text="☑ Select all")
        self.select_all_button.pack(side=tk.LEFT)
        self.clear_selection_button = ttk.Button(toolbar, text="☐ Clear", width=10)
        self.clear_selection_button.pack(side=tk.LEFT, padx=6)
        self.refresh_button = ttk.Button(toolbar, text="↻ Refresh", width=11)
        self.refresh_button.pack(side=tk.LEFT)
        table = ttk.Frame(outer)
        table.grid(row=3, column=0, sticky=tk.NSEW)
        self.tree = ttk.Treeview(
            table,
            columns=("state", "name", "version", "creator", "directory", "status"),
            show="headings",
            selectmode="extended",
        )
        columns = (
            ("state", "", 38, False),
            ("name", "Name", 250, True),
            ("version", "Version", 80, False),
            ("creator", "Creator", 160, True),
            ("directory", "Directory", 260, True),
            ("status", "Status", 95, False),
        )
        for key, title, width, stretch in columns:
            self._column_titles[key] = title
            marker = " ▲" if key == self._sort_column else ""
            self.tree.heading(
                key,
                text=f"{title}{marker}",
                command=partial(self._change_sort, key),
            )
            if key in {"state", "version", "status"}:
                self.tree.column(key, width=width, minwidth=width, stretch=stretch, anchor="center")
            else:
                self.tree.column(key, width=width, minwidth=width, stretch=stretch, anchor="w")
        vertical = ttk.Scrollbar(table, orient=tk.VERTICAL, command=self.tree.yview)
        horizontal = ttk.Scrollbar(table, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        self.tree.grid(row=0, column=0, sticky=tk.NSEW)
        vertical.grid(row=0, column=1, sticky=tk.NS)
        horizontal.grid(row=1, column=0, sticky=tk.EW)
        table.columnconfigure(0, weight=1)
        table.rowconfigure(0, weight=1)
        actions = ttk.Frame(outer)
        actions.grid(row=4, column=0, sticky=tk.EW, pady=(10, 0))
        self.enable_button = ttk.Button(actions, text="✓ Enable selected")
        self.enable_button.pack(side=tk.LEFT)
        self.disable_button = ttk.Button(actions, text="○ Disable selected")
        self.disable_button.pack(side=tk.LEFT, padx=8)
        ttk.Label(actions, textvariable=self.selection_var).pack(side=tk.LEFT, padx=8)
        ttk.Separator(outer).grid(row=5, column=0, sticky=tk.EW, pady=(10, 6))
        ttk.Label(outer, textvariable=self.status_var, anchor=tk.W).grid(
            row=6, column=0, sticky=tk.EW
        )
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(3, weight=1)

    def _configure_styles(self) -> None:
        """Apply lightweight native-theme presentation styles."""
        style = ttk.Style(self.root)
        style.configure("Title.TLabel", font=("Segoe UI", 15, "bold"))
        style.configure("Summary.TLabel", foreground="#555555")
        style.configure("Treeview", rowheight=25)
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))
        self.tree.tag_configure(PackageStatus.ENABLED.value, foreground="#167548")
        self.tree.tag_configure(PackageStatus.DISABLED.value, foreground="#666666")
        self.tree.tag_configure(PackageStatus.CONFLICTED.value, foreground="#a15c00")
        self.tree.tag_configure(PackageStatus.INVALID.value, foreground="#a4262c")

    def _filter(self) -> None:
        """Apply name search, state filtering, and the current ordering."""
        query = self.search_var.get().casefold().strip()
        status_filter = self.filter_var.get()
        self.tree.delete(*self.tree.get_children())
        ordered = sorted(
            self._packages.items(),
            key=lambda item: self._sort_value(item[1]),
            reverse=self._sort_reverse,
        )
        for key, package in ordered:
            searchable = f"{package.title} {package.directory_name}".casefold()
            if query and query not in searchable:
                continue
            if status_filter != "All" and package.status.value != status_filter:
                continue
            values = (
                self._status_symbol(package.status),
                package.title,
                package.version,
                package.creator,
                package.directory_name,
                package.status.value,
            )
            self.tree.insert("", tk.END, iid=key, values=values, tags=(package.status.value,))
        self._update_summary()
        self._update_action_states()

    def _change_sort(self, column: str) -> None:
        """Select a column order or reverse the active order.

        @param column: Tree column identifier.
        """
        if column == self._sort_column:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_column = column
            self._sort_reverse = False
        for key, title in self._column_titles.items():
            marker = ""
            if key == self._sort_column:
                marker = " ▼" if self._sort_reverse else " ▲"
            self.tree.heading(key, text=f"{title}{marker}")
        self._filter()

    def _sort_value(self, package: PackageInfo) -> tuple[str, str]:
        """Return a deterministic case-insensitive table sort key.

        @param package: Package represented by a row.
        @return: Selected column value and directory-name tie breaker.
        """
        values = {
            "state": package.status.value,
            "name": package.title,
            "version": package.version,
            "creator": package.creator,
            "directory": package.directory_name,
            "status": package.status.value,
        }
        return values[self._sort_column].casefold(), package.directory_name.casefold()

    def _status_symbol(self, status: PackageStatus) -> str:
        """Return a text icon that remains meaningful without color.

        @param status: Package status.
        @return: Compact status symbol.
        """
        symbols = {
            PackageStatus.ENABLED: "●",
            PackageStatus.DISABLED: "○",
            PackageStatus.CONFLICTED: "⚠",
            PackageStatus.INVALID: "✕",
        }
        return symbols[status]

    def _update_summary(self) -> None:
        """Update total and filtered package counts."""
        visible = len(self.tree.get_children())
        total = len(self._packages)
        enabled = sum(item.status is PackageStatus.ENABLED for item in self._packages.values())
        disabled = sum(item.status is PackageStatus.DISABLED for item in self._packages.values())
        filtered = f" · {visible} shown" if visible != total else ""
        self.summary_var.set(
            f"{total} packages · {enabled} enabled · {disabled} disabled{filtered}"
        )

    def _update_action_states(self) -> None:
        """Keep selection counters and action availability accurate."""
        selected = self.selected_packages()
        self.selection_var.set(f"{len(selected)} selected")
        can_enable = any(item.status is PackageStatus.DISABLED for item in selected)
        can_disable = any(item.status is PackageStatus.ENABLED for item in selected)
        self.enable_button.configure(
            state=tk.NORMAL if can_enable and not self._busy else tk.DISABLED
        )
        self.disable_button.configure(
            state=tk.NORMAL if can_disable and not self._busy else tk.DISABLED
        )
        selection_state = tk.NORMAL if self.tree.get_children() and not self._busy else tk.DISABLED
        self.select_all_button.configure(state=selection_state)
        self.clear_selection_button.configure(
            state=tk.NORMAL if selected and not self._busy else tk.DISABLED
        )

    def _on_selection_changed(self, _event: tk.Event[tk.Misc]) -> None:
        """React to mouse or keyboard selection changes.

        @param _event: Tk selection event.
        """
        self._update_action_states()

    def _select_all_event(self, _event: tk.Event[tk.Misc]) -> str:
        """Handle the select-all keyboard shortcut.

        @param _event: Tk keyboard event.
        @return: Tk event propagation directive.
        """
        self.select_all()
        return "break"

    def _unselect_all_event(self, _event: tk.Event[tk.Misc]) -> str:
        """Handle the clear-selection keyboard shortcut.

        @param _event: Tk keyboard event.
        @return: Tk event propagation directive.
        """
        self.unselect_all()
        return "break"
