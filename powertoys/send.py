import os
import requests
import tempfile
import pyperclip
import win32clipboard

from toast import balloon_tip
from pathlib import Path
from io import BytesIO
from PIL import Image


UPLOAD_URL = "http://192.168.1.64:1161/drop"
SUCCESS = "./_assets/check.ico"
ERROR = "./_assets/error.ico"
EMPTY = "./_assets/empty.ico"


def send_file(file_path):
    """Отправка файла на сервер"""
    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f)}
        headers = {}
        response = requests.post(UPLOAD_URL, files=files, headers=headers)
        if response.status_code == 200:
            balloon_tip("", "Отправлено", icon_path=SUCCESS)
        else:
            balloon_tip("Ошибка", " ", icon_path=ERROR)
        return response.status_code == 200


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


def handle_screenshot():
    """Обработка скриншота из буфера обмена"""
    try:
        win32clipboard.OpenClipboard()
        if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_DIB):
            # Получаем данные bitmap
            data = win32clipboard.GetClipboardData(win32clipboard.CF_DIB)

            # Создаем временный файл
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
                # Конвертируем DIB в изображение
                img = Image.frombytes(
                    "RGBA", (1, 1), data
                )  # Размер будет автоматически определен
                img.save(temp_file.name, "PNG")
                return temp_file.name

    except Exception as e:
        print(f"Ошибка обработки скриншота: {str(e)}")
    finally:
        win32clipboard.CloseClipboard()
    return None


def get_clipboard_content():
    """Проверка содержимого буфера обмена"""
    try:
        screenshot_path = handle_screenshot()
        if screenshot_path:
            return {"type": "file", "content": [screenshot_path]}

        # Проверка на файлы
        win32clipboard.OpenClipboard()
        if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_HDROP):
            files = win32clipboard.GetClipboardData(win32clipboard.CF_HDROP)
            return {"type": "files", "content": files}
        # elif win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_DIB):
        #     return {
        #         "type": "image",
        #         "content": "картинка хд",
        #     }  # TODO исправить на реальный "путь" до скрина
    finally:
        win32clipboard.CloseClipboard()

    text = pyperclip.paste().strip()
    if text:
        return {"type": "text", "content": text}

    return {"type": "empty"}


if __name__ == "__main__":
    content = get_clipboard_content()
    print(content)

    if content["type"] == "files":
        for file_path in content["content"]:
            send_file(file_path)
            # if send_file(file_path):
            #     print(f"Файл {file_path} отправлен!")
            # else:
            #     print(f"Ошибка отправки файла {file_path}")
    elif content["type"] == "text":
        send_text(content["content"])
    else:
        balloon_tip("", "Буфер обмена пуст", icon_path=EMPTY)
