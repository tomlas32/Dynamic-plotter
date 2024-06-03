import sys
import numpy as np
import pyqtgraph as pgt
from PyQt5.QtCore import QTimer, QObject, pyqtSignal, Qt
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QHBoxLayout, QFileDialog, QMainWindow, QWidget, QPushButton, QComboBox, QMessageBox, QLabel, QLCDNumber, QLineEdit
from PyQt5.QtWidgets import QSizePolicy, QSpacerItem
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
import csv
import time
import database as db


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


        ########## define GUI window dimentions characteristics #########################
        self.setWindowTitle("Serial Port Dynamic Viewer")
        self.setFixedSize(1024, 500)

        ########## define plot area widget characteristics ##############################
        self.plot_widget = pgt.PlotWidget()
        self.plot_widget.setBackground("#000000")
        self.plot_widget.setLabel("left", "Value")
        self.plot_widget.setLabel("bottom", "Time")
        self.plot_widget.showGrid(True, True)
        self.plot_widget.setMouseEnabled(x=True, y=False)
        self.plot_widget.setClipToView(True)

        ########## build the viewer widgets #############################################
        self.main_layout = QHBoxLayout()                                                                 # main layout to store 2 VBoxes
        self.window = QWidget()                                                                          # main window

        # left panel Widgets
        self.left_layout = QVBoxLayout()                                                                
        self.left_panel = QWidget()                                                                    
        self.left_panel.setLayout(self.left_layout)
        self.left_layout.addWidget(self.plot_widget)     

        # right panel Widgets
        self.right_layout = QVBoxLayout()                                                                # layout for data entry
        self.right_panel = QWidget()
        self.right_panel.setLayout(self.right_layout)

        # initilize right panel layouts for storing widgets
        self.exp_layout = QHBoxLayout()
        self.sample_layout = QHBoxLayout()
        self.buttons_layout = QHBoxLayout()
        self.LCD_layout = QVBoxLayout()
        self.COM_layout = QVBoxLayout()
        self.top_container = QVBoxLayout()
        self.top_container_widget = QWidget()
        self.top_container_widget.setLayout(self.top_container)

        # create spacers for adjusting layout positions
        spacer_1 = QSpacerItem(300, 50, QSizePolicy.Fixed, QSizePolicy.Fixed)
        spacer_2 = QSpacerItem(300, 50, QSizePolicy.Fixed, QSizePolicy.Fixed)

        # add to right panel layouts
        self.top_container.addLayout(self.LCD_layout)
        self.top_container.addSpacerItem(spacer_1)
        self.top_container.addLayout(self.exp_layout)
        self.top_container.addLayout(self.sample_layout)
        self.top_container.addSpacerItem(spacer_2)
        self.top_container.addLayout(self.COM_layout)
        self.top_container.addLayout(self.buttons_layout)
        self.top_container.addSpacerItem(spacer_2)

        self.right_layout.addWidget(self.top_container_widget, alignment=Qt.AlignTop)
        
        # LCD widget and label
        self.LCD_layout.addWidget(QLabel("Current Sensor Value (mbar)"))
        self.LCD_display = QLCDNumber()
        self.LCD_display.setFixedHeight(80)
        self.LCD_display.setFixedWidth(300)
        self.LCD_display.setDigitCount(8)
        self.LCD_layout.addWidget(self.LCD_display)

        # experiment label and input field
        self.exp_layout.addWidget(QLabel("Experiment Name"))
        self.exp_input = QLineEdit()
        self.exp_input.setFixedWidth(200)
        self.exp_layout.addWidget(self.exp_input)
        self.exp_input.textChanged.connect(self.check_condition)

        # sample rate label and input field
        self.sample_layout.addWidget(QLabel("Cartridge"))
        self.sample_input = QLineEdit()
        self.sample_input.setFixedWidth(200)
        self.sample_layout.addWidget(self.sample_input)

        # created COM label and dropdown field and add to layout
        self.com_port_combo = QComboBox()
        self.COM_layout.addWidget(QLabel("Select COM Port"))
        self.COM_layout.addWidget(self.com_port_combo)

        # create connect and export buttons and add to layout
        self.connect_button = QPushButton("Connect")
        self.buttons_layout.addWidget(self.connect_button)
        self.connect_button.setEnabled(False)
        self.connect_button.clicked.connect(self.toggle_connect)

        self.export_button = QPushButton("Export")
        self.buttons_layout.addWidget(self.export_button)
        self.export_button.clicked.connect(self.export_helper)

        # add to main layout
        self.main_layout.addWidget(self.left_panel)                                                  
        self.main_layout.addWidget(self.right_panel) 

        # set main window layout
        self.window.setLayout(self.main_layout)
        self.setCentralWidget(self.window)                                                               # set the main widget as the centre of the application gui    

        # create connect button for establishing serial communication
        self.status_label = QLabel("")                                                              # reporting on successful connection/disconnection
        self.left_layout.addWidget(self.status_label)

        # database entry confirmation message
        self.db_message = QLabel("")
        self.top_container.addWidget(self.db_message)

        # create instance of serial monitor
        self.serial_monitor = SerialPortMonitor()
        self.serial_monitor.port_changed.connect(self.update_com_port_combo)
        self.update_com_port_combo()
        
        # initialize and configure a QSerialPort object for serial communication
        self.serial_port = QSerialPort()
        self.serial_port.setBaudRate(9600)
        self.serial_port.readyRead.connect(self.receive_data)

    # function for checking if all condition for establishin connection are met
    def check_condition(self):
        exp_name = self.exp_input.text()
        comport_index = self.com_port_combo.currentText()

        if len(exp_name.strip()) and len(comport_index) > 0:
            self.connect_button.setEnabled(True)
        else:
            self.connect_button.setEnabled(False)
               

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

    def change_com_port(self):
        self.serial_port.setPortName(self.com_port_combo.currentText())

    # define toggle function for switching between connect and pause states
    def toggle_connect(self):
        if self.connect_button.text() == "Connect" or self.connect_button.text() == "Resume":
            port_name = self.com_port_combo.currentText()
            self.serial_port.setPortName(port_name)
            if not self.serial_port.isOpen():  # Check if the port is not already open
                if self.serial_port.open(QSerialPort.ReadOnly):
                    self.port_connect()
                    self.connect_button.setText("Pause")
                    self.status_label.setText("Connected to " + port_name)
                else:
                    self.status_label.setText("Failed to connect to COM port")
            else:
                self.status_label.setText("Port already open")
        else:
            self.port_pause()
            self.serial_port.close()  # Close the port when pausing
            self.connect_button.setText("Resume")

    # function for establishing serial communication
    def port_connect(self):
        self.is_paused = False
        self.is_connected = True
        self.start_time = time.time()
    
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
                self.LCD_display.display(formatted_value)
            except(UnicodeDecodeError, IndexError, ValueError):
                pass
    # define a helper function for exporting data and saving it into database
    def export_helper(self):
        measurements = self.data_records
        experiment_name = self.exp_input.text()
        cartridge_number = self.sample_input.text()
        message = db.store_measurements(experiment_name, cartridge_number, measurements)
        self.db_message.setText(message)
        self.export_data()
        
    def export_data(self):
        if len(self.data_records) > 0:
            filename, _ = QFileDialog.getSaveFileName(self, "Export Data", "", "CSV Files (*.csv)")
            if filename:
                try:
                    with open(filename, "w", newline="") as file:
                        writer = csv.writer(file)
                        writer.writerow(["Sensor", "Time", "Value"])
                        writer.writerows(self.data_records)
                    QMessageBox.information(self, "Success", "Data successfully exported to " + filename)
                except Exception as e:
                    QMessageBox.warning(self, "Error", "Failed to export data: " + str(e))
            else:
                QMessageBox.warning(self, "Export error", "Invalid file name.")
        else:
            QMessageBox.warning(self, "Export error", "No data to export.")
    

if __name__ == "__main__":
    application = QApplication(sys.argv)                                                            # creates instance of QApplication
    viewer_window = SerialDynamicPlotter()
    viewer_window.add_sensor("P", "r")
    viewer_window.show()
    sys.exit(application.exec_())
    # if viewer_window.serial_port.open(QSerialPort.ReadOnly):                                      # set to Read-only from sensors
    #     viewer_window.show()
    #     sys.exit(application.exec_())
    # else:
    #     QMessageBox.warning(viewer_window, "Error", "Failed to establish serial port connection")
    #     sys.exit(1)


