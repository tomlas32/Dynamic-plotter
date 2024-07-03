from PyQt5.QtCore import QObject, QThread, pyqtSignal, Qt
from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QComboBox
from PyQt5.QtWidgets import QLineEdit, QTextEdit, QFileDialog, QMessageBox, QLCDNumber, QSpacerItem, QSizePolicy, QAction, QIcon
import pyqtgraph as pgt
import time
import csv
import sys
import os

class DataReceiver(QObject):
    new_data = pyqtSignal(list, float)

    def __init__(self, serial_port):
        super().__init__()
        self.serial_port = serial_port
        self.is_connected = True
        self.is_paused = False


    def receive_data(self):
        while self.is_connected:
            if self.is_paused:
                continue

            self.serial_port.flush()
            while self.serial_port.canReadLine():
                try:
                    line = self.serial_port.readLine().data().decode("utf-8", errors="ignore").strip()
                    values = [float(x) for x in line.split(",")]
                    timestamp = time.time()  # Get timestamp immediately
                    self.new_data.emit(values, timestamp)
                except (UnicodeDecodeError, IndexError, ValueError):
                    pass