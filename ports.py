from serial_port import *

name_list = SerialPort.ls()
if len(name_list) == 0:
	print("No available ports!")
	sys.exit(1)

for i in range(len(name_list)):
	name = name_list[i]
	if i != len(name_list)-1:
		os.system("start cmd /k python \"" + os.path.dirname(os.path.abspath(__file__)) + "/port.py\" " + name)
	else:
		os.system("cls && python \"" + os.path.dirname(os.path.abspath(__file__)) + "/port.py\" " + name)