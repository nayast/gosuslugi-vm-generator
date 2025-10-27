from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QLineEdit, QPushButton, QFileDialog, QPlainTextEdit,
                               QGroupBox, QListWidget, QAbstractItemView, QSplitter, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication
import os

class JSONSchemeReader(QGroupBox):
    def __init__(self, on_state_change_callback):
        super().__init__()
        self.setTitle("JSON-схема")
        self.header_font = QFont()
        self.header_font.setPointSize(12)
        self.header_font.setBold(True)
        self.setFont(self.header_font)

        self.on_state_change_callback = on_state_change_callback

        layout = QVBoxLayout(self)
        self.line_edit = QLineEdit()
        self.line_edit.setReadOnly(True)
        self.line_edit.setVisible(False)
        self.line_edit.setStyleSheet("background-color: #E5EAF5; color: #000000; border: none;")

        layout.addWidget(self.line_edit)

        layout.addStretch()

        self.button = QPushButton("Загрузить...")
        self.button.setStyleSheet("background-color: #0D4CD3; color: #FFFFFF;")
        size_policy = self.button.sizePolicy()
        size_policy.setHorizontalPolicy(size_policy.Policy.Expanding)
        self.button.setSizePolicy(size_policy)

        layout.addWidget(self.button)

        self.button.clicked.connect(self._on_button_clicked)

    def _on_button_clicked(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите JSON-схему формы",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        if file_path:
            self.set_path(file_path)
            self.on_state_change_callback()

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
        self.label.setStyleSheet("background-color: #E5EAF5; color: #000000; border: none;")
        self.remove_button = QPushButton("✕")
        self.remove_button.setStyleSheet("background-color: transparent; color: #0D4CD3; border: none;")
        self.remove_button.setFixedSize(30, 30)

        layout.addWidget(self.label)
        layout.addWidget(self.remove_button)

        self.remove_button.clicked.connect(self._on_remove_clicked)

    def _on_remove_clicked(self):
        self.on_remove_callback(self.file_path)


class JSONAppsReader(QGroupBox):
    def __init__(self, on_state_change_callback):
        super().__init__()
        self.setTitle("JSON-примеры")
        self.header_font = QFont()
        self.header_font.setPointSize(12)
        self.header_font.setBold(True)
        self.setFont(self.header_font)

        self.on_state_change_callback = on_state_change_callback

        layout = QVBoxLayout(self)

        self.items_layout = QVBoxLayout()
        self.items_widget = QWidget()
        self.items_widget.setLayout(self.items_layout)
        self.items_widget.setVisible(False)

        layout.addWidget(self.items_widget)

        layout.addStretch()

        self.add_button = QPushButton("Добавить файл...")
        self.add_button.setStyleSheet("background-color: transparent; border: 3px dashed #0D4CD3; color: #0D4CD3;")
        size_policy = self.add_button.sizePolicy()
        size_policy.setHorizontalPolicy(size_policy.Policy.Expanding)
        self.add_button.setSizePolicy(size_policy)

        layout.addWidget(self.add_button)

        self.add_button.clicked.connect(self._on_add_clicked)
        self._file_paths = set()

    def get_paths(self):
        return list(self._file_paths)

    def     add_paths(self, paths):
        for path in paths:
            if path not in self._file_paths:
                item = JSONAppItem(path, self._on_item_removed)
                self.items_layout.addWidget(item)
                self._file_paths.add(path)

        self.items_widget.setVisible(bool(self._file_paths))
        self.on_state_change_callback()

    def _on_add_clicked(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Выберите примеры заявления (JSON)",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        if file_paths:
            self.add_paths(file_paths)

    def _on_item_removed(self, path):
        for i in range(self.items_layout.count()):
            item_widget = self.items_layout.itemAt(i).widget()
            if isinstance(item_widget, JSONAppItem) and item_widget.file_path == path:
                item_widget.setParent(None)
                self._file_paths.discard(path)
                break

        self.items_widget.setVisible(bool(self._file_paths))
        self.on_state_change_callback()


class XSDSchemeReader(QGroupBox):
    def __init__(self, on_state_change_callback):
        super().__init__()
        self.setTitle("XSD-схема")
        self.header_font = QFont()
        self.header_font.setPointSize(12)
        self.header_font.setBold(True)
        self.setFont(self.header_font)

        self.on_state_change_callback = on_state_change_callback

        layout = QVBoxLayout(self)

        self.line_edit = QLineEdit()
        self.line_edit.setReadOnly(True)
        self.line_edit.setVisible(False)
        self.line_edit.setStyleSheet("background-color: #E5EAF5; color: #000000; border: none;")

        layout.addWidget(self.line_edit)

        layout.addStretch()

        self.button = QPushButton("Загрузить...")
        self.button.setStyleSheet("background-color: #0D4CD3; color: #FFFFFF;")
        size_policy = self.button.sizePolicy()
        size_policy.setHorizontalPolicy(size_policy.Policy.Expanding)
        self.button.setSizePolicy(size_policy)

        layout.addWidget(self.button)

        self.button.clicked.connect(self._on_button_clicked)

    def _on_button_clicked(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите XSD-схему ведомства",
            "",
            "XSD Files (*.xsd);;All Files (*)"
        )
        if file_path:
            self.set_path(file_path)
            self.on_state_change_callback()

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

        self.button = QPushButton("Сгенерировать шаблон")
        size_policy = self.button.sizePolicy()
        size_policy.setHorizontalPolicy(size_policy.Policy.Expanding)
        self.button.setSizePolicy(size_policy)
        self.button.setStyleSheet("background-color: #EE3F58; color: #FFFFFF;")

        layout.addWidget(self.button)

    def connect_generate_signal(self, slot):
        self.button.clicked.connect(slot)

    def set_enabled(self, enabled):
        self.button.setEnabled(enabled)
        if enabled:
            self.button.setStyleSheet("background-color: #EE3F58; color: #FFFFFF;")
        else:
            self.button.setStyleSheet("background-color: #66727F; color: #FFFFFF;")


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
        self.text_edit.setStyleSheet("background-color: #E5EAF5; color: #000000;")

        self.button_layout = QHBoxLayout()
        self.copy_button = QPushButton("Копировать в буфер")
        self.save_button = QPushButton("Сохранить как файл...")
        self.copy_button.setVisible(False)
        self.save_button.setVisible(False)
        self.copy_button.setStyleSheet("background-color: #0D4CD3; color: #FFFFFF;")
        self.save_button.setStyleSheet("background-color: #0D4CD3; color: #FFFFFF;")

        self.button_layout.addWidget(self.copy_button)
        self.button_layout.addWidget(self.save_button)

        layout.addWidget(self.text_edit)
        layout.addLayout(self.button_layout)

    def set_content(self, content):
        self.text_edit.setPlainText(content)
        has_content = bool(content.strip())
        self.copy_button.setVisible(has_content)
        self.save_button.setVisible(has_content)

    def get_content(self):
        return self.text_edit.toPlainText()

    def connect_copy_signal(self, slot):
        self.copy_button.clicked.connect(slot)

    def connect_save_signal(self, slot):
        self.save_button.clicked.connect(slot)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Генератор VM-шаблонов")
        self.setGeometry(100, 100, 1200, 700)
        self.setStyleSheet("background-color: #FFFFFF;")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        central_layout = QHBoxLayout(central_widget)
        central_layout.addWidget(splitter)

        self.left_widget = QGroupBox()
        self.left_widget.setTitle("Загрузка файлов")
        self.left_widget.setStyleSheet("""
            QGroupBox {
                background-color: #FFFFFF;
                color: #000000;
                border: 1px solid #000000;
                border-radius: 5px;
                margin-top: 1ex;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #000000;
            }
        """)
        self.left_layout = QVBoxLayout(self.left_widget)

        self.json_schema_reader = JSONSchemeReader(self._on_file_state_changed)
        self.json_apps_reader = JSONAppsReader(self._on_file_state_changed)
        self.xsd_scheme_reader = XSDSchemeReader(self._on_file_state_changed)
        self.vm_generator_block = VMGeneratorBlock()

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
        self.vm_template_viewer.setStyleSheet("""
            QGroupBox {
                color: #000000;
                border: 1px solid #000000;
                border-radius: 5px;
                margin-top: 1ex;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #000000;
            }
        """)
        self.vm_template_viewer.connect_copy_signal(self.copy_template)
        self.vm_template_viewer.connect_save_signal(self.save_template)
        splitter.addWidget(self.vm_template_viewer)

        splitter.setSizes([splitter.width() // 2, splitter.width() // 2])

        self.vm_generator_block.connect_generate_signal(self.generate_template)
        self._on_file_state_changed()

    def _on_file_state_changed(self):
        schema_loaded = bool(self.json_schema_reader.get_path())
        examples_loaded = bool(self.json_apps_reader.get_paths())
        xsd_loaded = bool(self.xsd_scheme_reader.get_path())

        all_loaded = schema_loaded and examples_loaded and xsd_loaded
        self.vm_generator_block.set_enabled(all_loaded)

    def generate_template(self):
        schema_path = self.json_schema_reader.get_path()
        example_paths = self.json_apps_reader.get_paths()
        xsd_path = self.xsd_scheme_reader.get_path()

        missing_files = []
        files_to_clear = {'schema': False, 'examples': [], 'xsd': False}

        if schema_path and not os.path.exists(schema_path):
            missing_files.append(schema_path)
            files_to_clear['schema'] = True
        if xsd_path and not os.path.exists(xsd_path):
            missing_files.append(xsd_path)
            files_to_clear['xsd'] = True

        for path in example_paths[:]:
            if not os.path.exists(path):
                missing_files.append(path)
                files_to_clear['examples'].append(path)
                example_paths.remove(path)

        if missing_files:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setWindowTitle("Ошибка")
            msg_box.setText("Некоторые файлы не найдены:")
            msg_box.setDetailedText("\n".join(missing_files))
            msg_box.exec()

            if files_to_clear['schema']:
                self.json_schema_reader.set_path("")
            if files_to_clear['xsd']:
                self.xsd_scheme_reader.set_path("")
            if files_to_clear['examples']:
                self.json_apps_reader._file_paths = set(example_paths)
                for i in range(self.json_apps_reader.items_layout.count() - 1, -1, -1):
                    item_widget = self.json_apps_reader.items_layout.itemAt(i).widget()
                    if isinstance(item_widget, JSONAppItem) and item_widget.file_path in files_to_clear['examples']:
                        item_widget.setParent(None)
                self.json_apps_reader.items_widget.setVisible(bool(example_paths))

            self._on_file_state_changed()
            return

        #todo: поменять на логику по генерации шаблона.
        try:
            with open('gui/example.xml', 'r', encoding='utf-8') as f:
                template_content = f.read()
            self.vm_template_viewer.set_content(template_content)
        except FileNotFoundError:
            self.vm_template_viewer.set_content("Ошибка: файл 'gui/example.xml' не найден.")
        except Exception as e:
            self.vm_template_viewer.set_content(f"Ошибка при чтении шаблона: {e}")

    def copy_template(self):
        clipboard = QApplication.clipboard()
        template_text = self.vm_template_viewer.get_content()
        if template_text:
            clipboard.setText(template_text)

    def save_template(self):
        template_text = self.vm_template_viewer.get_content()
        if not template_text:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить VM-шаблон",
            "xxxxxxxxx_Applicant.vm",
            "VM Files (*.vm);;All Files (*)"
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(template_text)
            except Exception as e:
                print(f"Ошибка при сохранении шаблона: {e}")