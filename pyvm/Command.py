import logging
import binascii

CommonByteOrder = "big"

def reverseDict(map):
	return {v:k for k, v in map.items()}

# MOV
# Move value of variable in "register"-memory
MovToReg = 0x00
# Move "register" value to memory
MovFromReg = 0x01
# Mov constant value to "register"
MovConstant = 0x02
# Load value of memory pointed by source to target
Load = 0x03

# Input / Output
# input number from console
InpNumber = 0x10
OutNumber = 0x11
OutUnicode = 0x12

# Arithmetics
AddFar = 0x20
AddConst = 0x21
SubFar = 0x22
SubConst = 0x23
MulFar = 0x24
MulConst = 0x25
DivIFar = 0x26
DivIConst = 0x27
ModFar = 0x28
ModConst = 0x29

# Jumps 'n' Conditional
Jmp = 0x30
JmpZero = 0x31
JmpLZ = 0x32
JmpGZ = 0x33

# Stack
Push = 0x40
Pop = 0x41

# Call 'n' Ret
Call = 0x50
Ret = 0x51

# The end of program
Exit = 0xFF

# Commands to text
MnemonicOpCodes = {
	MovToReg : "mov",
	MovFromReg : "mov",
	MovConstant : "mov",
	Load : "load",
	InpNumber : "inpn",
	OutNumber : "outn",
	OutUnicode : "outu",
	AddFar : "add",
	AddConst : "add",
	SubFar : "sub",
	SubConst : "sub",
	MulFar : "mul",
	MulConst : "mul",
	DivIFar : "divi",
	DivIConst : "divi",
	ModFar : "mod",
	ModConst : "mod",
	Jmp : "jmp",
	JmpZero : "jz",
	JmpLZ : "jlz",
	JmpGZ : "jgz",
	Push : "push",
	Pop : "pop",
	Call : "call",
	Ret : "ret",
	Exit : "exit"
}

# Text to commands
OpCodeFromMnemonic = reverseDict(MnemonicOpCodes)

Omonimic = {
	"mov" : [MovToReg, MovConstant],
	"add" : [AddFar, AddConst],
	"sub" : [SubFar, SubConst],
	"mul" : [MulFar, MulConst],
	"divi" : [DivIFar, DivIConst],
	"mod" : [ModFar, ModConst]
}

CommandWithFarTarget = frozenset( [MovFromReg, Jmp, Push, Pop, Call, Ret] )

class Command(object):

	def __init__(self):
		super(Command, self).__init__()
		self.command = Exit
		self.localPtr = 0  # Typically pointer to register or var
		self.farPtr = 0  # Typically pointer to stack, function and so on

	def setSource(self, source):
		if self.command in CommandWithFarTarget:
			self.localPtr = source
		else:
			self.farPtr = source

	def setTarget(self, target):
		if self.command in CommandWithFarTarget:
			self.farPtr = target
		else:
			self.localPtr = target

	def __str__(self):
		return self.mnemonic() + "[" + str(self.localPtr) + "]{" + str(self.farPtr) + "}"

	def mnemonic(self):
		return MnemonicOpCodes[self.command]


class Encoder(object):

	"""docstring for Encoder"""

	def __init__(self):
		super(Encoder, self).__init__()

	def checkArgumentLength(command):
		if command.localPtr > 255:
			raise AssertionError( "Encoding error. Command " + command.mnemonic() + " has too long local argument" )
		if command.farPtr > 2**16 - 1:
			raise AssertionError( "Encoding error. Command " + command.mnemonic() + " has too long far argument" )

	def encode(command):
		Encoder.checkArgumentLength(command)
		byteCode = bytearray(4)
		byteCode[0:1] = command.command.to_bytes(1, CommonByteOrder)
		byteCode[1:2] = command.localPtr.to_bytes(1, CommonByteOrder)
		byteCode[2:4] = command.farPtr.to_bytes(2, CommonByteOrder)
		return byteCode

	def decode(byteCode):
		command = Command()
		command.command = int.from_bytes(byteCode[0:1], CommonByteOrder)
		command.localPtr = int.from_bytes(byteCode[1:2], CommonByteOrder)
		command.farPtr = int.from_bytes(byteCode[2:4], CommonByteOrder)
		logging.debug("Decode (%s) -> {%x}[%x][%x]"%( binascii.hexlify(byteCode), command.command, command.localPtr, command.farPtr))
		return command


