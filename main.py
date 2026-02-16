from PySide6.QtWidgets import QApplication, QMainWindow
import sys

from widget import Widget

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Widget()

    window.show()
    app.exec()