"""
file_manager_page.py

Android file-management UI using ADB. Browse device storage, push/pull
files, create folders, rename, and delete (always behind confirmation).
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QFileDialog, QHBoxLayout, QInputDialog, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QWidget,
)

from app.adb.adb_client import AdbClient
from app.files.file_manager import DeviceFileManager
from app.ui.widgets.confirm_dialog import confirm_destructive, show_error, show_info
from app.ui.widgets.terminal_widget import TerminalWidget

DEFAULT_ROOT = "/sdcard"


class FileManagerPage(QWidget):
    def __init__(self, app_context, parent: QWidget | None = None):
        super().__init__(parent)
        self.ctx = app_context
        self.current_path = DEFAULT_ROOT
        self._build_ui()

    def _manager(self) -> DeviceFileManager | None:
        if not self.ctx.adb_path:
            show_error(self, "ADB Not Found", "ADB was not detected.")
            return None
        return DeviceFileManager(AdbClient(self.ctx.adb_path))

    def _serial(self):
        return self.ctx.active_adb_serial

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(12)

        header = QLabel("File Manager")
        header.setProperty("class", "SectionHeader")
        outer.addWidget(header)

        path_row = QHBoxLayout()
        self.path_edit = QLineEdit(DEFAULT_ROOT)
        go_btn = QPushButton("Go")
        up_btn = QPushButton("Up")
        refresh_btn = QPushButton("Refresh")
        path_row.addWidget(self.path_edit, 1)
        path_row.addWidget(go_btn)
        path_row.addWidget(up_btn)
        path_row.addWidget(refresh_btn)
        outer.addLayout(path_row)

        self.file_list = QListWidget()
        self.file_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        outer.addWidget(self.file_list, 1)

        action_row = QHBoxLayout()
        pull_btn = QPushButton("Pull Selected")
        push_btn = QPushButton("Push File Here")
        mkdir_btn = QPushButton("New Folder")
        rename_btn = QPushButton("Rename Selected")
        delete_btn = QPushButton("Delete Selected")
        delete_btn.setObjectName("DangerButton")
        for b in (pull_btn, push_btn, mkdir_btn, rename_btn, delete_btn):
            action_row.addWidget(b)
        outer.addLayout(action_row)

        self.terminal = TerminalWidget()
        outer.addWidget(self.terminal, 1)

        go_btn.clicked.connect(self._go_to_typed_path)
        up_btn.clicked.connect(self._go_up)
        refresh_btn.clicked.connect(self.refresh)
        pull_btn.clicked.connect(self._pull_selected)
        push_btn.clicked.connect(self._push_here)
        mkdir_btn.clicked.connect(self._make_dir)
        rename_btn.clicked.connect(self._rename_selected)
        delete_btn.clicked.connect(self._delete_selected)

        self.refresh()

    def _go_to_typed_path(self):
        self.current_path = self.path_edit.text().strip() or DEFAULT_ROOT
        self.refresh()

    def _go_up(self):
        self.current_path = DeviceFileManager.parent_path(self.current_path)
        self.refresh()

    def refresh(self):
        manager = self._manager()
        if not manager:
            return
        self.path_edit.setText(self.current_path)
        entries, error = manager.list_dir(self.current_path, self._serial())
        self.file_list.clear()
        if error:
            self.terminal.append_stdout(f"[error] {error}")
            return
        for entry in entries:
            label = f"[DIR]  {entry.name}" if entry.is_dir else f"       {entry.name}"
            if entry.size_bytes is not None and not entry.is_dir:
                label += f"  ({entry.size_bytes} bytes)"
            item = QListWidgetItem(label)
            item.setData(1, entry.name)
            item.setData(2, entry.is_dir)
            self.file_list.addItem(item)

    def _on_item_double_clicked(self, item: QListWidgetItem):
        if item.data(2):
            self.current_path = DeviceFileManager.join_path(self.current_path, item.data(1))
            self.refresh()

    def _selected_entry_name(self) -> str | None:
        item = self.file_list.currentItem()
        return item.data(1) if item else None

    def _pull_selected(self):
        manager = self._manager()
        name = self._selected_entry_name()
        if not manager or not name:
            show_error(self, "No Selection", "Select a file to pull first.")
            return
        remote = DeviceFileManager.join_path(self.current_path, name)
        local, _ = QFileDialog.getSaveFileName(self, "Save As", name)
        if not local:
            return
        result = manager.pull(remote, local, self._serial())
        self.terminal.append_result_full(result)

    def _push_here(self):
        manager = self._manager()
        if not manager:
            return
        local, _ = QFileDialog.getOpenFileName(self, "Select File To Push")
        if not local:
            return
        import os
        remote = DeviceFileManager.join_path(self.current_path, os.path.basename(local))
        result = manager.push(local, remote, self._serial())
        self.terminal.append_result_full(result)
        self.refresh()

    def _make_dir(self):
        manager = self._manager()
        if not manager:
            return
        name, ok = QInputDialog.getText(self, "New Folder", "Folder name:")
        if not ok or not name.strip():
            return
        remote = DeviceFileManager.join_path(self.current_path, name.strip())
        result = manager.make_dir(remote, self._serial())
        self.terminal.append_result_full(result)
        self.refresh()

    def _rename_selected(self):
        manager = self._manager()
        name = self._selected_entry_name()
        if not manager or not name:
            show_error(self, "No Selection", "Select a file or folder to rename.")
            return
        new_name, ok = QInputDialog.getText(self, "Rename", "New name:", text=name)
        if not ok or not new_name.strip() or new_name.strip() == name:
            return
        old_path = DeviceFileManager.join_path(self.current_path, name)
        new_path = DeviceFileManager.join_path(self.current_path, new_name.strip())
        result = manager.rename(old_path, new_path, self._serial())
        self.terminal.append_result_full(result)
        self.refresh()

    def _delete_selected(self):
        manager = self._manager()
        item = self.file_list.currentItem()
        if not manager or not item:
            show_error(self, "No Selection", "Select a file or folder to delete.")
            return
        name = item.data(1)
        is_dir = item.data(2)
        remote = DeviceFileManager.join_path(self.current_path, name)
        if not confirm_destructive(
            self, "Delete From Device",
            f"This will permanently delete '{remote}' from the device.",
        ):
            return
        result = manager.delete(remote, recursive=bool(is_dir), serial=self._serial())
        self.terminal.append_result_full(result)
        self.refresh()