class Executor(object):

	"""docstring for Executor"""

	def __init__(self, binaryProgram):
		super(Executor, self).__init__()
		self._prog = binaryProgram
		self.isFinished = False

	def executeOneCommand(self):
		ip = self._prog.readIP()
		binaryCommand = self._prog.readCell(ip)
		command = Encoder.decode(binaryCommand)
		logging.debug( "ip = %x\t{%x} [%x] [%x]"%(ip, command.command, command.localPtr, command.farPtr))
		doIncIp = Executor.commands[command.command](self, command.localPtr, command.farPtr)
		if doIncIp:
			self._prog.incIP()

	def _doMovToReg(self, localPtr, farPtr):
		value = self._prog.readCell(farPtr)
		self._prog.writeCell(localPtr, value)
		logging.debug( "ip = %x\tMovToReg target:[%x] [%x]=%s"%(self._prog.readIP(), localPtr, farPtr, binascii.hexlify(value)))
		return True

	def _doMovFromReg(self, localPtr, farPtr):
		value = self._prog.readCell(localPtr)
		self._prog.writeCell(farPtr, value)
		logging.debug( "ip = %x\tMovFromReg source[%x] target[%x]=%s"%(self._prog.readIP(), localPtr, farPtr, binascii.hexlify(value)))
		return True

	def _doMovConstant(self, localPtr, farPtr):
		self._prog.writeInt(localPtr, farPtr)
		return True

	def _doLoad(self, localPtr, farPtr):
		ptr = self._prog.readInt(farPtr)
		value = self._prog.readCell(ptr)
		self._prog.writeCell(localPtr, value)
		logging.debug("Load to [%x] from [%x]=%x ={%s}"%(localPtr, farPtr, ptr, binascii.hexlify(value)))
		return True

	def _doInpNumber(self, localPtr, farPtr):
		value = input()
		intValue = 0
		try:
			intValue = int(value)
		except TypeError:
			print( "Error converting from '" + value + "' to int" )
			isFinished = True
		self._prog.writeInt(localPtr, intValue)
		return True

	def _doOutNumber(self, localPtr, farPtr):
		intValue = self._prog.readInt(localPtr)
		print(intValue, end="")
		return True

	def _doOutUnicode(self, localPtr, farPtr):
		unicodeChar = self._prog.readCell(localPtr).decode(encoding="utf32")
		logging.debug("OutUnicode from [%x]=%s"%(localPtr, unicodeChar))
		print( unicodeChar, end='' )
		return True

	def _doAddFar(self, localPtr, farPtr):
		farInt = self._prog.readInt(farPtr)
		localInt = self._prog.readInt(localPtr)
		self._prog.writeInt(localPtr, localInt + farInt)
		return True

	def _doAddConst(self, localPtr, farPtr):
		localInt = self._prog.readInt(localPtr)
		self._prog.writeInt(localPtr, localInt + farPtr)
		return True

	def _doSubFar(self, localPtr, farPtr):
		farInt = self._prog.readInt(farPtr)
		localInt = self._prog.readInt(localPtr)
		self._prog.writeInt(localPtr, localInt - farInt)
		return True

	def _doSubConst(self, localPtr, farPtr):
		localInt = self._prog.readInt(localPtr)
		self._prog.writeInt(localPtr, localInt - farPtr)
		return True

	def _doMulFar(self, localPtr, farPtr):
		farInt = self._prog.readInt(farPtr)
		localInt = self._prog.readInt(localPtr)
		self._prog.writeInt(localPtr, localInt * farInt)
		return True

	def _doMulConst(self, localPtr, farPtr):
		localInt = self._prog.readInt(localPtr)
		self._prog.writeInt(localPtr, localInt * farPtr)
		return True

	def _doDivIFar(self, localPtr, farPtr):
		farInt = self._prog.readInt(farPtr)
		localInt = self._prog.readInt(localPtr)
		self._prog.writeInt(localPtr, localInt // farInt)
		return True

	def _doDivIConst(self, localPtr, farPtr):
		localInt = self._prog.readInt(localPtr)
		self._prog.writeInt(localPtr, localInt // farPtr)
		return True

	def _doModFar(self, localPtr, farPtr):
		farInt = self._prog.readInt(farPtr)
		localInt = self._prog.readInt(localPtr)
		self._prog.writeInt(localPtr, localInt % farInt)
		return True

	def _doModConst(self, localPtr, farPtr):
		localInt = self._prog.readInt(localPtr)
		self._prog.writeInt(localPtr, localInt % farPtr)
		return True

	def _doJmp(self, localPtr, farPtr):
		self._prog.writeIP(farPtr)
		return False

	def _doJmpZero(self, localPtr, farPtr):
		value = self._prog.readInt(localPtr)
		if value == 0:
			self._prog.writeIP(farPtr)
			return False
		return True

	def _doJmpLZ(self, localPtr, farPtr):
		value = self._prog.readInt(localPtr)
		if value < 0:
			self._prog.writeIP(farPtr)
			return False
		return True

	def _doJmpGZ(self, localPtr, farPtr):
		value = self._prog.readInt(localPtr)
		if value > 0:
			self._prog.writeIP(farPtr)
			return False
		return True

	def _doPush(self, localPtr, farPtr):
		stackPtr = self._prog.readSP()
		value = self._prog.readCell(farPtr)
		logging.debug( "ip = %x\tPush stack(%x) [%x]=%s"%(self._prog.readIP(), stackPtr, farPtr, binascii.hexlify(value)))
		self._prog.writeCell(stackPtr, value)
		self._prog.writeSP(stackPtr + 1)
		return True

	def _doPop(self, localPtr, farPtr):
		stackPtr = self._prog.readSP()
		value = self._prog.readCell(stackPtr - 1)
		self._prog.writeCell(farPtr, value)
		self._prog.writeSP(stackPtr - 1)
		return True

	def _doCall(self, localPtr, farPtr):
		logging.debug( "ip = %x\tCall [%x]"%(self._prog.readIP(), farPtr))
		self._prog.incIP() # to return to next statement
		self._doPush(0, 0) # push IP
		self._prog.writeIP(farPtr)
		return False

	def _doRet(self, localPtr, farPtr):
		self._doPop(0, 0) # write directly to IP
		return False

	def _doExit(self, localPtr, farPtr):
		self.isFinished = True
		return False


	commands = {
		MovToReg : _doMovToReg,
		MovFromReg : _doMovFromReg,
		MovConstant : _doMovConstant,
		Load : _doLoad,
		InpNumber : _doInpNumber,
		OutNumber : _doOutNumber,
		OutUnicode : _doOutUnicode,
		AddFar : _doAddFar,
		AddConst : _doAddConst,
		SubFar : _doSubFar,
		SubConst : _doSubConst,
		MulFar : _doMulFar,
		MulConst : _doMulConst,
		DivIFar : _doDivIFar,
		DivIConst : _doDivIConst,
		ModFar : _doModFar,
		ModConst : _doModConst,
		Jmp : _doJmp,
		JmpZero : _doJmpZero,
		JmpLZ : _doJmpLZ,
		JmpGZ : _doJmpGZ,
		Push : _doPush,
		Pop : _doPop,
		Call : _doCall,
		Ret : _doRet,
		Exit : _doExit
	}