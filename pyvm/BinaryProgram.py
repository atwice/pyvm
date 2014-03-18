class BinaryProgram(object):

	def LoadFile(binaryFileName):
		file = open(binaryFileName, "rb")
		program = BinaryProgram()
		binProgram = file.read()
		program._cellsUsed = len(binProgram)
		program._binaryCode = bytearray(1024)
		program._binaryCode[0:0] = binProgram
		return program

	def ConstructForAssembler():
		program = BinaryProgram()
		program._binaryCode = bytearray(1024) # 1K
		program._cellsUsed = 2  # 0 is reserved for IP, 1 is reserved for SP
		return program

	def __init__(self):
		super(BinaryProgram, self).__init__()
		self._binaryCode = bytearray()
		self._cellsUsed = 0

	def binaryCode(self):
		return self._binaryCode[0: self._cellsUsed * 4]

	def cellsUsed(self):
		return self._cellsUsed

	def append(self, valueBytes):
		length = len(valueBytes)
		assert(length % 4 == 0)
		offset = self._cellsUsed * 4
		self._cellsUsed += length // 4
		self._binaryCode[offset: offset + length] = valueBytes

	def readIP(self):
		return self.readInt(0)

	def writeIP(self, value):
		self.writeInt(0, value)

	def incIP(self):
		value = self.readInt(0)
		self.writeInt(0, value + 1)

	def readSP(self):
		return self.readInt(1)

	def writeSP(self, value):
		self.writeInt(1, value)

	def readCell(self, cellNumber):
		return self._binaryCode[cellNumber*4 : cellNumber*4 + 4]

	def readInt(self, cellNumber):
		return int.from_bytes(self.readCell(cellNumber), byteorder='big', signed = True)

	def writeCell(self, cellNumber, value):
		self._binaryCode[cellNumber*4 : cellNumber*4 + 4] = value

	def writeInt(self, cellNumber, intValue):
		return self.writeCell(cellNumber, intValue.to_bytes(4, byteorder='big', signed = True))
