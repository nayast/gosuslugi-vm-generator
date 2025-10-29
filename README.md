# gosuslugi-vm-generator
Команда: await_docx

# Генератор VM-шаблонов

Десктопное приложение на Python + PySide6 для генерации Velocity-шаблонов (`.vm`) на основе JSON-схемы формы и XSD-схемы ведомства.

---

## 📦 Требования

- Python 3.8+
- Windows (рекомендуется; также работает на Linux)

---

## 🛠 Установка и запуск из исходников

1. Клонируйте или распакуйте проект.
2. Установите зависимости:
```bash
pip install -r requirements.txt
```
3. Запустите приложение:

```bash
python main_window.py
```

> Убедитесь, что папка `assets/` находится в той же директории, что и `main_window.py`.

---

## 🔧 Сборка в исполняемый файл (.exe)

Для распространения приложения без Python используйте **PyInstaller**.

1. Установите PyInstaller (если ещё не установлен):

```bash
pip install pyinstaller
```

2. Выполните команду из корня проекта:
```bash
pyinstaller --onefile --windowed ^
--add-data "assets;assets" ^
--add-data "core;core" ^
--icon="icon.ico" ^
--name="Генератор_VM" ^
main_window.py
```

> ⚠️ Убедитесь, что файл `icon.ico` существует в корне проекта.  
> Если иконка не нужна — удалите строку `--icon="icon.ico"`.

3. Готовый `.exe` будет находиться в папке `dist/Генератор_VM.exe`.

> 💡 При первом запуске `.exe` может быть медленным — это нормально (PyInstaller распаковывает архив во временную папку).

---
