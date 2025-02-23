import os
import sys
import time
import win32con

from win32gui import (
    WNDCLASS,
    GetModuleHandle,
    RegisterClass,
    CreateWindow,
    UpdateWindow,
    LoadImage,
    LoadIcon,
    Shell_NotifyIcon,
    DestroyWindow,
    DefWindowProc,
    PostQuitMessage,
)

from win32gui import (
    NIF_ICON,
    NIF_MESSAGE,
    NIF_TIP,
    NIM_ADD,
    NIM_DELETE,
    NIM_MODIFY,
    NIF_INFO,
)


class WindowsBalloonTip:
    def __init__(self, title: str, msg: str, ttd: float, icon_path: str = None):
        self.title = title
        self.msg = msg
        self.ttd = ttd
        self.icon_path = icon_path
        self.notification_added = False

        message_map = {
            win32con.WM_DESTROY: self.OnDestroy,
            win32con.WM_USER + 20: self.OnNotify,
        }

        # Register the Window class.
        self.class_name = f"PythonTaskbar_{id(self)}"
        wc = WNDCLASS()
        hinst = wc.hInstance = GetModuleHandle(None)
        wc.lpszClassName = self.class_name
        wc.lpfnWndProc = self.create_wnd_proc(message_map)  # Create message handler foo
        classAtom = RegisterClass(wc)

        # Create the Window.
        style = win32con.WS_OVERLAPPED | win32con.WS_SYSMENU
        self.hwnd = CreateWindow(
            classAtom,
            "Taskbar",
            style,
            0,
            0,
            win32con.CW_USEDEFAULT,
            win32con.CW_USEDEFAULT,
            0,
            0,
            hinst,
            None,
        )
        UpdateWindow(self.hwnd)

        icon = self.icon_path if self.icon_path else "balloontip.ico"
        iconPathName = os.path.abspath(os.path.join(sys.path[0], icon))
        icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE

        try:
            hicon = LoadImage(
                hinst, iconPathName, win32con.IMAGE_ICON, 0, 0, icon_flags
            )
        except Exception as e:
            print(e)
            hicon = LoadIcon(0, win32con.IDI_APPLICATION)

        self.show_balloon(hicon)

    def create_wnd_proc(self, message_map):
        """Создание функции-обработчика для оконных сообщений."""

        def wnd_proc(hwnd, msg, wparam, lparam):
            if msg in message_map:
                return message_map[msg](hwnd, msg, wparam, lparam)
            return DefWindowProc(hwnd, msg, wparam, lparam)

        return wnd_proc

    def show_balloon(self, hicon):
        flags = NIF_ICON | NIF_MESSAGE | NIF_TIP
        nid = (self.hwnd, 0, flags, win32con.WM_USER + 20, hicon, "tooltip")
        Shell_NotifyIcon(NIM_ADD, nid)
        self.notification_added = True

        # Display the balloon tooltip
        Shell_NotifyIcon(
            NIM_MODIFY,
            (
                self.hwnd,
                0,
                NIF_INFO,
                win32con.WM_USER + 20,
                hicon,
                "Balloon tooltip",
                self.msg,
                200,
                self.title,
            ),
        )
        time.sleep(self.ttd)
        self.cleanup(nid)

    def cleanup(self, nid):
        if self.notification_added:
            Shell_NotifyIcon(NIM_DELETE, nid)
            self.notification_added = False
        DestroyWindow(self.hwnd)

    def OnNotify(self, hwnd, msg, wparam, lparam):
        # Here you can handle additional notifications if needed
        return 0

    def OnDestroy(self, hwnd, msg, wparam, lparam):
        PostQuitMessage(0)  # Terminate the app.
        return 0  # Return 0 for successful termination


def balloon_tip(title: str, msg: str, ttd: float = 2.5, icon_path: str = None):
    w = WindowsBalloonTip(title, msg, ttd, icon_path)
    w


if __name__ == "__main__":
    balloon_tip("title", "msg", 2.5)
