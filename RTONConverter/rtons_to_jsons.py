# RTON parser
# written by 1Zulu and Nineteendo

# usage: put rton files in rtons & run
import os, json, struct, sys, traceback, datetime

# Default Options
options = {
	"allowNan": True,
	"allowAllJSON": True,
	"binObjClasses": (
		"drapersavedata",
		"globalsavedata",
		"playerinfolocalsavedata",
		"lootsavedata",
		"savegameheader"
	),
	"cachLimit": 128,
	"commaSeparator": "",
	"confirmPath": True,
	"datObjClasses": (
		"playerinfo",
	),
	"DEBUG_MODE": False,
	"doublePointSeparator": " ",
	"ensureAscii": False,
	"enteredPath": False,
	"indent": "\t",
	"RTONExtensions": (
		".bin",
		".dat",
		".rton",
		".section"
	),
	"RTONNoExtensions": (
		"draper_",
		"local_profiles",
		"loot",
		"_saveheader_rton"
	),
	"repairFiles": False,
	"shortNames": False,
	"sortKeys": False
}

class FakeDict(dict):
	def __init__(self, items):
		self["something"] = "something"
		self._items = items
	def items(self):
		return self._items

def warning_message(string):
	fail.write("\t" + string + "\n")
	print("\33[93m%s\33[0m" % string)

def error_message(string):
	if options["DEBUG_MODE"]:
		string = traceback.format_exc()
	
	fail.write(string + "\n")
	print("\033[91m%s\033[0m" % string)

def path_input(text):
	string = ""
	newstring = input("\033[1m%s\033[0m: " % text)
	while newstring or string == "":
		if options["enteredPath"]:
			string = newstring
		else:
			string = ""
			quoted = 0
			escaped = False
			tempstring = ""
			for char in newstring:
				if escaped:
					if quoted != 1 and char == "'" or quoted != 2 and char == '"' or quoted == 0 and char in "\\ ":
						string += tempstring + char
					else:
						string += tempstring + "\\" + char
					
					tempstring = ""
					escaped = False
				elif char == "\\":
					escaped = True
				elif quoted != 2 and char == "'":
					quoted = 1 - quoted
				elif quoted != 1 and char == '"':
					quoted = 2 - quoted
				elif quoted != 0 or char != " ":
					string += tempstring + char
					tempstring = ""
				else:
					tempstring += " "

		if string == "":
			newstring = input("\033[1m\033[91mEnter a path\033[0m: ")
		else:
			newstring = ""
			string = os.path.realpath(string)
			if options["confirmPath"]:
				newstring = input("\033[1mConfirm \033[100m%s\033[0m: " % string)

	return string

# type 08
def parse_int8(fp):
	return struct.unpack("b", fp.read(1))[0]

# type 0a
def parse_uint8(fp):
	return struct.unpack("B", fp.read(1))[0]
	
# type 10
def parse_int16(fp):
	return struct.unpack("<h", fp.read(2))[0]

# type 12
def parse_uint16(fp):
	return struct.unpack("<H", fp.read(2))[0]
	
# type 20
def parse_int32(fp):
	return struct.unpack("<i", fp.read(4))[0]

# type 22
def parse_float(fp):
	return struct.unpack("<f", fp.read(4))[0]
	
# type 24, 28, 44 and 48
def parse_varint(fp):
	result = 0
	i = 1
	while i == 1 or num > 127:
		num = struct.unpack("B", fp.read(1))[0]
		result += i * (num & 0x7f)
		i *= 128
	
	return result

# type 25, 29, 45 and 49
def parse_negative_varint(fp):
	return -parse_varint(fp)

# type 26
def parse_uint32(fp):
	return struct.unpack("<I", fp.read(4))[0]

# type 40
def parse_int64(fp):
	return struct.unpack("<q", fp.read(8))[0]

# type 42
def parse_double(fp):
	return struct.unpack("<d", fp.read(8))[0]

# type 46
def parse_uint64(fp):
	return struct.unpack("<Q", fp.read(8))[0]
	
# types 81, 90
def parse_latin_str(fp):
	return fp.read(parse_varint(fp)).decode("latin-1")
	
# type 82, 92
def parse_utf8_str(fp):
	i1 = parse_varint(fp) # Character length
	string = fp.read(parse_varint(fp)).decode()
	i2 = len(string)
	if i1 != i2:
		warning_message("SilentError: %s pos %s: Unicode string of character length %s found, expected %s" % (fp.name,fp.tell()-1,i2,i1))
	return string
	
