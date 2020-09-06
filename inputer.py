import msvcrt
import os

class Inputer:
	def __init__(self, history_filename = None):
		self.current_str = ""
		self.current_cursor = 0
		self.xe0_map = {"H": "Up", "P": "Down", "K": "Left", "M": "Right", "S": "Del"}

		# Ctrl + H, Ctrl + I, Ctrl + M is not supported
		self.ctrl_list = [b"\x01", b"\x02", b"\x03", b"\x04", b"\x05", b"\x06", b"\x07", b"\x0A", b"\x0B", b"\x0C", b"\x0E", b"\x0F", b"\x10", b"\x11", b"\x12", b"\x13", b"\x14", b"\x15", b"\x16", b"\x17", b"\x18", b"\x19", b"\x1A"]
		self.xe0_mode = False
		self.x00_mode = False

		if history_filename is None:
			self.history_file = None
			self.history_cmds = []
			self.history_index = len(self.history_cmds)
		else:
			self.use_history(history_filename)
		self.not_exe_cmd = ""
		self.illegal_ch = "/\\:*<>?\"|"
		self.is_block = False
		self.is_hidden = False
		self.prompt = ""
		self.sent_ctrl_mode = "none"

	def __del__(self):
		if not self.history_file is None:
			self.history_file.close()

	def use_history(self, filename):
		if not os.path.isdir(os.path.dirname(os.path.abspath(filename))):
			os.makedirs(os.path.dirname(os.path.abspath(filename)))

		if os.path.isfile(filename):
			self.history_cmds = open(filename).read().split("\n")
			self.history_cmds = [cmd for cmd in self.history_cmds if cmd != ""]
		else:
			self.history_cmds = []

		self.history_index = len(self.history_cmds)
		self.history_file = open(filename, "a")

	def backspace(self, n = 1):
		n = min(n, self.current_cursor)
		if n <= 0:
			return

		N = n+3*self.current_str[self.current_cursor-n : self.current_cursor].count("\t")
		tail_str = self.current_str[self.current_cursor:].replace("\t", "    ") + " "*N
		self.current_str = self.current_str[:self.current_cursor-n] + self.current_str[self.current_cursor:]
		self.current_cursor -= n

		if not self.is_hidden:
			print("\b"*N + tail_str + "\b"*len(tail_str), end="", flush=True)

	def delete(self, n = 1):
		n = min(n, len(self.current_str)-self.current_cursor)
		if n <= 0:
			return

		N = n+3*self.current_str[self.current_cursor : self.current_cursor+n].count("\t")

		tail_str = self.current_str[self.current_cursor+n:].replace("\t", "    ") + " "*N
		self.current_str = self.current_str[:self.current_cursor] + self.current_str[self.current_cursor+n:]

		if not self.is_hidden:
			print(tail_str + "\b"*len(tail_str), end="", flush=True)

	def left(self, n = 1):
		n = min(n, self.current_cursor)
		if n <= 0:
			return

		N = n+3*self.current_str[self.current_cursor-n : self.current_cursor].count("\t")

		if not self.is_hidden:
			print("\b"*N, end="", flush=True)

		self.current_cursor -= n

	def right(self, n = 1):
		n = min(n, len(self.current_str)-self.current_cursor)
		if n <= 0:
			return

		if not self.is_hidden:
			print(self.current_str[self.current_cursor:self.current_cursor+n].replace("\t", "    "), end="", flush=True)

		self.current_cursor += n

	def up(self):
		if self.history_index == 0:
			return

		if self.history_index == len(self.history_cmds):
			self.not_exe_cmd = self.current_str

		self.history_index -= 1

		self.flush()
		self.insert(self.history_cmds[self.history_index])

	def down(self):
		if self.history_index == len(self.history_cmds):
			return

		self.history_index += 1

		self.flush()
		if self.history_index == len(self.history_cmds):
			self.insert(self.not_exe_cmd)
		else:
			self.insert(self.history_cmds[self.history_index])

	def insert(self, content):
		tail_str = self.current_str[self.current_cursor:]
		self.current_str = self.current_str[:self.current_cursor] + content + tail_str
		if not self.is_hidden:
			print(content.replace("\t", "    ") + tail_str.replace("\t", "    ") + '\b'*len(tail_str.replace("\t", "    ")), end="", flush=True)
		self.current_cursor += len(content)

	def flush(self):
		self.left(self.current_cursor)
		self.delete(len(self.current_str))

	def block(self):
		self.is_block = True

	def unblock(self):
		self.is_block = False

	def hide(self):
		if self.is_hidden:
			return

		n = len(self.prompt) + len(self.current_str) + 3*self.current_str.count("\t")
		print("\b"*(len(self.prompt) + self.current_cursor+3*self.current_str[:self.current_cursor].count("\t")) + " "*n + "\b"*n, end="", flush=True)

		self.is_hidden = True

	def unhide(self):
		if self.sent_ctrl_mode == "in_unhide":
			self.sent_ctrl_mode = "in_hide"

		if not self.is_hidden:
			return

		print(self.prompt + self.current_str.replace("\t", "    ") + "\b"*(len(self.current_str[self.current_cursor:].replace("\t", "    "))), end="", flush=True)
		self.is_hidden = False

	def input(self, prompt = ""):
		self.prompt = prompt

		if self.sent_ctrl_mode == "in_unhide":
			self.unhide()
		elif not self.is_hidden:
			print(self.prompt + self.current_str.replace("\t", "    ") + "\b"*(len(self.current_str[self.current_cursor:].replace("\t", "    "))), end="", flush=True)
			
		if self.history_file is None:
			for ch in self.illegal_ch:
				prompt = prompt.replace(ch, "_")
			self.use_history(os.path.dirname(os.path.abspath(__file__)) + "/history/" + prompt)
		while True:
			try:
				raw = msvcrt.getch()
				self.sent_ctrl_mode = "none"
				if raw in self.ctrl_list:
					if self.is_hidden:
						self.sent_ctrl_mode = "in_hide"
					else:
						self.hide()
						self.sent_ctrl_mode = "in_unhide"

					print("[ sent Ctrl + " + chr(ord('A')+int.from_bytes(raw, byteorder="little")-1) + " ]", flush=True)
					# self.unhide()
					# continue
					return raw

				if self.is_block:
					continue

				if raw in [b"\xe0", b"\x00"]:
					self.xe0_mode = True
					continue
				# if raw == b"\x00":
				# 	self.x00_mode = True
				# 	continue
				# if self.x00_mode:
				# 	self.x00_mode = False
				# 	continue
				ch = str(raw, encoding="utf-8")
				if self.xe0_mode:
					self.xe0_mode = False
					if ch in self.xe0_map:
						ch = self.xe0_map[ch]
					else:
						continue
			except:
				continue

			if not (ch.isprintable() or ch in "\r\n\t\b"):
				continue

			if ch in "\n\r":
				print("", flush=True)
				if self.current_str.replace(" ", "").replace("\t", "") != "":
					self.history_cmds.append(self.current_str)
					self.history_file.write(self.current_str+"\n")
					self.history_file.flush()
				self.history_index = len(self.history_cmds)
				result = self.current_str
				self.current_str = ""
				self.current_cursor = 0
				self.prompt = ""
				return result
			elif ch == "\b":
				self.backspace()
			elif ch == "Del":
				self.delete()
			elif ch == "Left":
				self.left()
			elif ch == "Right":
				self.right()
			elif ch == "Up":
				self.up()
			elif ch == "Down":
				self.down()
			else:
				self.insert(ch)

if __name__ == "__main__":
	inputer = Inputer()
	while True:
		a = inputer.input(">")
	# import threading
	# import time
	# def modify(inputer):
	# 	time.sleep(4)
	# 	inputer.hide()
	# 	time.sleep(4)
	# 	inputer.unhide()

	# inputer = Inputer()
	# thread = threading.Thread(target=modify, args=(inputer,))
	# thread.start()
	
	# cmd = inputer.input(">")
	# thread.join()
	# # a = input(">")