import os
from AppKit import NSUserNotification, NSUserNotificationCenter, NSImage


def balloon_tip(title, message, icon_path=None):
    notification = NSUserNotification.alloc().init()
    notification.setTitle_(str(title))
    notification.setInformativeText_(str(message))

    if icon_path and os.path.exists(icon_path):
        image = NSImage.alloc().initWithContentsOfFile_(icon_path)
        notification.setContentImage_(image)

    NSUserNotificationCenter.defaultUserNotificationCenter().deliverNotification_(
        notification
    )


if __name__ == "__main__":
    balloon_tip("title", "message")