# types 90, 91, 92, 93
def parse_cached_str(fp, code, cached_latin_strings, cached_utf8_strings):
	if code == b"\x90":
		result = parse_latin_str(fp)
		cached_latin_strings.append(result)
	if code in b"\x91":
		result = cached_latin_strings[parse_varint(fp)]
	if code in b"\x92":
		result = parse_utf8_str(fp)
		cached_utf8_strings.append(result)
	if code in b"\x93":
		result = cached_utf8_strings[parse_varint(fp)]
	
	return (result, cached_latin_strings, cached_utf8_strings)

# type 83
def parse_ref(fp):
	ch = fp.read(1)
	
	if ch == b"\x00":
		return "RTID()"
	elif ch == b"\x03":
		p1 = parse_utf8_str(fp)
		p2 = parse_utf8_str(fp)
	elif ch == b"\x02":
		p1 = parse_utf8_str(fp)
		i2 = str(parse_varint(fp))
		i1 = str(parse_varint(fp))
		p2 = i1 + "." + i2 + "." + fp.read(4)[::-1].hex()
	else:
		raise ValueError("unexpected headbyte for type 83, found: " + ch.hex())
	
	return "RTID(%s@%s)" % (p2, p1)

# type 85
def parse_map(fp, cached_latin_strings, cached_utf8_strings):
	result = []
	
	try:
		while True:
			key, cached_latin_strings, cached_utf8_strings = parse(fp, cached_latin_strings, cached_utf8_strings)
			val, cached_latin_strings, cached_utf8_strings = parse(fp, cached_latin_strings, cached_utf8_strings)
			result.append((key,val))
	except KeyError as k:
		if str(k) == 'b""':
			if options["repairFiles"]:
				warning_message("SilentError: %s pos %s: end of file" %(fp.name, fp.tell() - 1))
			else:
				raise EOFError
		else:
			raise TypeError("unknown tag " + k.args[0].hex())
	except StopIteration:
		pass
	
	return (FakeDict(result), cached_latin_strings, cached_utf8_strings)
# type 86
def parse_list(fp, cached_latin_strings, cached_utf8_strings):	
	code = fp.read(1)
	if code != b"\xfd":
		raise KeyError("List starts with " + code.hex())
	
	result = []
	i1 = 0
	i2 = parse_varint(fp)
	try:
		while True:
			val, cached_latin_strings, cached_utf8_strings = parse(fp, cached_latin_strings, cached_utf8_strings)
			result.append(val)
			i1 += 1
	except KeyError as k:
		if str(k) == 'b""':
			if options["repairFiles"]:
				warning_message("SilentError: %s pos %s: end of file" %(fp.name, fp.tell() - 1))
			else:
				raise EOFError
		else:
			raise TypeError("unknown tag " + k.args[0].hex())
	except StopIteration:
		if (i1 != i2):
			warning_message("SilentError: %s pos %s: Array of length %s found, expected %s" %(fp.name, fp.tell() - 1, i1, i2))
	
	return (result, cached_latin_strings, cached_utf8_strings)

def end(fp):
	raise StopIteration

