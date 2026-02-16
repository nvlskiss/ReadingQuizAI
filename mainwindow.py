from PySide6.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QVBoxLayout
import sys




class MainWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setWindowTitle("AI Question Generator")
        
        # Language checkbox
        Question_Widget = WidgetSetting()


        #Menu bar - File, Help
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&Notebook")


        # new, save, quit
        new_file_action = file_menu.addAction("New Notebook")
        save_file_action = file_menu.addAction("Save Notebook")
        quit_action = file_menu.addAction("Quit")


        self.setCentralWidget(Question_Widget)


