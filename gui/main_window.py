from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QLineEdit, QPushButton, QFileDialog, QPlainTextEdit,
                               QGroupBox, QListWidget, QAbstractItemView, QSplitter)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class JSONSchemeReader(QGroupBox):
    def __init__(self):
        super().__init__()
        self.setTitle("JSON-схема")
        self.header_font = QFont()
        self.header_font.setPointSize(12)
        self.header_font.setBold(True)
        self.setFont(self.header_font)

        layout = QVBoxLayout(self)
        layout.addStretch() # Растягивающий элемент сверху

        self.line_edit = QLineEdit()
        self.line_edit.setReadOnly(True)
        self.line_edit.setVisible(False)

        self.button = QPushButton("Загрузить...")
        size_policy = self.button.sizePolicy()
        size_policy.setHorizontalPolicy(size_policy.Policy.Expanding) # Растягивание по ширине
        self.button.setSizePolicy(size_policy)

        layout.addWidget(self.line_edit)
        layout.addWidget(self.button, alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom) # Выравнивание содержимого

    def get_path(self):
        return self.line_edit.text()

    def set_path(self, path):
        self.line_edit.setText(path)
        self.line_edit.setVisible(bool(path))


class JSONAppItem(QWidget):
    def __init__(self, file_path, on_remove_callback):
        super().__init__()
        self.file_path = file_path
        self.on_remove_callback = on_remove_callback

        layout = QHBoxLayout(self)
        self.label = QLabel(file_path)
        self.remove_button = QPushButton("✕")
        self.remove_button.setFixedSize(30, 30)

        layout.addWidget(self.label)
        layout.addWidget(self.remove_button)

        self.remove_button.clicked.connect(self._on_remove_clicked)

    def _on_remove_clicked(self):
        self.on_remove_callback(self.file_path)


