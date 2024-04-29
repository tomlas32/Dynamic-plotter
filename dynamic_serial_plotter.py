import sys
import numpy as np
import pyqtgraph as pgt
from PyQt5.QtCore import QTimer, QObject, pyqtSignal
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QFileDialog, QMainWindow, QWidget, QPushButton, QComboBox, QMessageBox, QLabel
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
import csv
import time


#define buffer - using circular approach
class CircularBuffer:
    # constructor for circular buffer
    def __init__(self, max_size):
        self.max_size = max_size
        self.buffer = np.zeros(max_size)
        self.index = 0
        self.full = False

    # get function for fetching data from the buffer
    def get_data(self):
        if self.full:
            return np.concatenate((self.buffer[self.index:], self.buffer[:self.index]))
        else:
            return self.buffer[:self.index]

    # push function for adding data to the buffer
    def push(self, value):
        self.buffer[self.index] = value                                                             # assigns pushed value to the current index element in the numpy list
        self.index = (self.index + 1) % self.max_size                                               # increment index and checks if buffer was filled 
        if self.index == 0:
            self.full = True  


# class related to monitoring Serial Port activity 
class SerialPortMonitor(QObject):
    port_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_ports)
        self.timer.start(1000)                                                                      # checks current ports every 3 seconds

        self.current_ports = []                                                                     # list for storing currently available ports
    
    # function for checking currently available ports
    def check_ports(self):
        available_ports = self.get_ports()
        if available_ports != self.current_ports:
            self.current_ports = available_ports
            self.port_changed.emit()
    
    # function for fetching currently available ports
    def get_ports(self):
        return [port.portName() for port in QSerialPortInfo().availablePorts()]


class SerialDynamicPlotter(QMainWindow):
    def __init__(self):
        super().__init__()                                                                          # inherit from superclass (QMainWindow)

        # initialize variables
        self.sensor_data = {}                                                                       # dictionary for storing the data
        self.com_port_names = []                                                                    # list for storing active COM ports
        self.data_records = []                                                                      # list for storing sensor data for export
        self.buffer_size = 7000
        self.is_connected = False
        self.is_paused = False


        # define GUI window dimentions characteristics
        self.setWindowTitle("Serial Port Dynamic Viewer")
        self.setGeometry(100, 100, 1024, 768)

        # define plot area widget characteristics
        self.plot_widget = pgt.PlotWidget()
        self.plot_widget.setBackground("#000000")
        self.plot_widget.setLabel("left", "Value")
        self.plot_widget.setLabel("bottom", "Time")
        self.plot_widget.showGrid(True, True)
        self.plot_widget.setMouseEnabled(x=True, y=False)
        self.plot_widget.setClipToView(True)

        # build the viewer widgets
        plot_widget_layout = QVBoxLayout()                                                          # vertical layout
        viewer_widget = QWidget()                                                                   # viewer widget
        plot_widget_layout.addWidget(self.plot_widget)
        viewer_widget.setLayout(plot_widget_layout)
        self.setCentralWidget(viewer_widget)

        # create drop down widgets for choosing COM port
        self.com_port_combo = QComboBox()
        plot_widget_layout.addWidget(self.com_port_combo)

        # create connect button for establishing serial communication
        self.connect_button = QPushButton("Connect")
        self.status_label = QLabel("")                                                              # reporting on successful connection/disconnection
        plot_widget_layout.addWidget(self.connect_button)
        plot_widget_layout.addWidget(self.status_label)
        self.connect_button.clicked.connect(self.toggle_connect)

        # create instance of serial monitor
        self.serial_monitor = SerialPortMonitor()
        self.serial_monitor.port_changed.connect(self.update_com_port_combo)
        self.update_com_port_combo()
        
        # initialize and configure a QSerialPort object for serial communication
        self.serial_port = QSerialPort()
        self.serial_port.setBaudRate(9600)
        self.start_time = time.time()
        self.serial_port.readyRead.connect(self.receive_data)

    def update_com_port_combo(self):
        current_port = self.com_port_combo.currentText()
        self.com_port_combo.clear()
        for port_name in self.serial_monitor.current_ports:
            self.com_port_combo.addItem(port_name)
        if current_port in self.serial_monitor.current_ports:
            self.com_port_combo.setCurrentText(current_port)   
    
    def add_sensor(self, name, color):
        self.sensor_data[name] = {
            'buffer': CircularBuffer(self.buffer_size),
            'plot_data': self.plot_widget.plot(pen=pgt.mkPen(color, width=2), name=name),
        }

    def change_com_port(self, index):
        #self.serial_port.setPortName(self.com_port_names[index])
        self.serial_port.setPortName(self.com_port_combo.currentText())
        #self.serial_port.readyRead.connect(self.receive_serial_data)

    # define toggle function for switching between connect and pause states
    def toggle_connect(self):
        if self.connect_button.text() == "Connect":
            port_name = self.com_port_combo.currentText()
            self.serial_port.setPortName(port_name)
            if not self.serial_port.isOpen():  # Check if the port is not already open
                if self.serial_port.open(QSerialPort.ReadOnly):
                    self.port_connect()
                    self.connect_button.setText("Pause")
                    self.status_label.setText("Connected to " + port_name)
                else:
                    self.status_label.setText("Failed to connect to " + port_name)
            else:
                self.status_label.setText("Port already open")
        else:
            self.port_pause()
            self.serial_port.close()  # Close the port when pausing
            self.connect_button.setText("Connect")

    # function for establishing serial communication
    def port_connect(self):
        self.is_paused = False
        self.is_connected = True
    
    # function for pausing data stream and plotting
    def port_pause(self):
        self.is_paused = True
        self.is_connected = True

    # function to receive serial data
    def receive_data(self):
        
        while self.serial_port.canReadLine():
            try:
                data = self.serial_port.readLine().data().decode("utf-8").strip()
                values = data.split(", ")
                sensor_name = "P"
                sensor_value = float(values[4].strip())
                formatted_value = "{:.2f}".format(sensor_value)
                if sensor_name in self.sensor_data and self.is_connected and not self.is_paused:
                    data_buffer = self.sensor_data[sensor_name]['buffer']
                    data_buffer.push(formatted_value)
                    self.sensor_data[sensor_name]['plot_data'].setData(data_buffer.get_data())
                    timestamp = format(float(time.time() - self.start_time), ".2f")
                    self.data_records.append([sensor_name, timestamp, formatted_value])
                    time.sleep(0.01)
            except(UnicodeDecodeError, IndexError, ValueError):
                pass


if __name__ == "__main__":
    application = QApplication(sys.argv)                                                            # creates instance of QApplication
    viewer_window = SerialDynamicPlotter()
    viewer_window.add_sensor("P", "r")
    viewer_window.show()
    sys.exit(application.exec_())
    # if viewer_window.serial_port.open(QSerialPort.ReadOnly):                                        # set to Read-only from sensors
    #     viewer_window.show()
    #     sys.exit(application.exec_())
    # else:
    #     QMessageBox.warning(viewer_window, "Error", "Failed to establish serial port connection")
    #     sys.exit(1)