def parse(fp, cached_latin_strings, cached_utf8_strings):
	# mappings
	mappings = {	
		b"\x00": lambda x: False,
		b"\x01": lambda x: True,
		
		b"\x08": parse_int8,  
		b"\x09": lambda x: 0, # int8_zero
		b"\x0a": parse_uint8,
		b"\x0b": lambda x: 0, # uint8_zero
		
		b"\x10": parse_int16,
		b"\x11": lambda x: 0,  # int16_zero
		b"\x12": parse_uint16,
		b"\x13": lambda x: 0, # uint16_zero
		
		b"\x20": parse_int32,
		b"\x21": lambda x: 0, # int32_zero
		b"\x22": parse_float,
		b"\x23": lambda x: 0.0, # float_zero
		b"\x24": parse_varint, # positive_int32_varint
		b"\x25": parse_negative_varint, # negative_int32_varint
		# only in NoBackup RTONs
		b"\x26": parse_uint32,
		b"\x27": lambda x: 0, #uint_32_zero
		b"\x28": parse_varint, # positive_uint32_varint
		b"\x29": parse_negative_varint, #negative_int32_varint
		
		b"\x40": parse_int64,
		b"\x41": lambda x: 0, #int64_zero
		b"\x42": parse_double,
		b"\x43": lambda x: 0.0, # double_zero
		b"\x44": parse_varint, # positive_int64_varint
		b"\x45": parse_negative_varint, # negative_int64_varint
		b"\x46": parse_uint64,
		b"\x47": lambda x: 0, # uint64_zero
		b"\x48": parse_varint, # positive_uint64_varint
		b"\x49": parse_negative_varint, # negative_uint64_varint
		
		b"\x81": parse_latin_str, # uncached string with roman characters
		b"\x82": parse_utf8_str, # uncached string with unicode characters
		b"\x83": parse_ref,
		b"\x84": lambda x: "RTID()", # Empty reference?
	
		b"\xfe": end, 
		b"\xff": end
	
	}
	cached_data = {
		b"\x85": parse_map,
		b"\x86": parse_list
	} 
	code = fp.read(1)
	# handle string types
	if code in [b"\x90", b"\x91", b"\x92", b"\x93"]:
		return parse_cached_str(fp, code, cached_latin_strings, cached_utf8_strings)
	# handle No_Backup
	elif code in cached_data:
		return cached_data[code](fp, cached_latin_strings, cached_utf8_strings)
	else:
		return (mappings[code](fp), cached_latin_strings, cached_utf8_strings)
## Recursive file convert function
def conversion(inp, out):
	if os.path.isdir(inp) and inp != pathout:
		os.makedirs(out, exist_ok=True)
		for entry in sorted(os.listdir(inp)):
			conversion(os.path.join(inp, entry), os.path.join(out, entry))
	elif os.path.isfile(inp) and (inp.lower().endswith(options["RTONExtensions"]) or os.path.basename(inp).lower().startswith(options["RTONNoExtensions"])):	
		if options["shortNames"]:
			out = os.path.splitext(out)[0]
			 
		jfn = out + ".json"
		file = open(inp, "rb")
		try:
			if file.read(8) == b"RTON\x01\x00\x00\x00":
				data = parse_map(file, [], [])[0]
				json.dump(data, open(jfn, "w"), allow_nan = options["allowNan"], ensure_ascii = options["ensureAscii"], indent = options["indent"], separators = ("," + options["commaSeparator"], ":" + options["doublePointSeparator"]), sort_keys = options["sortKeys"])
				print("wrote " + os.path.relpath(jfn, pathout))
			else:
				raise Warning("No RTON: " + inp)
		except Exception as e:
			error_message("%s in %s pos %s: %s" % (type(e).__name__, inp, file.tell() - 1, e))

try:
	os.system('')
	if getattr(sys, 'frozen', False):
		application_path = os.path.dirname(sys.executable)
	else:
		application_path = sys.path[0]

	fail = open(os.path.join(application_path, "fail.txt"), "w")
	if sys.version_info[0] < 3:
		raise RuntimeError("Must be using Python 3")
	
	print("\033[95m\033[1mRTONParser v1.1.0\n(C) 2021 by Nineteendo\033[0m\n")
	try:
		newoptions = json.load(open(os.path.join(application_path, "options.json"), "rb"))
		for key in options:
			if key in newoptions:
				if type(options[key]) == type(newoptions[key]):
					options[key] = newoptions[key]
				elif isinstance(options[key], tuple) and isinstance(newoptions[key], list):
					options[key] = tuple([str(i).lower() for i in newoptions[key]])
				elif key == "Indent" and type(newoptions[key]) in [int, type(None)]:
					options[key] = newoptions[key]
	except Exception as e:
		error_message("%s in options.json: %s" % (type(e).__name__, e))
	
	print("Working directory: " + os.getcwd())
	pathin = path_input("Input file or directory")
	if os.path.isfile(pathin):
		pathout = path_input("Output file").removesuffix(".json")
	else:
		pathout = path_input("Output directory")
		
	# Start conversion
	start_time = datetime.datetime.now()
	conversion(pathin, pathout)
	print("\033[32mfinished converting %s in %s\033[0m" % (pathin, datetime.datetime.now() - start_time))
	input("\033[95m\033[1mPRESS [ENTER]\033[0m")
except BaseException as e:
	error_message("%s: %s" % (type(e).__name__, e))

fail.close()