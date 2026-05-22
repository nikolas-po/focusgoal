"""Глобальные горячие клавиши"""
from PyQt5.QtWidgets import QShortcut
from PyQt5.QtGui import QKeySequence
from typing import Callable, Dict


class HotkeyManager:
    """Управление горячими клавишами в рамках окна Qt"""
    def __init__(self, widget):
        self.widget = widget
        self._shortcuts: Dict[str, QShortcut] = {}

    def register(self, key: str, callback: Callable, description: str = ""):
        shortcut = QShortcut(QKeySequence(key), self.widget)
        shortcut.activated.connect(callback)
        self._shortcuts[key] = shortcut
        return shortcut

    def unregister(self, key: str):
        if key in self._shortcuts:
            self._shortcuts[key].setEnabled(False)
            del self._shortcuts[key]

    def enable_all(self):
        for s in self._shortcuts.values():
            s.setEnabled(True)

    def disable_all(self):
        for s in self._shortcuts.values():
            s.setEnabled(False)
