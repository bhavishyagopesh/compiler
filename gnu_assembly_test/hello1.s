 .text
 .globl main
main:
 push %rbp
 mov %rsp, %rbp
 push $hw_str
 call puts
 add $8, %rsp
 xor %rax, %rax
 leave
 ret

 .data
hw_str:
 .asciz "Hello world!"