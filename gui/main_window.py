from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QLineEdit, QPushButton, QFileDialog, QPlainTextEdit,
                               QGroupBox, QListWidget, QAbstractItemView, QSplitter, QMessageBox, QMenuBar)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication
import os
import json
import sys

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
        self._items_widgets_map = {}

    def get_paths(self):
        return list(self._file_paths)

    def add_paths(self, paths):
        for path in paths:
            if path not in self._file_paths:
                item = JSONAppItem(path, self._on_item_removed)
                self.items_layout.addWidget(item)
                self._file_paths.add(path)
                self._items_widgets_map[path] = item

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
        item_widget = self._items_widgets_map.get(path)
        if item_widget:
            item_widget.setParent(None)
            del self._items_widgets_map[path]
        self._file_paths.discard(path)

        self.items_widget.setVisible(bool(self._file_paths))
        self.on_state_change_callback()

    def clear_all(self):
        for item_widget in self._items_widgets_map.values():
            item_widget.setParent(None)
        self._items_widgets_map.clear()
        self._file_paths.clear()
        self.items_widget.setVisible(False)
        self.on_state_change_callback()

    def set_paths(self, paths):
        self.clear_all()
        self.add_paths(paths)


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
        self.main_window._update_recent_menu() # Обновляем меню после изменения списка

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
        self.project_manager = ProjectManager(self)
        self.recent_files_manager = RecentFilesManager(self)

        self.setWindowTitle(f"{self.project_manager.default_project_name} - Генератор VM-шаблонов")
        self.setGeometry(100, 100, 920, 700)
        qr = self.frameGeometry()
        cp = self.screen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        self.setStyleSheet("background-color: #FFFFFF;")

        menu_bar = QMenuBar(self)
        menu_bar.setStyleSheet("""
            QMenuBar {
                background-color: #053B75;
                color: #FFFFFF;
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
        examples_loaded = bool(self.json_apps_reader.get_paths())
        xsd_loaded = bool(self.xsd_scheme_reader.get_path())

        all_loaded = schema_loaded and examples_loaded and xsd_loaded
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

    def show_instruction(self):
        instruction_text = """
        Инструкция по использованию:
        1. Загрузите JSON-схему формы.
        2. Загрузите примеры JSON-заявлений.
        3. Загрузите XSD-схему ведомства.
        4. Нажмите "Сгенерировать шаблон".
        """
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Инструкция")
        msg_box.setText(instruction_text)
        msg_box.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())