import sys
from PyQt5.QtWidgets import QApplication
from dynamic_serial_plotter import SerialDynamicPlotter

if __name__ == "__main__":
    application = QApplication(sys.argv)                                                            # creates instance of QApplication
    viewer_window = SerialDynamicPlotter()
    viewer_window.add_sensor("P", "r")
    viewer_window.show()
    sys.exit(application.exec_())