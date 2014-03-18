import sys
import re
import pyvm.BinaryProgram as binProg
import pyvm.Command


class Assembler(object):
	# default code segment
	CODE = 0
	# var segment - names for variadic data cells
	VAR = 1
	# data segment - names, values and strings for constant data
	DATA = 2

	def __init__(self, asmFile, binFile):
		super(Assembler, self).__init__()
		self._asmFile = open(asmFile, encoding="utf-8")
		self._binFile = binFile
		self._binaryProgram = binProg.BinaryProgram.ConstructForAssembler()
		# 0 is reserved for IP, 1 is reserved for SP
		self._firstPassOffset = self._binaryProgram.cellsUsed()
		self._varOffsets = { "IP" : 0, "SP" : 1 }
		self._codeOffsets = {}

	def run(self):
		print("Start running assembler...")
		try:
			self.processAsmFile(True)  # lexical analisys
			self.processAsmFile(False)  # syntax analisys
			self._binaryProgram.writeSP(self._binaryProgram.cellsUsed())
			self.outputBinary()
		except Exception as e:
			print(e)
			if __debug__:
				raise e

	def _processAuxLexeme(line, segmentType):
		assert(line != "")

		if line == "var":
			return Assembler.VAR, True
		elif line == "data":
			return Assembler.DATA, True
		elif line == "code":
			return Assembler.CODE, True
		else:
			return segmentType, False

	# fill in variables offsets, label offsets
	def processAsmFile(self, firstPass):
		self._asmFile.seek(0)
		segmentType = Assembler.VAR
		for lineNumber, line in enumerate(self._asmFile):
			line = Assembler.stripComments(line)
			if line == "":
				continue
			# changes current segmentType
			segmentType, processed = Assembler._processAuxLexeme(line, segmentType)
			if processed:
				continue
			try:
				if firstPass:
					self.collectOffsets(line, segmentType)
				else:
					self.buildProgram(line, segmentType)
			except Exception as e:
				raise AssertionError(str(e) + "\n on line[" + str(lineNumber) + "]: " + line)

	def stripComments(line):
		line = line.strip()
		pos = line.find(";")
		if pos != -1:
			line = line[:pos].strip()
		return line

#
# First Pass
# Collects offset of vars, data and labels

	def _doCollectVarOffset(self, line):
		if not line.isidentifier():
			raise AssertionError("VAR is not valid identifier: " + line)
		self._varOffsets[line] = self._firstPassOffset
		self._firstPassOffset += 1
		print( line, self._firstPassOffset)

	def _doCollectDataOffset(self, line):
		parts = line.split("=", 1)
		if len(parts) < 2:
			raise AssertionError("DATA line has wrong syntax: " + line)
		varname = parts[0].strip()
		if not varname.isidentifier():
			raise AssertionError("DATA line variable name is invalid: " + varname)
		value = parts[1].strip()
		self._varOffsets[varname] = self._firstPassOffset
		if value[0] == '"' and value[-1] == '"':
			value = value.replace("\\n", "\n")
			self._firstPassOffset += (len(value) - 2) + 1 # null-terminated
		elif value.isdigit():
			self._firstPassOffset += 1
		elif value[0] == '&':
			if value[1:] not in self._varOffsets:
				raise AssertionError("Unknown variable '" + value[1:] + "'")
			self._firstPassOffset += 1
		else:
			raise AssertionError("Unknown format of DATA line: " + line)
		print( varname, self._firstPassOffset)

	def _doCollectLabelOffset(self, line):
		pos = line.find(":")
		if pos != -1:
			label = line[:pos]
			if label in self._codeOffsets:
				raise AssertionError(
					"Label '" + label + "' already processed at " + str(self._codeOffsets[label]))
			self._codeOffsets[label] = self._firstPassOffset
			print( label, self._codeOffsets[label])
		if line[pos+1:] != "":
			self._firstPassOffset += 1  # every code line is one cell

	collectOffsetByType = {
		VAR: _doCollectVarOffset,
		DATA: _doCollectDataOffset,
		CODE: _doCollectLabelOffset
	}

	def collectOffsets(self, line, segmentType):
		Assembler.collectOffsetByType[segmentType](self, line)

