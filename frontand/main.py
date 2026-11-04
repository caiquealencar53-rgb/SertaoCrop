import sys
from PySide6.QtWidgets import (
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