import sys
import numpy as np
import pyqtgraph as pgt
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QFileDialog, QMainWindow, QWidget, QPushButton, QComboBox, QMessageBox
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
import csv


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

class SerialDynamicPlotter(QMainWindow):
    def __init__(self):
        super().__init__()                                                                          # inherit from superclass (QMainWindow)

        # initialize variables
        self.sensor_data = {}                                                                       # dictionary for storing the data
        self.com_port_names = []                                                                    # list for storing active COM ports


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

        # fetch currently available COM ports
        self.available_ports = QSerialPortInfo().availablePorts()
        self.com_port_names = [port.portName() for port in self.available_ports]

        # create drop down widgets for choosing COM port
        self.com_port_combo = QComboBox()
        self.com_port_combo.addItems([str(com) for com in self.com_port_names])
        self.com_port_combo.setCurrentIndex(0)
        self.com_port_combo.currentIndexChanged.connect(self.change_com_port)
        plot_widget_layout.addWidget(self.com_port_combo)


        # initialize and configure a QSerialPort object for serial communication
        self.serial_port = QSerialPort()
        self.serial_port.setPortName("COM11")
        self.serial_port.setBaudRate(9600)
        #self.serial_port.readyRead.connect(self.receive_serial_data)
        
    
    def add_sensor(self, name, color):
        pass

    def change_com_port(self, index):
        #self.serial_port.setPortName(self.com_port_names[index])
        self.serial_port.setPortName(self.com_port_combo.currentText())
        #self.serial_port.readyRead.connect(self.receive_serial_data)


if __name__ == "__main__":
    application = QApplication(sys.argv)                                                            # creates instance of QApplication

    viewer_window = SerialDynamicPlotter()
    viewer_window.add_sensor("P", "r")

    if viewer_window.serial_port.open(QSerialPort.ReadOnly):                                        # set to Read-only from sensors
        viewer_window.show()
        sys.exit(application.exec_())
    else:
        QMessageBox.warning(viewer_window, "Error", "Failed to establish serial port connection")
        sys.exit(1)


