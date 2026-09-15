# main.py
import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from window import MainWindow

def main():
    # Performance optimization flags for fast loading and crisp UI
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    os.environ["QT_USE_PHYSICAL_DPI"] = "1"

    app = QApplication(sys.argv)
    app.setApplicationName("Parto")
    app.setApplicationVersion("0.1.0")
    
    # Placeholder for Logo/Favicon installation. 
    # To use a custom app logo, save a 'logo.png' in this directory and uncomment below.
    # logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
    # if os.path.exists(logo_path):
    #     app.setWindowIcon(QIcon(logo_path))
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()