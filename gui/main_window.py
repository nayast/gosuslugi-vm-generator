import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QLineEdit, QPushButton, QFileDialog, QPlainTextEdit,
                               QGroupBox, QListWidget, QAbstractItemView, QSplitter)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class JSONSchemeReader(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        self.header_label = QLabel("JSON-схема")
        header_font = QFont()
        header_font.setPointSize(12)
        header_font.setBold(True)
        self.header_label.setFont(header_font)

        content_layout = QHBoxLayout()
        self.line_edit = QLineEdit()
        self.line_edit.setReadOnly(True)
        self.button = QPushButton("Загрузить...")

        content_layout.addWidget(self.line_edit)
        content_layout.addWidget(self.button)

        layout.addWidget(self.header_label)
        layout.addLayout(content_layout)

    def get_path(self):
        return self.line_edit.text()

    def set_path(self, path):
        self.line_edit.setText(path)


class JSONAppsReader(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        self.header_label = QLabel("JSON-примеры")
        header_font = QFont()
        header_font.setPointSize(12)
        header_font.setBold(True)
        self.header_label.setFont(header_font)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Добавить файл...")
        self.clear_button = QPushButton("Очистить список")
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.clear_button)

        layout.addWidget(self.header_label)
        layout.addWidget(self.list_widget)
        layout.addLayout(button_layout)

    def get_paths(self):
        paths = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item:
                paths.append(item.text())
        return paths

    def add_paths(self, paths):
        existing_paths = set(self.get_paths())
        for path in paths:
            if path not in existing_paths:
                self.list_widget.addItem(path)

    def clear_paths(self):
        self.list_widget.clear()


class XSDSchemeReader(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        self.header_label = QLabel("XSD-схема")
        header_font = QFont()
        header_font.setPointSize(12)
        header_font.setBold(True)
        self.header_label.setFont(header_font)

        content_layout = QHBoxLayout()
        self.line_edit = QLineEdit()
        self.line_edit.setReadOnly(True)
        self.button = QPushButton("Загрузить...")

        content_layout.addWidget(self.line_edit)
        content_layout.addWidget(self.button)

        layout.addWidget(self.header_label)
        layout.addLayout(content_layout)

    def get_path(self):
        return self.line_edit.text()

    def set_path(self, path):
        self.line_edit.setText(path)


class VMGeneratorBlock(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        self.header_label = QLabel("VM-шаблон")
        header_font = QFont()
        header_font.setPointSize(12)
        header_font.setBold(True)
        self.header_label.setFont(header_font)

        self.button = QPushButton("Сгенерировать шаблон")

        layout.addWidget(self.header_label)
        layout.addWidget(self.button)

    def connect_generate_signal(self, slot):
        self.button.clicked.connect(slot)


class VMTemplateViewer(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        self.header_label = QLabel("Предпросмотр VM-шаблона")
        header_font = QFont()
        header_font.setPointSize(12)
        header_font.setBold(True)
        self.header_label.setFont(header_font)

        self.text_edit = QPlainTextEdit()
        self.text_edit.setReadOnly(True)

        layout.addWidget(self.header_label)
        layout.addWidget(self.text_edit)

    def set_content(self, content):
        self.text_edit.setPlainText(content)

    def get_content(self):
        return self.text_edit.toPlainText()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Генератор VM-шаблонов")
        self.setGeometry(100, 100, 1200, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        central_layout = QHBoxLayout(central_widget)
        central_layout.addWidget(splitter)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        self.json_schema_reader = JSONSchemeReader()
        self.json_apps_reader = JSONAppsReader()
        self.xsd_scheme_reader = XSDSchemeReader()

        left_layout.addWidget(self.json_schema_reader)
        left_layout.addWidget(self.json_apps_reader)
        left_layout.addWidget(self.xsd_scheme_reader)

        self.vm_generator_block = VMGeneratorBlock()
        self.vm_generator_block.connect_generate_signal(self.generate_template)
        left_layout.addWidget(self.vm_generator_block)

        splitter.addWidget(left_widget)

        self.vm_template_viewer = VMTemplateViewer()
        splitter.addWidget(self.vm_template_viewer)

        splitter.setSizes([splitter.width() // 2, splitter.width() // 2])

        self.json_schema_reader.button.clicked.connect(self.load_form_schema)
        self.json_apps_reader.add_button.clicked.connect(self.add_example_app)
        self.json_apps_reader.clear_button.clicked.connect(self.clear_example_app)
        self.xsd_scheme_reader.button.clicked.connect(self.load_department_xsd)

    def load_form_schema(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите JSON-схему формы",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        if file_path:
            self.json_schema_reader.set_path(file_path)
            print(f"Загружена JSON-схема формы: {file_path}")

    def add_example_app(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Выберите примеры заявления (JSON)",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        if file_paths:
            self.json_apps_reader.add_paths(file_paths)
            print(f"Добавлены примеры заявления: {file_paths}")

    def clear_example_app(self):
        self.json_apps_reader.clear_paths()
        print("Список примеров заявления очищен.")

    def load_department_xsd(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите XSD-схему ведомства",
            "",
            "XSD Files (*.xsd);;All Files (*)"
        )
        if file_path:
            self.xsd_scheme_reader.set_path(file_path)
            print(f"Загружена XSD-схема ведомства: {file_path}")

    def generate_template(self):
        print("Нажата кнопка 'Сгенерировать шаблон'")
        schema_path = self.json_schema_reader.get_path()
        example_paths = self.json_apps_reader.get_paths()
        xsd_path = self.xsd_scheme_reader.get_path()

        print(f"JSON Schema Path: {schema_path}")
        print(f"Example JSON Paths: {example_paths}")
        print(f"XSD Path: {xsd_path}")