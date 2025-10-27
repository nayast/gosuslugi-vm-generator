import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QLineEdit, QPushButton, QFileDialog, QPlainTextEdit,
                               QGroupBox, QListWidget, QAbstractItemView, QSplitter)
from PySide6.QtCore import Qt


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Генератор VM-шаблонов услуг")
        self.setGeometry(100, 100, 1200, 700)

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        central_layout = QHBoxLayout(central_widget)
        central_layout.addWidget(splitter)

        # --- ЛЕВЫЙ БЛОК (Загрузка файлов) ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # --- Блок 1: JSON-схема формы ---
        self.form_schema_block = self.create_file_block(
            "JSON-схема формы с Госуслуг",
            self.load_form_schema
        )
        left_layout.addWidget(self.form_schema_block)

        # --- Блок 2: Примеры заявления (JSON) ---
        self.example_app_block = self.create_multiple_files_block(
            "Примеры заявления (JSON)",
            self.add_example_app,
            self.clear_example_app
        )
        left_layout.addWidget(self.example_app_block)

        # --- Блок 3: XSD-схема ведомства ---
        self.department_xsd_block = self.create_file_block(
            "XSD-схема ведомственной системы",
            self.load_department_xsd
        )
        left_layout.addWidget(self.department_xsd_block)

        # --- Кнопка генерации ---
        self.generate_button = QPushButton("Сгенерировать шаблон")
        self.generate_button.clicked.connect(self.generate_template)
        left_layout.addWidget(self.generate_button)

        # Добавляем левый виджет в сплиттер
        splitter.addWidget(left_widget)

        # --- ПРАВЫЙ БЛОК (Предварительный просмотр) ---
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        preview_label = QLabel("Предварительный просмотр VM-шаблона:")
        preview_label.setText('''
        
                            ''')
        right_layout.addWidget(preview_label)

        self.preview_area = QPlainTextEdit()
        self.preview_area.setReadOnly(True) # Сделать область только для чтения
        right_layout.addWidget(self.preview_area)

        # Добавляем правый виджет в сплиттер
        splitter.addWidget(right_widget)

        # Опционально: Установить начальные пропорции (например, 1:1)
        splitter.setSizes([splitter.width() // 2, splitter.width() // 2])


    def create_file_block(self, label_text, load_callback):
        """Создает блок для загрузки одного файла."""
        group_box = QGroupBox(label_text)
        layout = QHBoxLayout(group_box)

        line_edit = QLineEdit()
        line_edit.setReadOnly(True) # Поле только для чтения
        layout.addWidget(line_edit)

        button = QPushButton("Загрузить...")
        button.clicked.connect(load_callback)
        layout.addWidget(button)

        # Сохраняем ссылки на элементы управления, чтобы к ним можно было обратиться позже
        group_box.line_edit = line_edit
        group_box.button = button

        return group_box

    def create_multiple_files_block(self, label_text, add_callback, clear_callback):
        """Создает блок для загрузки нескольких файлов."""
        group_box = QGroupBox(label_text)
        layout = QVBoxLayout(group_box)

        # Список для отображения загруженных файлов
        self.file_list_widget = QListWidget()
        self.file_list_widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection) # Позволяет выбирать несколько элементов
        layout.addWidget(self.file_list_widget)

        # Кнопки управления списком
        button_layout = QHBoxLayout()
        add_button = QPushButton("Добавить файл...")
        add_button.clicked.connect(add_callback)
        button_layout.addWidget(add_button)

        clear_button = QPushButton("Очистить список")
        clear_button.clicked.connect(clear_callback)
        button_layout.addWidget(clear_button)

        layout.addLayout(button_layout)

        # Сохраняем ссылки
        group_box.list_widget = self.file_list_widget
        group_box.add_button = add_button
        group_box.clear_button = clear_button

        return group_box

    # --- Функции-заглушки для обработчиков ---
    def load_form_schema(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите JSON-схему формы",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        if file_path:
            self.form_schema_block.line_edit.setText(file_path)
            print(f"Загружена JSON-схема формы: {file_path}")

    def add_example_app(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Выберите примеры заявления (JSON)",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        if file_paths:
            for path in file_paths:
                items = []
                for i in range(self.example_app_block.list_widget.count()):
                    items.append(self.example_app_block.list_widget.item(i).text())
                if path not in items:
                    self.example_app_block.list_widget.addItem(path)
            print(f"Добавлены примеры заявления: {file_paths}")

    def clear_example_app(self):
        self.example_app_block.list_widget.clear()
        print("Список примеров заявления очищен.")

    def load_department_xsd(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите XSD-схему ведомства",
            "",
            "XSD Files (*.xsd);;All Files (*)"
        )
        if file_path:
            self.department_xsd_block.line_edit.setText(file_path)
            print(f"Загружена XSD-схема ведомства: {file_path}")

    def generate_template(self):
        print("Нажата кнопка 'Сгенерировать шаблон'")
        # Здесь будет вызов логики генерации
        # После генерации результат можно отобразить в self.preview_area
        # self.preview_area.setPlainText("Сгенерированный VM-шаблон появится здесь...")


app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())