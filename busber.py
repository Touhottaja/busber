import threading
import usb.core
import usb.util
from enum import Enum

read_devices = []


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
    print("Initial devices:")
    for device in usb.core.find(find_all=True):
        read_devices.append(device)
        print_device_information(device)
    print("-----------------------------------")

    # Create a separate thread for monitoring devices
    monitor_thread = threading.Thread(target=monitor_devices)
    monitor_thread.start()


def monitor_devices():
    while True:
        new_devices = usb.core.find(find_all=True)
        for device in new_devices:
            if device in read_devices:
                continue
            print("New device found:")
            read_devices.append(device)
            print_device_information(device)
            read_input_from_device(device)


def print_device_information(device: usb.core.Device) -> None:
    device_class = USBClass(device.bDeviceClass)
    print(f"Class: {device_class.name}, "\
          f"Vendor ID: {device.idVendor}, " \
          f"Product ID: {device.idProduct}")


def read_input_from_device(device: usb.core.Device) -> None:
    endpoint = device[0][(0,0)][0]
    while True:
        try:
            data = device.read(endpoint.bEndpointAddress,
                               endpoint.wMaxPacketSize)
            print(f"Received data: {data}")
        except usb.core.USBError as e:
            print(f"Error reading data from device: {e}")
            break


if __name__ == "__main__":
    main()
