from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QVBoxLayout,
    QHBoxLayout,
    QMainWindow,
    QWidget,
    QPushButton,
    QComboBox,
    QMessageBox,
    QLabel,
    QLineEdit,
)
from PyQt5.QtWidgets import QSizePolicy, QSpacerItem, QTextEdit, QAction
from PyQt5.QtGui import QIcon
import sys
from PyQt5.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QLabel, QWidget
from single_sensor_gui import SerialDynamicPlotter
from multi_sensor_gui import MultiSensorPlotter
import os


class GuiMain(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Test Selection")
        icon = QIcon(self.resource_path("assets/sensor.ico"))
        self.setWindowIcon(icon)
        self.setFixedSize(250, 200)

        layout = QVBoxLayout()

        title_label = QLabel("Select Test Type:")
        title_label.setStyleSheet("font-size: 16px;")  # Set font size for the title
        layout.addWidget(title_label)

        self.temp_button = QPushButton("Temperature")
        self.temp_button.clicked.connect(self.on_temperature_click)
        self.temp_button.setStyleSheet(
            "padding: 10px;"
        )  # Add some padding to the button
        layout.addWidget(self.temp_button)

        self.pressure_button = QPushButton("Pressure")
        self.pressure_button.clicked.connect(self.on_pressure_click)
        self.pressure_button.setStyleSheet("padding: 10px;")
        layout.addWidget(self.pressure_button)

        self.output_label = QLabel("")  # For displaying output
        self.output_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.output_label)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def on_temperature_click(self):
        self.temperature_window = MultiSensorPlotter(parent=self)
        self.temperature_window.show()
        self.temp_button.setEnabled(False)

    def on_pressure_click(self):
        self.pressure_window = SerialDynamicPlotter(parent=self)
        self.pressure_window.show()
        self.pressure_button.setEnabled(False)

    def resource_path(self, relative_path):
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS2
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)