class JSONAppsReader(QGroupBox):
    def __init__(self):
        super().__init__()
        self.setTitle("JSON-примеры")
        self.header_font = QFont()
        self.header_font.setPointSize(12)
        self.header_font.setBold(True)
        self.setFont(self.header_font)

        layout = QVBoxLayout(self)
        layout.addStretch() # Растягивающий элемент сверху

        self.items_layout = QVBoxLayout()
        self.items_widget = QWidget()
        self.items_widget.setLayout(self.items_layout)
        self.items_widget.setVisible(False)

        self.add_button = QPushButton("Добавить файл...")
        size_policy = self.add_button.sizePolicy()
        size_policy.setHorizontalPolicy(size_policy.Policy.Expanding) # Растягивание по ширине
        self.add_button.setSizePolicy(size_policy)

        layout.addWidget(self.items_widget)
        layout.addWidget(self.add_button, alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom) # Выравнивание содержимого

        self.add_button.clicked.connect(self._on_add_clicked)
        self._file_paths = set()

    def get_paths(self):
        return list(self._file_paths)

    def add_paths(self, paths):
        for path in paths:
            if path not in self._file_paths:
                item = JSONAppItem(path, self._on_item_removed)
                self.items_layout.addWidget(item)
                self._file_paths.add(path)

        self.items_widget.setVisible(bool(self._file_paths))

    def _on_add_clicked(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Выберите примеры заявления (JSON)",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        if file_paths:
            self.add_paths(file_paths)
            print(f"Добавлены примеры заявления: {file_paths}")

    def _on_item_removed(self, path):
        for i in range(self.items_layout.count()):
            item_widget = self.items_layout.itemAt(i).widget()
            if isinstance(item_widget, JSONAppItem) and item_widget.file_path == path:
                item_widget.setParent(None)
                self._file_paths.discard(path)
                break

        self.items_widget.setVisible(bool(self._file_paths))


class XSDSchemeReader(QGroupBox):
    def __init__(self):
        super().__init__()
        self.setTitle("XSD-схема")
        self.header_font = QFont()
        self.header_font.setPointSize(12)
        self.header_font.setBold(True)
        self.setFont(self.header_font)

        layout = QVBoxLayout(self)
        layout.addStretch() # Растягивающий элемент сверху

        self.line_edit = QLineEdit()
        self.line_edit.setReadOnly(True)
        self.line_edit.setVisible(False)

        self.button = QPushButton("Загрузить...")
        size_policy = self.button.sizePolicy()
        size_policy.setHorizontalPolicy(size_policy.Policy.Expanding) # Растягивание по ширине
        self.button.setSizePolicy(size_policy)

        layout.addWidget(self.line_edit)
        layout.addWidget(self.button, alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom) # Выравнивание содержимого

    def get_path(self):
        return self.line_edit.text()

    def set_path(self, path):
        self.line_edit.setText(path)
        self.line_edit.setVisible(bool(path))


class VMGeneratorBlock(QGroupBox):
    def __init__(self):
        super().__init__()
        self.setTitle("VM-шаблон")
        self.header_font = QFont()
        self.header_font.setPointSize(12)
        self.header_font.setBold(True)
        self.setFont(self.header_font)

        layout = QVBoxLayout(self)
        layout.addStretch() # Растягивающий элемент сверху
        layout.setContentsMargins(9, 25, 9, 9) # Уменьшаем отступы

        self.button = QPushButton("Сгенерировать шаблон")
        size_policy = self.button.sizePolicy()
        size_policy.setHorizontalPolicy(size_policy.Policy.Expanding) # Растягивание по ширине
        self.button.setSizePolicy(size_policy)

        layout.addWidget(self.button, alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom) # Выравнивание содержимого

    def connect_generate_signal(self, slot):
        self.button.clicked.connect(slot)


class VMTemplateViewer(QGroupBox):
    def __init__(self):
        super().__init__()
        self.setTitle("Предпросмотр VM-шаблона")
        self.header_font = QFont()
        self.header_font.setPointSize(12)
        self.header_font.setBold(True)
        self.setFont(self.header_font)

        layout = QVBoxLayout(self)

        self.text_edit = QPlainTextEdit()
        self.text_edit.setReadOnly(True)

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

        self.left_widget = QGroupBox()
        self.left_widget.setTitle("Загрузка файлов")
        self.left_layout = QVBoxLayout(self.left_widget)

        self.json_schema_reader = JSONSchemeReader()
        self.json_apps_reader = JSONAppsReader()
        self.xsd_scheme_reader = XSDSchemeReader()
        self.vm_generator_block = VMGeneratorBlock()

        # Устанавливаем политику размера для минимизации высоты блоков
        json_schema_size_policy = self.json_schema_reader.sizePolicy()
        json_schema_size_policy.setVerticalPolicy(json_schema_size_policy.Policy.Minimum)
        self.json_schema_reader.setSizePolicy(json_schema_size_policy)

        json_apps_size_policy = self.json_apps_reader.sizePolicy()
        json_apps_size_policy.setVerticalPolicy(json_apps_size_policy.Policy.Minimum)
        self.json_apps_reader.setSizePolicy(json_apps_size_policy)

        xsd_scheme_size_policy = self.xsd_scheme_reader.sizePolicy()
        xsd_scheme_size_policy.setVerticalPolicy(xsd_scheme_size_policy.Policy.Minimum)
        self.xsd_scheme_reader.setSizePolicy(xsd_scheme_size_policy)

        vm_gen_size_policy = self.vm_generator_block.sizePolicy()
        vm_gen_size_policy.setVerticalPolicy(vm_gen_size_policy.Policy.Minimum)
        self.vm_generator_block.setSizePolicy(vm_gen_size_policy)

        self.left_layout.addWidget(self.json_schema_reader)
        self.left_layout.addWidget(self.json_apps_reader)
        self.left_layout.addWidget(self.xsd_scheme_reader)
        self.left_layout.addWidget(self.vm_generator_block)

        splitter.addWidget(self.left_widget)

        self.vm_template_viewer = VMTemplateViewer()
        splitter.addWidget(self.vm_template_viewer)

        splitter.setSizes([splitter.width() // 2, splitter.width() // 2])

        self.json_schema_reader.button.clicked.connect(self.load_form_schema)
        self.xsd_scheme_reader.button.clicked.connect(self.load_department_xsd)
        self.vm_generator_block.connect_generate_signal(self.generate_template)

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