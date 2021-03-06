import serial
import serial.tools.list_ports
import threading
import os
import sys
import time
import string
from inputer import *

Ctrl_A = b'\x01'
Ctrl_B = b'\x02'
Ctrl_C = b'\x03'
Ctrl_D = b'\x04'
Ctrl_E = b'\x05'
Ctrl_F = b'\x06'
Ctrl_G = b'\x07'
Ctrl_H = b'\x08'
Ctrl_I = b'\x09'
Ctrl_G = b'\x0A'
Ctrl_K = b'\x0B'
Ctrl_L = b'\x0C'
Ctrl_M = b'\x0D'
Ctrl_N = b'\x0E'
Ctrl_O = b'\x0F'
Ctrl_P = b'\x10'
Ctrl_Q = b'\x11'
Ctrl_R = b'\x12'
Ctrl_S = b'\x13'
Ctrl_T = b'\x14'
Ctrl_U = b'\x15'
Ctrl_V = b'\x16'
Ctrl_W = b'\x17'
Ctrl_X = b'\x18'
Ctrl_Y = b'\x19'
Ctrl_Z = b'\x1A'

class SerialPort:
	def __init__(self, COMn, baudrate = 115200, bytesize = 8, stopbits = 1, parity = "none", end = ""):
		self.full_log_path = ""
		self.full_log_file = None
		self.log_path = ""
		self.log_file = None
		self.read_thread = None
		self.write_thread = None
		self.continue_read = True
		self.need_print = False
		self.first_write = True
		self.inputer = Inputer()
		self.start_wait = False
		self.mode = "reading"
		self.end = end
		self.rest_content = ""
		self.rest_wait = False

		if bytesize == 5:
			bytesize = serial.FIVEBITS
		elif bytesize == 6:
			bytesize = serial.SIXBITS
		elif bytesize == 7:
			bytesize = serial.SEVENBITS
		else:
			bytesize = serial.EIGHTBITS

		if stopbits == 2:
			stopbits = serial.STOPBITS_TWO
		elif stopbits == 1.5:
			stopbits = serial.STOPBITS_ONE_POINT_FIVE
		else:
			stopbits = serial.STOPBITS_ONE

		parity = parity.lower()
		if parity == "even":
			parity = serial.PARITY_EVEN
		elif parity == "odd":
			parity = serial.PARITY_ODD
		elif parity == "mark":
			parity = serial.PARITY_MARK
		elif parity == "space":
			parity = serial.PARITY_SPACE
		else:
			parity = serial.PARITY_NONE

		self.port = serial.Serial(COMn, baudrate = baudrate, bytesize = bytesize, stopbits = stopbits, parity = parity, timeout = 0.1)

	def full_log_into(self, filename):
		self.full_log_path = filename
		if not os.path.isdir(os.path.dirname(os.path.abspath(self.full_log_path))):
			os.makedirs(os.path.dirname(os.path.abspath(self.full_log_path)))
		self.full_log_file = open(self.full_log_path, "w")

	def log_into(self, filename):
		if self.log_file:
			self.log_file.close()

		self.log_path = filename
		if not os.path.isdir(os.path.dirname(os.path.abspath(self.log_path))):
			os.makedirs(os.path.dirname(os.path.abspath(self.log_path)))
		self.log_file = open(self.log_path, "w")

		self.first_write = True

	def open_print(self):
		self.need_print = True

	def close_print(self):
		self.need_print = False

	def write(self, value):
		if isinstance(value, str):
			self.port.write(value.encode("utf-8"))
		else:
			self.port.write(value)

	def writing(self):
		while self.continue_read:
			cmd = self.inputer.input(self.port.name + ">")
			self.exec(cmd)
			self.inputer.hide()

	def exec(self, cmd):
		cmd, cmd_type = self.check_cmd(cmd)
		if cmd_type == "system":
			os.system(cmd)
		elif cmd_type == "internal":
			self.internal_exec(cmd)
		else:
			if isinstance(cmd, str):
				self.write(cmd + self.end)
			else:
				self.write(cmd)

	def check_cmd(self, cmd):
		if not isinstance(cmd, str):
			return cmd, "write"

		temp_cmd = cmd.strip(" ").strip("\t")
		cmd_type = ""
		if len(temp_cmd) >= 2:
			if temp_cmd[0] == ":":
				cmd = temp_cmd[1:].replace("\\!", "!").replace("\\:", ":")
				cmd_type = "internal"
			elif temp_cmd[0] == "!":
				cmd = temp_cmd[1:].replace("\\!", "!").replace("\\:", ":")
				cmd_type = "system"
		else:
			cmd = cmd.replace("\\!", "!").replace("\\:", ":")
			cmd_type = "write"

		return cmd, cmd_type

	def internal_exec(self, cmd):
		argv = self.get_argv(cmd)
		if argv[0] == "write":
			if len(argv) >= 2:
				if not os.path.isfile(argv[1]):
					print("File \"" + argv[1] + "\" is not exist!")

				try:
					content = open(argv[1]).read()
				except:
					print("Error while opening file \"" + argv[1] + "\"!")

				self.write(content)
			else:
				target_path = os.path.dirname(os.path.abspath(__file__)) + "\\write_buffer"
				if not os.path.isdir(target_path):
					os.makedirs(target_path)

				target_file = target_path + "\\content.txt"

				open(target_file, "w").close()

				exit_code = os.system("where vim >nul 2>&1")
				if exit_code == 0:
					os.system("vim \"" + target_file + "\"")
				else:
					vim = os.path.dirname(os.path.abspath(__file__)) + "\\vim_portable\\vim.exe"
					vim_cmd = vim + " " + target_file
					os.system(vim_cmd)

				try:
					content = open(target_file).read()
				except:
					print("Error while opening file \"" + target_file + "\"!")

				self.write(content)
		elif argv[0] == "clear_log":
			self.log_file.close()
			self.log_file = open(self.log_path, "w")
		elif argv[0] == "exit" or argv[0] == "q" or argv[0] == "wq" or argv[0] == "quit" or argv[0] == "bye":
			os._exit(0)
		else:
			print("Error: Unknown command \"" + argv[0] + "\"")

	def get_argv(self, argv_str):
		argv = []
		arg, i = self.get_word(argv_str, 0)
		while arg != "":
			argv.append(arg)
			arg, i = self.get_word(argv_str, i)
		return argv

	def get_word(self, content, i):
		if i < 0 or i >= len(content):
			return "", -1

		while i < len(content) and content[i] in " \t":
			i += 1

		i_start = i

		while i < len(content) and content[i] not in " \t":
			i += 1

		return content[i_start:i], i

	def reading(self):
		while self.continue_read:
			try:
				n = self.port.in_waiting
			except:
				self.continue_read = False

			if self.port.in_waiting == 0:
				if self.need_print:
					if self.rest_content != "":
						self.inputer.hide()
						print(self.rest_content + "\n", end="", flush=True)
						self.rest_content = ""

					self.inputer.unhide()

				continue

			try:
				# print_content = SerialPort.filter_printable(self._read().decode("utf-8"))
				print_content = SerialPort.filter_printable(self.port.read(self.port.in_waiting).decode("utf-8"))
				if print_content == "":
					if self.need_print:
						if self.rest_content != "":
							self.inputer.hide()
							print(self.rest_content + "\n", end="", flush=True)
							self.rest_content = ""

						self.inputer.unhide()

					continue

				if self.need_print:
					pos = print_content.rfind("\n")
					if pos == -1:
						if self.rest_content == "":
							self.rest_content = print_content
						else:
							self.inputer.hide()
							print(self.rest_content + print_content + "\n", end="", flush=True)
							self.rest_content = ""
							self.inputer.unhide()
					else:
						self.inputer.hide()
						print(self.rest_content + print_content[:pos+1], end="", flush=True)
						self.rest_content = print_content[pos+1:]
						self.inputer.unhide()
						
				current_time = "[" + time.strftime("%Y-%m-%d %H:%M:%S") + "]  "
				write_content = print_content.replace("\n", "\n"+current_time)

				if self.log_file or self.full_log_file:
					if self.log_file:
						if self.first_write:
							self.log_file.write(current_time + write_content)
						else:
							self.log_file.write(write_content)
						self.log_file.flush()

					if self.full_log_file:
						if self.first_write:
							self.full_log_file.write(current_time + write_content)
						else:
							self.full_log_file.write(write_content)
						self.full_log_file.flush()

					self.first_write = False

			except:
				pass

	def start_read(self):
		if self.need_print:
			if self.write_thread is None or not self.write_thread.is_alive():
				self.write_thread = threading.Thread(target=self.writing, daemon=True)
				self.write_thread.start()

		if self.read_thread is None or not self.read_thread.is_alive():
			self.read_thread = threading.Thread(target=self.reading, daemon=True)
			self.read_thread.start()

	def end_read(self):
		self.continue_read = False
		if not self.read_thread is None and self.read_thread.is_alive():
			self.read_thread.join()
			self.read_thread = None
		if not self.write_thread is None and self.write_thread.is_alive():
			self.inputer.close()
			self.write_thread.join()
			self.write_thread = None
		if not self.log_file is None:
			self.log_file.close()
			self.log_file = None

	def close(self):
		self.end_read()
		self.port.close()

	def hold_on(self):
		while True:
			pass

	def __del__(self):
		self.close()

	def _read(self):
		content = open("port.txt", "rb").read()
		if len(content) != 0:
			open("port.txt", "wb").close()
		return content

	@staticmethod
	def ls():
		result = serial.tools.list_ports.comports()
		port_list = []
		for i in range(len(result)):
			port_list.append(result[i][0])

		return port_list

	@staticmethod
	def filter_printable(content):
		return ''.join(filter(lambda x: x in string.printable, content)).replace("\r\n", "\n").replace("\n\r", "\n").replace("\r", "\n")
 
if __name__ == "__main__":
	port = SerialPort("COM4")
	port.open_print()
	port.log_into("test.txt")
	port.start_read()
	port.hold_on()