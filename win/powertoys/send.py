import os
import requests
import tempfile
import pyperclip
import win32clipboard

from PIL import Image
from toast import balloon_tip


UPLOAD_URL = "http://192.168.1.73:1161/drop"
SUCCESS = "./_assets/check.ico"
ERROR = "./_assets/error.ico"
EMPTY = "./_assets/empty.ico"


def send_file(file_path: str) -> bool:
    """Отправка файла на сервер"""
    headers = {}
    response = None
    success = False

    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f)}
        filename = os.path.basename(file_path).split("\\")[-1]
        
        try:
            response = requests.post(UPLOAD_URL, files=files, headers=headers)
            response.raise_for_status()
        except requests.exceptions.Timeout:
            balloon_tip(
                "Ошибка", "Сервер недоступен: превышено время ожидания", 
                icon_path=ERROR
            )
            success = False
        except requests.exceptions.RequestException as e:
            error_message = f"Ошибка подключения: {str(e)}"
            balloon_tip("Ошибка", error_message, icon_path=ERROR)
            success = False
        else:
            balloon_tip("", f'Файл "{filename}" отправлен', icon_path=SUCCESS)
            success = True
        finally:
            if response is not None and not success:
                balloon_tip(
                    "Ошибка", f"HTTP ошибка: {response.status_code}", 
                    icon_path=ERROR
                )

        return success


def send_text(text: str) -> bool:
    """Отправляет текст на сервер и возвращает результат операции."""
    headers = {"Content-Type": "text/plain"}
    response = None
    success = False

    try:
        response = requests.post(UPLOAD_URL, data=text, headers=headers, timeout=3)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        balloon_tip(
            "Ошибка", "Сервер недоступен: превышено время ожидания", 
            icon_path=ERROR
        )
        success = False
    except requests.exceptions.RequestException as e:
        error_message = f"Ошибка подключения: {str(e)}"
        balloon_tip("Ошибка", error_message, icon_path=ERROR)
        success = False
    else:
        balloon_tip("", "Отправлено успешно", icon_path=SUCCESS)
        success = True
    finally:
        if response is not None and not success:
            balloon_tip(
                "Ошибка", f"HTTP ошибка: {response.status_code}", 
                icon_path=ERROR
            )

    return success


def handle_screenshot() -> str | None:
    """Обработка скриншота из буфера обмена"""
    try:
        win32clipboard.OpenClipboard()
        if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_DIB):
            data = win32clipboard.GetClipboardData(win32clipboard.CF_DIB)  # получаем данных из bitmap
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
                img = Image.frombytes("RGBA", (1, 1), data)  # конвертиртация DIB в изображение
                img.save(temp_file.name, "PNG")
                return temp_file.name

    except Exception as e:
        print(f"Ошибка обработки скриншота: {str(e)}")
        balloon_tip(
            "Ошибка", f"Ошибка обработки скриншота: {str(e)}", 
            icon_path=ERROR
        )
    finally:
        win32clipboard.CloseClipboard()
    return None


def handle_files() -> str | None:
    try:
        win32clipboard.OpenClipboard()
        if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_HDROP):
            files = win32clipboard.GetClipboardData(win32clipboard.CF_HDROP)
            return files

    except Exception as e:
        print(f"Ошибка обработки файла: {str(e)}")
        balloon_tip(
            "Ошибка", f"Ошибка обработки файла: {str(e)}", 
            icon_path=ERROR
        )
    finally:
        win32clipboard.CloseClipboard()
    return None


def get_clipboard_content():
    """Проверка содержимого буфера обмена"""
    screenshot_path = handle_screenshot()
    if screenshot_path:
        return {"type": "file", "content": [screenshot_path]}

    files = handle_files()
    if files: 
        return {"type": "files", "content": files}

    text = pyperclip.paste().strip()
    if text:
        return {"type": "text", "content": text}

    return {"type": "empty"}


if __name__ == "__main__":
    content = get_clipboard_content()
    # print(content)

    if content["type"] == "files":
        for file_path in content["content"]:
            send_file(file_path)
    elif content["type"] == "text":
        send_text(content["content"])
    else:
        balloon_tip("", "Буфер обмена пуст", icon_path=EMPTY)
