import sys
import os
import json
import codecs
from serial_port import *

def parse_argv():
	args = []
	kwargs = {}
	i = 1
	while i < len(sys.argv):
		if sys.argv[i][0] == '-':
			if i+1 < len(sys.argv):
				if sys.argv[i+1][0] != "-":
					kwargs[sys.argv[i]] = sys.argv[i+1]
					i += 2
				else:
					kwargs[sys.argv[i]] = ""
					i += 1
			else:
				kwargs[sys.argv[i]] = ""
				i += 1
		else:
			args.append(sys.argv[i])
			i += 1
	return args, kwargs

def load_option():
	config_file = os.path.dirname(os.path.abspath(__file__)) + "/default.json"
	
	result = {"baudrate": 115200, "bytesize": 8, "stopbits": 1.0, "parity": "none", "end": "\r\n", "log": "default"}
	if os.path.isfile(config_file):
		result = json.loads(open(os.path.dirname(os.path.abspath(__file__)) + "/default.json").read())

	return result

def save_option(option):
	file = open("default.json", "w")
	file.write(json.dumps(option))
	file.close()

def print_setting(option):
	print("Baud Rate : " + str(option["baudrate"]))
	print("Byte Size : " + str(option["bytesize"]))
	print("Stop Bits : " + str(option["stopbits"]))
	print("Parity    : " + str(option["parity"]))
	print("end       : " + option["end"])
	print("log       : " + option["log"])

def help():
	print("usage: port [args] [options]")
	print("args can be:")
	print("<port_name> : <port_name> should be an available serial port name. Such as \"COM3\"")
	print("ls          : To list all available serial port names.")
	print("setting     : Print current used settings.")
	print("config      : Not open port, only config.")
	print("If <port_name> is not specified, will use first found serial port name. So just use \"port\" can also work fine.")
	print("")
	print("options can be:")
	print("--baudrate <rate> : Specify baud rate for serial communication.")
	print("                    <rate> can be any positive integer. Default is 115200.")
	print("--bytesize <size> : Specify byte size for serial communication.")
	print("                    <size> can choose in [5, 6, 7, 8]. Default is 8.")
	print("--stopbits <bits> : Specify byte size for serial communication.")
	print("                    <bits> can choose in [1, 1.5, 2]. Default is 1.")
	print("--parity <type>   : Specify parity type for serial communication.")
	print("                    <type> can choose in [none, even, odd, mark, space]. Default is none.")
	print("--end <str>       : Specify end string for each input command.")
	print("                    <str> can be any value. Default is \\r\\n.")
	print("--log <filename>  : Specify log file storage path.")
	print("                    If <filename> is none, means don't save serial output to file.")
	print("                    If <filename> is default, means save serial output to current working directory.")
	print("                    If <filename> is a file path, means save serial output to this path.")
	print("                    <filename>'s default value is default.")
	print("--global          : If --global is used, all options you configured will be memorised and will be used next time.")
	print("--setting         : Print current used settings.")
	print("--help            : Print this help message and exit.")
	print("")
	print("After you see \"COMn>\", input message then press enter, then message append with --end argument will be send to serial port.")
	print("Specially, if your input string begin with !, system command will be called. For example, !cls will clear the screen.")
	print("If your input string begin with :, internal command will be called. Following internal command is supported:")
	print(":write [<filename>]           : If <filename> is existing file path, this file's content will be sent to serial port.")
	print("                                If you don't use <filename> argument, will go into vim editing mode.")
	print("                                After you save, the content that you just write will be sent to serial port.")
	print(":clear_log                    : Clear the log file content.")
	print(":exit, :q, :wq, :quit, :bye   : To exit program.")

args, kwargs = parse_argv()
if len(args) == 0 and len(kwargs) == 1:
	if "--help" in kwargs:
		help()
		sys.exit(0)
	if "--setting" in kwargs:
		print_setting(load_option())
		sys.exit(0)

names = SerialPort.ls()

name = ""
if len(args) == 0:
	if len(names) == 0:
		print("No available ports!")
		sys.exit(1)
	name = names[0]
else:
	if args[0] == "ls":
		for name in names:
			print(name)
		sys.exit(0)
	if args[0] == "setting":
		print_setting(load_option())
		sys.exit(0)

	name = args[0]
	if name not in names and name != "config":
		print(name + " is not an available port!")
		sys.exit(1)

option = load_option()

if "--baudrate" in kwargs:
	option["baudrate"] = int(kwargs["--baudrate"])

if "--bytesize" in kwargs:
	option["bytesize"] = int(kwargs["--bytesize"])

if "--stopbits" in kwargs:
	option["stopbits"] = float(kwargs["--stopbits"])

if "--parity" in kwargs:
	option["parity"] = kwargs["--parity"]

if "--end" in kwargs:
	option["end"] = codecs.decode(kwargs["--end"], 'unicode_escape')

if "--log" in kwargs:
	option["log"] = kwargs["--log"]

if "--global" in kwargs or "config" in args or ("--global" in kwargs and "config" in kwargs["--global"]):
	save_option(option)

if "config" in args or ("--global" in kwargs and "config" in kwargs["--global"]):
	sys.exit(0)

os.system("title " + name)
port = SerialPort(name, baudrate=option["baudrate"], bytesize=option["bytesize"], stopbits=option["stopbits"], parity=option["parity"], end=option["end"])
port.open_print()
if "log" in option:
	if option["log"] == "default":
		port.log_into(name + "_log.txt")
	elif option["log"] == "none":
		pass
	else:
		port.log_into(option["log"])

port.start_read()
port.hold_on()