#
# Second Pass
# Builds binary program, using offset tables

	# in this section one line contains one variable name
	def _doBuildVar(self, line):
		print( line, self._varOffsets[line], self._binaryProgram.cellsUsed() )
		assert self._varOffsets[line] == self._binaryProgram.cellsUsed()
		nameTruncated = "%-4s" % line[:4]  # first four simbols, or left adjusted name with spaces
		bytesToWrite = nameTruncated.encode("cp1251")
		assert(len(bytesToWrite) == 4)
		self._binaryProgram.append(bytesToWrite)

	# this section contains lines of 2 types:
	# var_name = "string" ; assembler allocates memory for string with trailing 0 and saves offset
	# var_name2 = 1112223 ; for numbers assembler allocates one cell
	def _doBuildData(self, line):
		varname, value = line.split("=", 1)
		varname = varname.strip()
		value = value.strip()
		assert(self._binaryProgram.cellsUsed() == self._varOffsets[varname])
		if value[0] == '"':
			self._buildString(value.strip('"'))
		elif value[0] == '&':
			self._buildPtr(value.strip('&'))
		else:
			self._buildInt(int(value))

	def _buildString(self, value):
		value = value.replace("\\n", "\n")
		valueBytes = value.encode(encoding="utf32")[4:]  # ignore BOM
		self._binaryProgram.append(valueBytes)
		self._binaryProgram.append(b'\x00\x00\x00\x00') # null-terminated

	def _buildPtr(self, varname):
		if varname not in self._varOffsets:
			raise AssertionError("Unknown variable: " + varname)
		self._buildInt(self._varOffsets[varname])

	def _buildInt(self, intValue):
		if intValue > 2 ** 31 or intValue < -2 ** 31:
			raise AssertionError("Integer value is out of 32bit size: " + str(intValue))
		self._binaryProgram.append(intValue.to_bytes(4, byteorder='big'))

	def removeLabel(line):
		pos = line.find(":")
		return line[pos + 1:] if pos != -1 else line

	def _doBuildCommand(self, line):
		if line[:5] == "main:":
			self._binaryProgram.writeIP(self._binaryProgram.cellsUsed())
		line = Assembler.removeLabel(line).strip()
		if line == "":
			return
		commandMnemonic, target, source = self._analyzeLine(line)
		command = pyvm.Command.Command()
		command.command = self._analyzeCommand(commandMnemonic, target, source)
		tgt = self._analyzeTarget(target)
		command.setTarget(self._analyzeTarget(target))
		command.setSource(self._analyzeSource(source))

		encodedCommand = pyvm.Command.Encoder.encode(command)
		assert len(encodedCommand) == 4
		self._binaryProgram.append(encodedCommand)

	def _analyzeLine(self, line):
		parts = re.split("\W+", line)
		commandMnemonic = parts[0]
		target = None if len(parts) < 2 else parts[1]
		source = None if len(parts) < 3 else parts[2]
		if len(parts) > 3:
			raise AssertionError("Unknown command format: " + line)
		return commandMnemonic, target, source

	def _analyzeCommand(self, commandMnemonic, target, source):
		if commandMnemonic not in pyvm.Command.Omonimic:
			return pyvm.Command.OpCodeFromMnemonic[commandMnemonic]
		else:
			if source.isdigit():
				return pyvm.Command.Omonimic[commandMnemonic][1] # ***Const
			elif self._varOffsets[target] < 2 ** 8:
				return pyvm.Command.Omonimic[commandMnemonic][0] # ***Far
			else:
				if commandMnemonic != "mov":
					raise AssertionError("Command '" + commandMnemonic + "' can't have far target")
				return pyvm.Command.MovToReg

	def _analyzeTarget(self, target):
		return 0 if target is None else self._analyzeArg(target, allowNumber=False)

	def _analyzeSource(self, source):
		return 0 if source is None else self._analyzeArg(source, allowNumber=True)

	def _analyzeArg(self, arg, allowNumber):
		if arg.isidentifier():
			if arg in self._codeOffsets:
				return self._codeOffsets[arg]
			elif arg in self._varOffsets:
				return self._varOffsets[arg]
		elif allowNumber and arg.isdigit():
			return int(arg)
		raise AssertionError("Unknown argument \'" + arg + "\'")

	buildProgramByType = {
		VAR: _doBuildVar,
		DATA: _doBuildData,
		CODE: _doBuildCommand
	}

	def buildProgram(self, line, segmentType):
		Assembler.buildProgramByType[segmentType](self, line)

	def outputBinary(self):
		print("Writing output: " + self._binFile + "...")
		outFile = open(self._binFile, "wb")
		outFile.write(self._binaryProgram.binaryCode())
