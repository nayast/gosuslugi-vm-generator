import sys
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout

class MyWidgetBlock(QWidget):
    def __init__(self):
        super().__init__()

        # Устанавливаем белый фон для блока
        self.setStyleSheet("background-color: white;")

        # Создаем layout для вертикального размещения
        layout = QVBoxLayout()

        # QLabel сверху
        label = QLabel("Это подпись сверху")
        layout.addWidget(label)
        label.setStyleSheet("color: #000000;")

        # QLineEdit посередине
        line_edit = QLineEdit("Текст в поле ввода")
        layout.addWidget(line_edit)

        # QPushButton внизу
        button = QPushButton("Кнопка")
        button.setStyleSheet("background-color: #000000;")
        layout.addWidget(button)

        # Применяем layout к виджету
        self.setLayout(layout)

# Пример использования
app = QApplication(sys.argv)

widget_block = MyWidgetBlock()
widget_block.show()

sys.exit(app.exec())