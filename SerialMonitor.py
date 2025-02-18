from PyQt5.QtCore import QTimer, QObject, pyqtSignal, Qt
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo


# class related to monitoring Serial Port activity
class SerialPortMonitor(QObject):
    port_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_ports)
        self.timer.start(1000)  # checks current ports every 3 seconds

        self.current_ports = []  # list for storing currently available ports

    # function for checking currently available ports
    def check_ports(self):
        available_ports = self.get_ports()
        if available_ports != self.current_ports:
            self.current_ports = available_ports
            self.port_changed.emit()

    # function for fetching currently available ports
    def get_ports(self):
        return [port.portName() for port in QSerialPortInfo().availablePorts()]
