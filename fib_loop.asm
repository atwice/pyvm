; Комманда = 32 бита
; минимально адремуем 32 бита
; Максимальное число фибоначчи в int32 - по номеру 46 значение 1836311903
var
	AX; common
	BX; common
	CX; counter
	DX; common
	req_number ; requested N
	fib_result ; result Fib[N]

data
	str_welcome = "Hello, this program counts n-th Fibonacci number.\nInput n: "
	str_result_1 = "Fibonacci( "
	str_result_2 = " ) = "
	str_endl = "\n"
	str_welcome_ptr = &str_welcome
	str_result1_ptr = &str_result_1
	str_result2_ptr = &str_result_2
	str_endl_ptr = &str_endl

;-CODE----------------------------------------------------------------------------------------------
code

main:
	call out_welcome
	inpn AX ; request in AX
	mov req_number, AX
	call calc_fib_loop
	call out_result
	push str_endl_ptr
	call print_str
	exit

; Prints unicode string up to first occurence of two zero bytes (\u0000)
; @bx [stack+4] address of string begin
print_str:
	push AX
	push BX
	mov BX SP
	sub BX 4
	load BX BX
loop_print_begin:
	load AX BX
	jz AX print_str_exit
	outu AX
	add BX 1
	jmp loop_print_begin
print_str_exit:
	pop BX
	pop AX
	ret

; prints string str_welcome
out_welcome:
	push str_welcome_ptr
	call print_str
	pop AX
	ret

; prints str_result strings
out_result:
	push str_result1_ptr
	call print_str
	pop AX
	outn req_number
	push str_result2_ptr
	call print_str
	pop AX
	outn fib_result
	ret

; returns result in @fib_result
calc_fib_loop:
	; save regs
	push AX
	push BX
	push CX
	push DX

	mov DX 0 ; fibonacci result
	mov CX req_number
	jz CX loop_fib_exit
	
	sub CX 1 ; number of sums
	mov AX 0 ; fib[0]
	mov BX 1 ; fib[1]

loop_fib_begin:
	jz CX loop_fib_exit
	mov DX BX
	add DX AX
	mov AX BX
	mov BX DX
	sub CX 1
	jmp loop_fib_begin

loop_fib_exit:
	mov fib_result DX
	; restore regs
	pop DX
	pop CX
	pop BX
	pop AX
	ret
