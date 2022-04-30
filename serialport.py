import serial.tools.list_ports
import keyboard
import time

ports = serial.tools.list_ports.comports()
serialInst = serial.Serial()

portList = []

serialInst.baudrate = 115200
serialInst.port = "COM4"
serialInst.open()

control_keys = {'w': 'W', 'a': 'A', 's': 'S', 'd': 'D', 'g': 'G'}
EXIT_HOTKEY = 'ctrl+c'

while True:
    if serialInst.in_waiting:
        packet = serialInst.readline().decode('ascii')
        if len(packet) > 0:
            print(packet)

    time.sleep(0.1)

    if keyboard.read_key() in control_keys:
        serialInst.write(str.encode(control_keys[keyboard.read_key()]))

    if keyboard.read_hotkey == EXIT_HOTKEY:
        quit()