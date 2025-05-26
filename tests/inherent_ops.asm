; tests/inherent_ops.asm
; Inherent ve Akümülatör Adresleme Modu Testleri

        ORG     $0100       ; Program başlangıç adresi

START   NOP                 ; No Operation
        INCA                ; Increment Accumulator A
        DECA                ; Decrement Accumulator A
        INCB                ; Increment Accumulator B
        DECB                ; Decrement Accumulator B
        CLC                 ; Clear Carry Flag
        SEC                 ; Set Carry Flag
        CLI                 ; Clear Interrupt Mask
        SEI                 ; Set Interrupt Mask
        CLV                 ; Clear Overflow Flag
        SEV                 ; Set Overflow Flag
        TAP                 ; Transfer A to CCR
        TPA                 ; Transfer CCR to A
        INX                 ; Increment Index Register
        DEX                 ; Decrement Index Register
        INS                 ; Increment Stack Pointer
        DES                 ; Decrement Stack Pointer
        TSX                 ; Transfer Stack Pointer to Index Register
        TXS                 ; Transfer Index Register to Stack Pointer
        PULA                ; Pull A from Stack
        PULB                ; Pull B from Stack
        PSHA                ; Push A to Stack
        PSHB                ; Push B to Stack
        RTS                 ; Return from Subroutine
        RTI                 ; Return from Interrupt
        SWI                 ; Software Interrupt
        WAI                 ; Wait for Interrupt

        ABA                 ; Add B to A
        SBA                 ; Subtract B from A
        CBA                 ; Compare B to A
        TAB                 ; Transfer A to B
        TBA                 ; Transfer B to A

        CLRA                ; Clear Accumulator A
        CLRB                ; Clear Accumulator B
        COMA                ; Complement A
        COMB                ; Complement B
        NEGA                ; Negate A
        NEGB                ; Negate B
        ROLA                ; Rotate A Left
        ROLB                ; Rotate B Left
        RORA                ; Rotate A Right
        RORB                ; Rotate B Right
        ASLA                ; Arithmetic Shift Left A
        ASLB                ; Arithmetic Shift Left B
        ASRA                ; Arithmetic Shift Right A
        ASRB                ; Arithmetic Shift Right B
        LSRA                ; Logical Shift Right A
        LSRB                ; Logical Shift Right B
        DAA                 ; Decimal Adjust A

        END