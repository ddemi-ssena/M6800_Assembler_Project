; tests/indexed_ops.asm
; Indexed Adresleme Modu Testleri

        ORG     $0400

START   LDX     #$1000      ; Index register'ı başlat
        LDAA    0,X         ; Load A from (X + 0)
        LDAB    $0A,X       ; Load B from (X + $0A)
        STAA    OFFSET,X    ; Store A to (X + OFFSET)
        STAB    255,X       ; Store B to (X + 255) -> en büyük offset
        
        ADDA    1,X
        ADDB    $F0,X
        SUBA    2,X
        SUBB    $E0,X
        ANDA    3,X
        ANDB    $D0,X
        ORAA    4,X
        ORAB    $C0,X
        EORA    5,X
        EORB    $B0,X
        BITA    6,X
        BITB    $A0,X
        CMPA    7,X
        CMPB    $90,X
        SBCA    8,X
        SBCB    $80,X
        ADCA    9,X
        ADCB    $70,X

        LDS     $10,X
        LDX     $20,X       ; Dikkat: X'i değiştiriyor!
        STS     $30,X
        STX     $40,X       ; Dikkat: X'i değiştiriyor!
        CPX     $50,X       ; Dikkat: X'i değiştiriyor!

        JMP     $00,X
        JSR     ROUTINE_X,X ; X'e göre Subroutine'e atla

OFFSET  EQU     $20
ROUTINE_X EQU   $05

        END