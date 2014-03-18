import sys
import pyvm.Assembler as asm
import pyvm.Disassembler as disasm
import pyvm.VirtualMachine as vm

import logging

logging.basicConfig(filename='pyvm.log', level=logging.INFO)

def disassemble(fileName):
	disassembler = disasm.Disassembler(fileName)
	print(disassembler.run())


def assemble(asmFileName, outFileName):
	assembler = asm.Assembler(asmFileName, outFileName)
	assembler.run()


def executeVM(fileName):
	virtualMachine = vm.VirtualMachine(fileName)
	virtualMachine.run()

usage = """usage:
vm.py -asm -o:[target binary file] [source file]
	Compile binary program
vm.py -disasm [binary file]
	Decompile binary to assembly source
vm.py [binary file]
	Execute program"""

def main():
	if len(sys.argv) < 2:
		showHelp()
	elif len(sys.argv) == 2:
		arg = sys.argv[1]
		if arg[:2].lower() == "-h":
			showHelp()
			return
		fileName = sys.argv[1]
		executeVM(fileName)

	mode = sys.argv[1]
	if mode == "-disasm":
		fileName = sys.argv[2]
		disassemble(fileName)
	elif mode == "-asm":
		out = sys.argv[2]
		if out[:3] != "-o:":
			showHelp()
			return
		fileName = sys.argv[3]
		assemble(fileName, out[3:])

def showHelp():
	print( usage )

if __name__ == '__main__':
	main()
