; tests/relative_ops.asm
; Relative Adresleme Modu (Dallanma) Testleri

        ORG     $0500

START   LDAA    #$00
        LDAB    #$05
LOOP    DECA
        DECB
        BNE     LOOP        ; Geri dallanma (Z=0 ise)
        BEQ     EQUAL       ; İleri dallanma (Z=1 ise)
        BRA     ALWAYS_JUMP ; Koşulsuz ileri dallanma

DUMMY1  NOP
DUMMY2  NOP

EQUAL   INCA
        BCC     CARRY_CLEAR ; İleri dallanma (C=0 ise)
        BCS     CARRY_SET   ; İleri dallanma (C=1 ise)

ALWAYS_JUMP
        LDX     #$0000
BACK_TARGET
        INX
        CPX     #$000A
        BLT     BACK_TARGET ; Geri dallanma (N^V=1 ise) - CPX N ve V'yi etkiler
        BPL     POSITIVE    ; İleri dallanma (N=0 ise)
        BMI     NEGATIVE    ; İleri dallanma (N=1 ise)

CARRY_CLEAR
        BSR     SUB_ROUTINE ; Subroutine'e dallanma
        BGT     GREATER_THAN
        BVS     OVERFLOW_SET
        NOP

CARRY_SET
        BHI     HIGHER
        BGE     GREATER_EQUAL
        NOP

POSITIVE
        BLS     LOWER_SAME
        BLE     LESS_EQUAL
        NOP
        
NEGATIVE
        BVC     OVERFLOW_CLEAR
        NOP

SUB_ROUTINE
        PSHA
        LDAA    #$AA
        PULA
        RTS                 ; Subroutine'den dön

GREATER_THAN NOP
OVERFLOW_SET NOP
HIGHER NOP
GREATER_EQUAL NOP
LOWER_SAME NOP
LESS_EQUAL NOP
OVERFLOW_CLEAR NOP

        END