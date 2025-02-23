import os
import requests
# import tempfile
import pyperclip
# from AppKit import (
#     NSPasteboard,
#     NSURL,
#     NSFilenamesPboardType,
#     NSPasteboardTypePNG,
#     NSPasteboardTypeTIFF,
#     NSPasteboardTypeFileURL
# )

# from PIL import Image
from toast import balloon_tip

UPLOAD_URL = "http://192.168.1.68:6144/drop"


def send_file(file_path: str) -> bool:
    headers = {}
    response = None
    success = False

    try:
        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f)}
            response = requests.post(UPLOAD_URL, files=files, headers=headers)
            response.raise_for_status()
            balloon_tip("Успех", "Файл отправлен успешно")
            success = True
    except requests.exceptions.Timeout:
        balloon_tip("Ошибка", "Сервер недоступен: таймаут")
    except Exception as e:
        balloon_tip("Ошибка", f"Ошибка отправки: {str(e)}")
    finally:
        if response and not success:
            balloon_tip(
                "Ошибка", f"HTTP ошибка: {response.status_code}"
            )
        if os.path.exists(file_path) and "/var/folders/" in file_path:
            os.remove(file_path)
    return success


def send_text(text: str) -> bool:
    headers = {"Content-Type": "text/plain"}
    try:
        response = requests.post(UPLOAD_URL, data=text, headers=headers, timeout=3)
        response.raise_for_status()
        balloon_tip("Успех", "Текст отправлен")
        return True
    except Exception as e:
        print("err", e)
        balloon_tip("Ошибка", f"Ошибка: {str(e)}")
        return False


# def handle_files() -> str | None:
#     try:
#         pb = NSPasteboard.generalPasteboard()
#         data = None
        
#         # Получаем массив типов в виде NSArray
#         types = pb.types()
        
#         # Проверяем наличие типов через containsObject_
#         if types.containsObject_(NSPasteboardTypePNG):
#             data = pb.dataForType_(NSPasteboardTypePNG)
#         elif types.containsObject_(NSPasteboardTypeTIFF):
#             data = pb.dataForType_(NSPasteboardTypeTIFF)
        
#         if data:
#             with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f:
#                 f.write(data)
#                 img = Image.open(f.name)
#                 img.save(f.name, "PNG")
#                 return f.name
#     except Exception as e:
#         balloon_tip("Ошибка", f"Ошибка скриншота: {str(e)}")
#     finally:
#         return None


# def handle_files() -> list | None:
#     # try:
#         pb = NSPasteboard.generalPasteboard()
#         types = pb.types()
        
#         # Проверяем наличие файлов через NSURL
#         if types.containsObject_(NSFilenamesPboardType):
#             files = pb.propertyListForType_(NSFilenamesPboardType)
#             return files if isinstance(files, list) else None
        
#         if types.containsObject_([NSURL]):
#             print("да")
        
#         if types.containsObject_(NSPasteboardTypePNG):
#             print("png")
#             data = pb.dataForType_(NSPasteboardTypePNG)
            
        # Альтернативный способ через чтение NSURL
        # urls = pb.readObjectsForClasses_([NSURL], options=None)
        # if urls:
        #     return [url.path() for url in urls]
            
        # return None

    # except Exception as e:
    #     balloon_tip("Ошибка", f"Ошибка обработки файлов: {str(e)}")
    #     return None


# def handle_files() -> list | None:
#     # try:
#         pb = NSPasteboard.generalPasteboard()
#         # files = pb.readObjectsForClasses_([NSURL], options=None)
#         files = pb.readObjects([NSURL], options=None)
        
#         return [url.path() for url in files] if files else None
#     # except Exception as e:
#     #     balloon_tip("Ошибка", f"Ошибка файлов: {str(e)}")
#     # return None


def get_clipboard_content():
    # if files := handle_files():
    #     print("files: ", files)
    #     return {"type": "files", "content": files}

    if text := pyperclip.paste().strip():
        print("text: ",text)
        return {"type": "text", "content": text}

    return {"type": "empty"}


if __name__ == "__main__":
    content = get_clipboard_content()

    if content["type"] == "files":
        for path in content["content"]:
            send_file(path)
    elif content["type"] == "text":
        # print(content["content"])
        send_text(content["content"])
    else:
        balloon_tip("Инфо", "Буфер пуст")
