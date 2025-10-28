from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QLineEdit, QPushButton, QFileDialog, QPlainTextEdit,
                               QGroupBox, QListWidget, QAbstractItemView, QSplitter, QMessageBox, QMenuBar)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPalette, QColor, QSyntaxHighlighter, QTextCharFormat, QBrush, QFontDatabase
from PySide6.QtWidgets import QApplication
import os
import json
import sys
import core.mid_vm
import re


class JSONSchemeReader(QWidget):
    def __init__(self, on_state_change_callback):
        super().__init__()
        self.on_state_change_callback = on_state_change_callback

        self.setStyleSheet("""
            QWidget {
                background-color: #FFFFFF;
                border-radius: 4px;
                padding: 5px;
            }
        """)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.header_label = QLabel("JSON-схема")
        header_font = QFont("Lato", 14, QFont.Weight.Bold)
        self.header_label.setFont(header_font)
        self.header_label.setStyleSheet("color: #556371; padding: 5px; border: none;")

        self.line_edit = QLineEdit()
        self.line_edit.setReadOnly(True)
        self.line_edit.setVisible(False)
        self.line_edit.setStyleSheet("background-color: #E5EAF5; color: #000000; border: none; font-family: 'Lato'; font-weight: bold;")

        self.button = QPushButton("Загрузить...")
        self.button.setStyleSheet("""
            QPushButton {
                background-color: #0D4CD3;
                color: #FFFFFF;
                border: none;
                padding: 12px 10px; /* Увеличенный отступ для высоты */
                border-radius: 8px;
                outline: none;
                font-family: 'Lato';
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0A3C9F;
            }
            QPushButton:pressed {
                background-color: #082F7F;
            }
        """)
        size_policy = self.button.sizePolicy()
        size_policy.setHorizontalPolicy(size_policy.Policy.Expanding)
        self.button.setSizePolicy(size_policy)

        self.layout.addWidget(self.header_label)
        self.layout.addWidget(self.line_edit)
        self.layout.addWidget(self.button)

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
        self.label.setStyleSheet("background-color: #E5EAF5; color: #000000; border: none; font-family: 'Lato'; font-weight: bold;")
        self.remove_button = QPushButton("✕")
        self.remove_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #0D4CD3;
                border: none;
                border-radius: 15px;
                font-family: 'Lato';
                font-weight: bold;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #E5EAF5;
            }
        """)
        self.remove_button.setFixedSize(30, 30)

        layout.addWidget(self.label)
        layout.addWidget(self.remove_button)

        self.remove_button.clicked.connect(self._on_remove_clicked)

    def _on_remove_clicked(self):
        self.on_remove_callback(self.file_path)


class JSONAppsReader(QWidget):
    def __init__(self, on_state_change_callback):
        super().__init__()
        self.on_state_change_callback = on_state_change_callback

        self.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 4px;
                padding: 5px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        header_layout = QHBoxLayout()
        self.header_label = QLabel("JSON-примеры (необязательно)")
        header_font = QFont("Lato", 14, QFont.Weight.Bold)
        self.header_label.setFont(header_font)
        self.header_label.setStyleSheet("color: #556371; padding: 5px; border: none;")

        self.toggle_button = QPushButton(">")
        self.toggle_button.setCheckable(True)
        self.toggle_button.setVisible(False) # Скрываем по умолчанию
        self.toggle_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #0D4CD3;
                border: none;
                font-family: 'Lato';
                font-weight: bold;
                font-size: 12pt;
                width: 20px;
                height: 20px;
            }
        """)
        self.toggle_button.setFixedSize(20, 20)

        header_layout.addWidget(self.header_label)
        header_layout.addStretch()
        header_layout.addWidget(self.toggle_button)

        layout.addLayout(header_layout)

        self.items_widget = QWidget()
        self.items_widget.setStyleSheet("background-color: transparent; border: none;")
        self.items_layout = QVBoxLayout(self.items_widget)
        self.items_layout.setContentsMargins(0, 0, 0, 0)
        self.items_widget.setVisible(False)
        layout.addWidget(self.items_widget)

        self.add_button = QPushButton("Добавить файл...")
        self.add_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 3px dashed #0D4CD3;
                color: #0D4CD3;
                font-family: 'Lato';
                font-weight: bold;
                border-radius: 4px;
            }
        """)
        size_policy = self.add_button.sizePolicy()
        size_policy.setHorizontalPolicy(size_policy.Policy.Expanding)
        self.add_button.setSizePolicy(size_policy)
        layout.addWidget(self.add_button)

        self.add_button.clicked.connect(self._on_add_clicked)
        self._file_paths = set()
        self._items_widgets_map = {}

        self.toggle_button.clicked.connect(self._toggle_items_visibility)

    def _toggle_items_visibility(self):
        is_checked = self.toggle_button.isChecked()
        self.items_widget.setVisible(is_checked)
        self.toggle_button.setText("v" if is_checked else ">")

    def get_paths(self):
        return list(self._file_paths)

    def add_paths(self, paths):
        for path in paths:
            if path not in self._file_paths:
                item = JSONAppItem(path, self._on_item_removed)
                self.items_layout.addWidget(item)
                self._file_paths.add(path)
                self._items_widgets_map[path] = item

        has_files = bool(self._file_paths)
        self.items_widget.setVisible(has_files and self.toggle_button.isChecked())
        self.toggle_button.setVisible(has_files) # Показываем кнопку, если есть файлы
        self.toggle_button.setEnabled(has_files)
        if not has_files:
            self.toggle_button.setChecked(False) # Сбрасываем состояние
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
        item_widget = self._items_widgets_map.get(path)
        if item_widget:
            item_widget.setParent(None)
            del self._items_widgets_map[path]
        self._file_paths.discard(path)

        has_files = bool(self._file_paths)
        if not has_files:
            self.toggle_button.setChecked(False)
            self.items_widget.setVisible(False)
            self.toggle_button.setVisible(False) # Скрываем кнопку
            self.toggle_button.setEnabled(False)
        else:
            self.items_widget.setVisible(self.toggle_button.isChecked())

        self.on_state_change_callback()

    def clear_all(self):
        for item_widget in self._items_widgets_map.values():
            item_widget.setParent(None)
        self._items_widgets_map.clear()
        self._file_paths.clear()
        self.toggle_button.setChecked(False)
        self.items_widget.setVisible(False)
        self.toggle_button.setVisible(False) # Скрываем кнопку
        self.toggle_button.setEnabled(False)
        self.on_state_change_callback()

    def set_paths(self, paths):
        self.clear_all()
        self.add_paths(paths)


class XSDSchemeReader(QWidget):
    def __init__(self, on_state_change_callback):
        super().__init__()
        self.on_state_change_callback = on_state_change_callback

        self.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 4px;
                padding: 5px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.header_label = QLabel("XSD-схема")
        header_font = QFont("Lato", 14, QFont.Weight.Bold)
        self.header_label.setFont(header_font)
        self.header_label.setStyleSheet("color: #556371; padding: 5px; border: none;")

        layout.addWidget(self.header_label)

        self.line_edit = QLineEdit()
        self.line_edit.setReadOnly(True)
        self.line_edit.setVisible(False)
        self.line_edit.setStyleSheet("background-color: #E5EAF5; color: #000000; border: none; font-family: 'Lato'; font-weight: bold;")
        layout.addWidget(self.line_edit)

        self.button = QPushButton("Загрузить...")
        self.button.setStyleSheet("""
            QPushButton {
                background-color: #0D4CD3;
                color: #FFFFFF;
                border: none;
                padding: 12px 10px; /* Увеличенный отступ для высоты */
                border-radius: 8px;
                outline: none;
                font-family: 'Lato';
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0A3C9F;
            }
            QPushButton:pressed {
                background-color: #082F7F;
            }
        """)
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


class VMGeneratorBlock(QWidget):
    def __init__(self):
        super().__init__()

        self.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 4px;
                padding: 5px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.header_label = QLabel("VM-шаблон")
        header_font = QFont("Lato", 14, QFont.Weight.Bold)
        self.header_label.setFont(header_font)
        self.header_label.setStyleSheet("color: #556371; padding: 5px; border: none;")

        layout.addWidget(self.header_label)

        self.button = QPushButton("Сгенерировать шаблон")
        size_policy = self.button.sizePolicy()
        size_policy.setHorizontalPolicy(size_policy.Policy.Expanding)
        self.button.setSizePolicy(size_policy)
        self.button.setStyleSheet("""
            QPushButton {
                background-color: #2DC36A;
                color: #FFFFFF;
                border: none;
                padding: 12px 10px; /* Увеличенный отступ для высоты */
                border-radius: 8px;
                outline: none;
                font-family: 'Lato';
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #26A85A;
            }
            QPushButton:pressed {
                background-color: #1F8C4A;
            }
            QPushButton:disabled {
                background-color: #66727F;
            }
        """)
        layout.addWidget(self.button)

    def connect_generate_signal(self, slot):
        self.button.clicked.connect(slot)

    def set_enabled(self, enabled):
        self.button.setEnabled(enabled)


class VMSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(QColor("#888888"))

        self.directive_format = QTextCharFormat()
        self.directive_format.setForeground(QColor("#00AA00"))

        self.variable_format = QTextCharFormat()
        self.variable_format.setForeground(QColor("#800080"))

        self.tag_format = QTextCharFormat()
        self.tag_format.setForeground(QColor("#0000FF"))

        self.attribute_format = QTextCharFormat()
        self.attribute_format.setForeground(QColor("#FFA500"))

    def highlightBlock(self, text):
        self.setFormat(0, len(text), QTextCharFormat())

        comment_start = 0
        while comment_start < len(text):
            comment_start = text.find('#*', comment_start)
            if comment_start == -1:
                break
            comment_end = text.find('*#', comment_start + 2)
            if comment_end == -1:
                comment_end = len(text)
            else:
                comment_end += 2
            self.setFormat(comment_start, comment_end - comment_start, self.comment_format)
            comment_start = comment_end

        directive_pattern = re.compile(r'(#\w+)')
        for match in directive_pattern.finditer(text):
            start, end = match.span()
            is_in_comment = False
            for comment_start in re.finditer(r'#\*', text):
                comment_end_match = re.search(r'\*#', text[comment_start.start():])
                if comment_end_match:
                    actual_comment_end = comment_start.start() + comment_end_match.end()
                    if comment_start.start() <= start < actual_comment_end:
                        is_in_comment = True
                        break
            if not is_in_comment:
                self.setFormat(start, end - start, self.directive_format)

        variable_pattern = re.compile(r'\$!?\{[^}]*\}|\$[a-zA-Z_][a-zA-Z0-9_-]*|\$[a-zA-Z0-9_-]+')
        for match in variable_pattern.finditer(text):
            start, end = match.span()
            self.setFormat(start, end - start, self.variable_format)

        tag_pattern = re.compile(r'<[^>]*>')
        for match in tag_pattern.finditer(text):
            start, end = match.span()
            tag_text = text[start:end]

            attr_pattern = re.compile(r'(\w+)=("[^"]*")')
            for attr_match in attr_pattern.finditer(tag_text):
                attr_start, attr_end = attr_match.span()
                self.setFormat(start + attr_start, attr_end - attr_start, self.attribute_format)

            self.setFormat(start, end - start, self.tag_format)


class VMTemplateViewer(QWidget):
    def __init__(self):
        super().__init__()

        self.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 4px;
                padding: 5px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.header_label = QLabel("Предпросмотр VM-шаблона")
        header_font = QFont("Lato", 12, QFont.Weight.Bold)
        self.header_label.setFont(header_font)
        self.header_label.setStyleSheet("color: #0B1F33; padding: 5px; border: none;")

        layout.addWidget(self.header_label)

        self.text_edit = QPlainTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet("""
            background-color: #E5EAF5; 
            color: #000000; 
            border: none; 
            font-family: 'Lato';
            /* Стили для скроллбара */
            QScrollBar:vertical {
                border: none;
                background-color: #E0E0E0;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #A0A0A0;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #808080;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        size_policy = self.text_edit.sizePolicy()
        size_policy.setVerticalPolicy(size_policy.Policy.Expanding)
        self.text_edit.setSizePolicy(size_policy)

        self.highlighter = VMSyntaxHighlighter(self.text_edit.document())

        layout.addWidget(self.text_edit)

        self.button_layout = QHBoxLayout()
        self.copy_button = QPushButton("Копировать в буфер")
        self.save_button = QPushButton("Сохранить как файл...")
        self.copy_button.setVisible(False)
        self.save_button.setVisible(False)
        self.copy_button.setStyleSheet("""
            QPushButton {
                background-color: #0D4CD3;
                color: #FFFFFF;
                border: none;
                padding: 12px 10px; /* Увеличенный отступ для высоты */
                border-radius: 8px;
                outline: none;
                font-family: 'Lato';
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0A3C9F;
            }
            QPushButton:pressed {
                background-color: #082F7F;
            }
        """)
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #0D4CD3;
                color: #FFFFFF;
                border: none;
                padding: 12px 10px; /* Увеличенный отступ для высоты */
                border-radius: 8px;
                outline: none;
                font-family: 'Lato';
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0A3C9F;
            }
            QPushButton:pressed {
                background-color: #082F7F;
            }
        """)

        self.button_layout.addWidget(self.copy_button)
        self.button_layout.addWidget(self.save_button)

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


class ProjectData:
    def __init__(self, json_schema_path="", json_examples_paths=None, xsd_schema_path=""):
        self.json_schema_path = json_schema_path
        self.json_examples_paths = json_examples_paths or []
        self.xsd_schema_path = xsd_schema_path

    @classmethod
    def from_dict(cls, data):
        return cls(
            json_schema_path=data.get("json_schema_path", ""),
            json_examples_paths=data.get("json_examples_paths", []),
            xsd_schema_path=data.get("xsd_schema_path", "")
        )

    def to_dict(self):
        return {
            "json_schema_path": self.json_schema_path,
            "json_examples_paths": self.json_examples_paths,
            "xsd_schema_path": self.xsd_schema_path
        }


class RecentFilesManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.file_path = "recent_files.json"
        self.max_recent = 3
        self.recent_files = self._load_recent_files()

    def _load_recent_files(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return data.get("recent_files", [])
            except:
                pass
        return []

    def _save_recent_files(self):
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump({"recent_files": self.recent_files}, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Ошибка при сохранении списка недавних файлов: {e}")

    def add_file(self, file_path):
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)
        self.recent_files.insert(0, file_path)
        self.recent_files = self.recent_files[:self.max_recent]
        self._save_recent_files()
        self.main_window._update_recent_menu()

    def get_recent_files(self):
        return self.recent_files


class ProjectManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.current_project_path = ""
        self.default_project_name = "Новый проект"

    def get_display_name(self):
        if self.current_project_path:
            base_name = os.path.basename(self.current_project_path)
            return os.path.splitext(base_name)[0]
        else:
            return self.default_project_name

    def update_window_title(self):
        display_name = self.get_display_name()
        self.main_window.setWindowTitle(f"{display_name} - Генератор VM-шаблонов")

    def save_project(self, force_save_as=False):
        if not force_save_as and self.current_project_path:
            save_path = self.current_project_path
        else:
            save_path, _ = QFileDialog.getSaveFileName(
                self.main_window,
                "Сохранить проект",
                "",
                "Файлы проектов (*.raw_esks);;All Files (*)"
            )
            if not save_path:
                return False
            if not save_path.endswith('.raw_esks'):
                save_path += '.raw_esks'

        project_data = ProjectData(
            json_schema_path=self.main_window.json_schema_reader.get_path(),
            json_examples_paths=self.main_window.json_apps_reader.get_paths(),
            xsd_schema_path=self.main_window.xsd_scheme_reader.get_path()
        )

        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(project_data.to_dict(), f, ensure_ascii=False, indent=4)
            self.current_project_path = save_path
            self.main_window.recent_files_manager.add_file(save_path)
            self.update_window_title()
            return True
        except Exception as e:
            print(f"Ошибка при сохранении проекта: {e}")
            QMessageBox.critical(self.main_window, "Ошибка", f"Не удалось сохранить проект:\n{e}")
            return False

    def load_project(self):
        load_path, _ = QFileDialog.getOpenFileName(
            self.main_window,
            "Открыть проект",
            "",
            "Файлы проектов (*.raw_esks);;All Files (*)"
        )
        if not load_path or not load_path.endswith('.raw_esks'):
            return

        try:
            with open(load_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            project_data = ProjectData.from_dict(data)
        except Exception as e:
            print(f"Ошибка при загрузке проекта: {e}")
            QMessageBox.critical(self.main_window, "Ошибка", f"Не удалось загрузить проект:\n{e}")
            return

        self.main_window.json_schema_reader.set_path(project_data.json_schema_path)
        self.main_window.xsd_scheme_reader.set_path(project_data.xsd_schema_path)
        self.main_window.json_apps_reader.set_paths(project_data.json_examples_paths)

        missing_files = self._check_files_existence(project_data)
        if missing_files:
            self._show_missing_files_warning(missing_files)
            self._remove_missing_files_from_ui(project_data)

        self.current_project_path = load_path
        self.main_window.recent_files_manager.add_file(load_path)
        self.update_window_title()
        self.main_window._on_file_state_changed()
        self.main_window.vm_template_viewer.set_content("")

    def new_project(self):
        self.current_project_path = ""
        self.main_window.json_schema_reader.set_path("")
        self.main_window.xsd_scheme_reader.set_path("")
        self.main_window.json_apps_reader.clear_all()
        self.update_window_title()
        self.main_window._on_file_state_changed()
        self.main_window.vm_template_viewer.set_content("")

    def _check_files_existence(self, project_data):
        missing_files = []
        if project_data.json_schema_path and not os.path.exists(project_data.json_schema_path):
            missing_files.append(project_data.json_schema_path)
        if project_data.xsd_schema_path and not os.path.exists(project_data.xsd_schema_path):
            missing_files.append(project_data.xsd_schema_path)
        for path in project_data.json_examples_paths:
            if not os.path.exists(path):
                missing_files.append(path)
        return missing_files

    def _show_missing_files_warning(self, missing_files):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowTitle("Ошибка")
        msg_box.setText("Некоторые файлы не найдены:")
        msg_box.setDetailedText("\n".join(missing_files))
        msg_box.exec()

    def _remove_missing_files_from_ui(self, project_data):
        schema_path = project_data.json_schema_path
        xsd_path = project_data.xsd_schema_path
        example_paths = project_data.json_examples_paths

        files_to_clear = {'schema': False, 'examples': [], 'xsd': False}

        if schema_path and not os.path.exists(schema_path):
            files_to_clear['schema'] = True
        if xsd_path and not os.path.exists(xsd_path):
            files_to_clear['xsd'] = True

        existing_example_paths = []
        for path in example_paths:
            if os.path.exists(path):
                existing_example_paths.append(path)
            else:
                files_to_clear['examples'].append(path)

        if files_to_clear['schema']:
            self.main_window.json_schema_reader.set_path("")
        if files_to_clear['xsd']:
            self.main_window.xsd_scheme_reader.set_path("")
        if files_to_clear['examples']:
            self.main_window.json_apps_reader.set_paths(existing_example_paths)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        font_dir = "assets/fonts"
        if os.path.exists(font_dir):
            for font_file in os.listdir(font_dir):
                if font_file.lower().endswith('.ttf'):
                    font_path = os.path.join(font_dir, font_file)
                    QFontDatabase.addApplicationFont(font_path)

        app_font = QFont("Lato", 10)
        self.setFont(app_font)

        self.project_manager = ProjectManager(self)
        self.recent_files_manager = RecentFilesManager(self)

        self.setWindowTitle(f"{self.project_manager.default_project_name} - Генератор VM-шаблонов")
        self.setGeometry(100, 100, 920, 700)
        qr = self.frameGeometry()
        cp = self.screen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        self.setStyleSheet("""
            QMainWindow {
                background-color: #FAFCFF;
            }
        """)

        menu_bar = QMenuBar(self)
        menu_bar.setStyleSheet("""
            QMenuBar {
                background-color: #053B75;
                color: #FFFFFF;
                font-family: 'Lato';
            }
            QMenuBar::item {
                color: #FFFFFF;
            }
            QMenuBar::item:selected {
                background-color: #0D4CD3;
            }
            QMenu {
                background-color: #053B75;
                color: #FFFFFF;
                font-family: 'Lato';
            }
            QMenu::item {
                color: #FFFFFF;
            }
            QMenu::item:selected {
                background-color: #0D4CD3;
            }
        """)
        self.setMenuBar(menu_bar)

        file_menu = menu_bar.addMenu("Файл")
        new_project_action = file_menu.addAction("Новый проект")
        new_project_action.triggered.connect(self.new_project)

        open_project_action = file_menu.addAction("Открыть проект")
        open_project_action.triggered.connect(self.open_project)

        save_project_action = file_menu.addAction("Сохранить проект")
        save_project_action.triggered.connect(self.save_project)

        save_project_as_action = file_menu.addAction("Сохранить проект как...")
        save_project_as_action.triggered.connect(lambda: self.save_project(force_save_as=True))

        self.recent_menu = file_menu.addMenu("Недавние")
        self._update_recent_menu()

        instruction_menu = menu_bar.addMenu("Инструкция")
        show_instruction_action = instruction_menu.addAction("Показать инструкцию")
        show_instruction_action.triggered.connect(self.show_instruction)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("""
            QSplitter {
                background-color: transparent;
                border: none;
            }
            QSplitter::handle {
                background-color: transparent;
                border: none;
            }
        """)
        splitter.setHandleWidth(40)
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)

        central_layout = QHBoxLayout(central_widget)
        central_layout.addWidget(splitter)

        self.left_widget = QWidget()
        self.left_widget.setStyleSheet("")
        size_policy = self.left_widget.sizePolicy()
        size_policy.setVerticalPolicy(size_policy.Policy.Minimum)
        self.left_widget.setSizePolicy(size_policy)

        self.left_layout = QVBoxLayout(self.left_widget)
        self.left_layout.setAlignment(Qt.AlignTop)
        self.left_layout.setContentsMargins(0, 0, 0, 0)

        self.json_schema_reader = JSONSchemeReader(self._on_file_state_changed)
        self.json_apps_reader = JSONAppsReader(self._on_file_state_changed)
        self.xsd_scheme_reader = XSDSchemeReader(self._on_file_state_changed)
        self.vm_generator_block = VMGeneratorBlock()

        for widget in [self.json_schema_reader, self.json_apps_reader, self.xsd_scheme_reader, self.vm_generator_block]:
            size_policy = widget.sizePolicy()
            size_policy.setVerticalPolicy(size_policy.Policy.Preferred)
            widget.setSizePolicy(size_policy)

        # --- Обёртки с тенями ---
        self.json_schema_wrapper = QWidget()
        self.json_schema_wrapper.setStyleSheet("""
            QWidget {
                background-color: #FFFFFF;
                border-radius: 4px;
                padding: 5px;
                box-shadow: 0px 4px 4px 0px #000000;
            }
        """)
        self.json_schema_layout = QVBoxLayout(self.json_schema_wrapper)
        self.json_schema_layout.addWidget(self.json_schema_reader)

        self.json_apps_wrapper = QWidget()
        self.json_apps_wrapper.setStyleSheet("""
            QWidget {
                background-color: #FFFFFF;
                border-radius: 4px;
                padding: 5px;
                box-shadow: 0px 4px 4px 0px #000000; /* Тень */
            }
        """)
        self.json_apps_layout = QVBoxLayout(self.json_apps_wrapper)
        self.json_apps_layout.addWidget(self.json_apps_reader)

        self.xsd_scheme_wrapper = QWidget()
        self.xsd_scheme_wrapper.setStyleSheet("""
            QWidget {
                background-color: #FFFFFF;
                border-radius: 4px;
                padding: 5px;
                box-shadow: 0px 4px 4px 0px #000000; /* Тень */
            }
        """)
        self.xsd_scheme_layout = QVBoxLayout(self.xsd_scheme_wrapper)
        self.xsd_scheme_layout.addWidget(self.xsd_scheme_reader)

        self.vm_generator_wrapper = QWidget()
        self.vm_generator_wrapper.setStyleSheet("""
            QWidget {
                background-color: #FFFFFF;
                border-radius: 4px;
                padding: 5px;
                box-shadow: 0px 4px 4px 0px #000000; /* Тень */
            }
        """)
        self.vm_generator_layout = QVBoxLayout(self.vm_generator_wrapper)
        self.vm_generator_layout.addWidget(self.vm_generator_block)

        self.left_layout.addWidget(self.json_schema_wrapper)
        self.left_layout.addWidget(self.json_apps_wrapper)
        self.left_layout.addWidget(self.xsd_scheme_wrapper)
        self.left_layout.addWidget(self.vm_generator_wrapper)
        self.left_layout.addStretch()

        splitter.addWidget(self.left_widget)

        self.vm_template_viewer_widget = QWidget()
        self.vm_template_viewer_widget.setStyleSheet("")
        size_policy = self.vm_template_viewer_widget.sizePolicy()
        size_policy.setVerticalPolicy(size_policy.Policy.Minimum)
        self.vm_template_viewer_widget.setSizePolicy(size_policy)

        vm_template_viewer_layout = QVBoxLayout(self.vm_template_viewer_widget)
        vm_template_viewer_layout.setAlignment(Qt.AlignTop)
        vm_template_viewer_layout.setContentsMargins(0, 0, 0, 0)
        vm_template_viewer_layout.setSpacing(5)

        self.vm_template_viewer = VMTemplateViewer()
        self.vm_template_wrapper = QWidget()
        self.vm_template_wrapper.setStyleSheet("""
            QWidget {
                background-color: #FFFFFF;
                border-radius: 4px;
                padding: 5px;
                box-shadow: 0px 4px 4px 0px #000000; /* Тень */
            }
        """)
        self.vm_template_layout = QVBoxLayout(self.vm_template_wrapper)
        self.vm_template_layout.addWidget(self.vm_template_viewer)

        size_policy = self.vm_template_wrapper.sizePolicy()
        size_policy.setVerticalPolicy(size_policy.Policy.Expanding)
        self.vm_template_wrapper.setSizePolicy(size_policy)

        vm_template_viewer_layout.addWidget(self.vm_template_wrapper)
        vm_template_viewer_layout.addStretch()

        splitter.addWidget(self.vm_template_viewer_widget)

        splitter.setSizes([440, 440])

        self.vm_generator_block.connect_generate_signal(self.generate_template)
        self._on_file_state_changed()

        self.vm_template_viewer.connect_copy_signal(self.copy_template)
        self.vm_template_viewer.connect_save_signal(self.save_template)

    def _update_recent_menu(self):
        self.recent_menu.clear()
        recent_files = self.recent_files_manager.get_recent_files()

        if not recent_files:
            no_recent_action = self.recent_menu.addAction("(нет недавних)")
            no_recent_action.setEnabled(False)
        else:
            for file_path in recent_files:
                action = self.recent_menu.addAction(file_path)
                action.triggered.connect(lambda checked=False, path=file_path: self._open_recent_project(path))

    def _open_recent_project(self, file_path):
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                project_data = ProjectData.from_dict(data)
            except Exception as e:
                print(f"Ошибка при загрузке проекта из недавних: {e}")
                QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить проект:\n{e}")
                return

            self.json_schema_reader.set_path(project_data.json_schema_path)
            self.xsd_scheme_reader.set_path(project_data.xsd_schema_path)
            self.json_apps_reader.set_paths(project_data.json_examples_paths)

            missing_files = self.project_manager._check_files_existence(project_data)
            if missing_files:
                self.project_manager._show_missing_files_warning(missing_files)
                self.project_manager._remove_missing_files_from_ui(project_data)

            self.project_manager.current_project_path = file_path
            self.recent_files_manager.add_file(file_path)
            self.project_manager.update_window_title()
            self._on_file_state_changed()
            self.vm_template_viewer.set_content("")
        else:
            QMessageBox.warning(self, "Файл не найден", f"Файл проекта больше не существует:\n{file_path}")
            self.recent_files_manager.recent_files = [f for f in self.recent_files_manager.recent_files if f != file_path]
            self.recent_files_manager._save_recent_files()
            self._update_recent_menu()


    def new_project(self):
        self.project_manager.new_project()

    def open_project(self):
        self.project_manager.load_project()

    def save_project(self, force_save_as=False):
        self.project_manager.save_project(force_save_as=force_save_as)

    def _on_file_state_changed(self):
        schema_loaded = bool(self.json_schema_reader.get_path())
        # examples_loaded больше не участвует в проверке
        xsd_loaded = bool(self.xsd_scheme_reader.get_path())

        all_loaded = schema_loaded and xsd_loaded # examples_loaded убрано
        self.vm_generator_block.set_enabled(all_loaded)

    def generate_template(self):
        schema_path = self.json_schema_reader.get_path()
        example_paths = self.json_apps_reader.get_paths()
        xsd_path = self.xsd_scheme_reader.get_path()

        project_data = ProjectData(
            json_schema_path=schema_path,
            json_examples_paths=example_paths,
            xsd_schema_path=xsd_path
        )

        missing_files = self.project_manager._check_files_existence(project_data)

        if missing_files:
            self.project_manager._show_missing_files_warning(missing_files)
            self.project_manager._remove_missing_files_from_ui(project_data)
            self._on_file_state_changed()
            return

        try:
            template_content = core.mid_vm.generate_template(schema_path, xsd_path)
            self.vm_template_viewer.set_content(template_content)
            # Автоматически копируем в буфер
            clipboard = QApplication.clipboard()
            clipboard.setText(template_content)
            # Автоматически открываем диалог сохранения
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить VM-шаблон",
                "xxxxxxxxx_Applicant.vm",
                "VM Files (*.vm);;All Files (*)"
            )

            if file_path:
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(template_content)
                except Exception as e:
                    print(f"Ошибка при сохранении шаблона: {e}")
                    QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить шаблон:\n{e}")
        except Exception as e:
            self.vm_template_viewer.set_content(f"Ошибка при генерации шаблона: {e}")

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

    def show_instruction(self):
        instruction_text = """
        Инструкция по использованию:
        1. Загрузите JSON-схему формы.
        2. Загрузите XSD-схему ведомства.
        3. Нажмите "Сгенерировать шаблон".
        """
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Инструкция")
        msg_box.setText(instruction_text)
        msg_box.exec()
