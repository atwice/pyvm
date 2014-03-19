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

;----------------------------------------------------------
; Main. Entry point
main:
	call out_welcome
	inpn AX ; request in AX
	mov req_number, AX
	call calc_fib_rec
	call out_result
	push str_endl_ptr
	call print_str
	exit

;----------------------------------------------------------
; Print string
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


;----------------------------------------------------------
; Func
; prints string str_welcome
out_welcome:
	push str_welcome_ptr
	call print_str
	pop AX
	ret


;----------------------------------------------------------
; Func
; prints final message with request and result
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

;----------------------------------------------------------
; Func
; Calculate Fibonacci number with loop algorithm
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


;----------------------------------------------------------
; Func
; Calculate Fibonacci number with RECURSIVE algorithm
; returns result in @fib_result
calc_fib_rec:
	push AX
	push BX
	mov AX req_number
	call calc_fib_rec_helper
	mov fib_result BX
	pop BX
	pop AX

;----------------------------------------------------------
; aux Func
; implementation of recursion
; req_number in AX
; returns result in BX
calc_fib_rec_helper:
	push AX ; dont modify arg
	push CX
	jgz AX calc_fib_rec_not_zero
	mov BX 0; Fib(0) = 0
	jmp calc_fib_rec_helper_exit

calc_fib_rec_not_zero:
	sub AX 1
	jgz AX calc_fib_rec_not_one
	mov BX 1; Fib(1) = 1
	jmp calc_fib_rec_helper_exit

calc_fib_rec_not_one:
	call calc_fib_rec_helper; Fib(n - 1)
	mov CX BX
	sub AX 1
	call calc_fib_rec_helper; Fib(n - 2)
	add BX CX

calc_fib_rec_helper_exit:
	pop CX
	pop AX
	ret