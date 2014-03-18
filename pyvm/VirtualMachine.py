import pyvm.BinaryProgram
import pyvm.Command

class VirtualMachine(object):

	def __init__(self, binFile):
		super(VirtualMachine, self).__init__()
		binaryProgram = pyvm.BinaryProgram.BinaryProgram.LoadFile(binFile)
		self._executor = pyvm.Command.Executor(binaryProgram)

	def run(self):
		print("Start running VirtualMachine")
		
		while not self._executor.isFinished:
			self._executor.executeOneCommand()

		print("Program is finished")
