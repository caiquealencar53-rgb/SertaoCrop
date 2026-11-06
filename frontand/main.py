<<<<<<< HEAD
import sys from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton,
    QVBoxLayout, QLabel
)

app = QApplication(sys.argv)

janela = QWidget()
janela.setWindowTitle("SertãoCrop")
janela.resize(800, 600)

layout = QVBoxLayout()

titulo = QLabel("Bem-vindo ao SertãoCrop")
botao = QPushButton("Nova simulação")

layout.addWidget(titulo)
layout.addWidget(botao)

janela.setLayout(layout)

janela.show()

sys.exit(app.exec())
=======
import sys
import os

from qt_core import *
from main_window.ui_main_window import *   


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        
        self.show()


if __name__ == "__main__":
    app  = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
>>>>>>> d6e51d7 (primeira janela)
