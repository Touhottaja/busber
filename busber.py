import colorlog
import logging
import threading
import usb.core
import usb.util
from enum import Enum

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

formatter = colorlog.ColoredFormatter(
    "%(log_color)s%(asctime)s - %(levelname)s - %(message)s",
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'white',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white',
    })

console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Global variables
read_devices = []

# USB HID scancodes
SCANCODES = {
    # Letters
    4: 'a', 5: 'b', 6: 'c', 7: 'd', 8: 'e', 9: 'f', 10: 'g', 11: 'h', 12: 'i',
    13: 'j', 14: 'k', 15: 'l', 16: 'm', 17: 'n', 18: 'o', 19: 'p', 20: 'q',
    21: 'r', 22: 's', 23: 't', 24: 'u', 25: 'v', 26: 'w', 27: 'x', 28: 'y',
    29: 'z',
    # Numbers
    30: '1', 31: '2', 32: '3', 33: '4', 34: '5', 35: '6', 36: '7',37: '8',
    38: '9', 39: '0',
    # Special keys
    40: '[ENTER]', 41: '[ESC]', 42: '[BACKSPACE]', 43: '[TAB]', 44: '[SPACE]',
    57: '[CAPSLOCK]', 225: '[LEFTSHIFT]', 229: '[RIGHTSHIFT]', 226: '[LEFTALT]',
    230: '[RIGHTALT]', 224: '[LEFTCTRL]', 228: '[RIGHTCTRL]', 227: '[LEFTMETA]',
    231: '[RIGHTMETA]',
    # Function keys
    58: '[F1]', 59: '[F2]', 60: '[F3]', 61: '[F4]', 62: '[F5]', 63: '[F6]',
    64: '[F7]', 65: '[F8]', 66: '[F9]', 67: '[F10]', 68: '[F11]', 69: '[F12]',
}

DEVICE_READ_TIMEOUT_S = 5 * 1000


class USBClass(Enum):
    UNKNOWN = 0x00
    AUDIO = 0x01
    COMMUNICATIONS = 0x02
    HID = 0x03
    PHYSICAL = 0x05
    IMAGE = 0x06
    PRINTER = 0x07
    MASS_STORAGE = 0x08
    HUB = 0x09
    CDC_DATA = 0x0a
    SMART_CARD = 0x0b
    CONTENT_SECURITY = 0x0d
    VIDEO = 0x0e
    PERSONAL_HEALTHCARE = 0x0f
    AUDIO_VIDEO = 0x10
    BILLBOARD = 0x11
    USB_TYPE_C_BRIDGE = 0x12
    DIAGNOSTIC_DEVICE = 0xdc
    WIRELESS_CONTROLLER = 0xe0
    MISCELLANEOUS = 0xef
    APPLICATION_SPECIFIC = 0xfe
    VENDOR_SPECIFIC = 0xff


def main() -> None:
    # Read initial devices
    logger.info("Initial devices:")
    for device in usb.core.find(find_all=True):
        read_devices.append(device)
        print_device_information(device)
    logger.info("")

    # Create a separate thread for monitoring devices
    monitor_thread = threading.Thread(target=monitor_devices)
    monitor_thread.start()


def monitor_devices():
    while True:
        new_devices = usb.core.find(find_all=True)
        for device in new_devices:
            if device in read_devices:
                continue
            logger.warning("New device found:")
            read_devices.append(device)
            print_device_information(device)
            read_input_from_device(device)


def print_device_information(device: usb.core.Device) -> None:
    device_class = USBClass(device.bDeviceClass)
    device_info = f"Class: {device_class.name}, "\
                  f"Vendor ID: {device.idVendor}, " \
                  f"Product ID: {device.idProduct}"
    logger.info(device_info)


def read_input_from_device(device: usb.core.Device) -> None:
    endpoint = device[0][(0,0)][0]
    interface_number = \
        device.configurations()[0].interfaces()[0].bInterfaceNumber

    # If the device is using a kernel driver, detach it
    if device.is_kernel_driver_active(interface_number):
        try:
            device.detach_kernel_driver(interface_number)
            logger.warning("Kernel driver detached from interface" \
                           f"{interface_number}")
        except usb.core.USBError as e:
            logger.error(f"Error detaching kernel driver: {e}")
            return

    # Claim the interface
    ascii_data = ""
    while True:
        try:
            data = device.read(endpoint.bEndpointAddress,
                               endpoint.wMaxPacketSize,
                               timeout=DEVICE_READ_TIMEOUT_S)
            ascii_data += "".join(
                [SCANCODES.get(code, "") for code in data[2:] if code != 0])
            logger.info(ascii_data)
        except usb.core.USBError as e:
            if e.errno == 19:
                logger.error("Device disconnected")
                break
            logger.error(f"Error reading data from device: {e}")
            continue


if __name__ == "__main__":
    main()
