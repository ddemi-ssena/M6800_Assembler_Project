; tests/direct_extended_ops.asm
; Direct ve Extended Adresleme Modu Testleri

        ORG     $0300

START   LDAA    $10         ; Direct: Load A from address $0010
        LDAB    $0020       ; Direct: Load B from address $0020 (explicit zero)
        STAA    VAR_A       ; Direct: Store A to VAR_A (VAR_A < $FF olmalı)
        STAB    $30         ; Direct: Store B to $0030
        
        ADDA    $0400       ; Extended: Add to A from $0400
        ADDB    MEM_LOC     ; Extended: Add to B from MEM_LOC
        SUBA    $0500
        SUBB    $0600
        ANDA    $0700
        ANDB    $0800
        ORAA    $0900
        ORAB    $0A00
        EORA    $0B00
        EORB    $0C00
        BITA    $0D00
        BITB    $0E00
        CMPA    $0F00
        CMPB    $1000
        SBCA    $1100
        SBCB    $1200
        ADCA    $1300
        ADCB    $1400

        LDS     $1F00       ; Extended
        LDX     BIG_ADDR    ; Extended
        STS     $00F0       ; Direct
        STX     $2000       ; Extended
        CPX     $3000       ; Extended
        
        JMP     $0450       ; Extended Jump
        JSR     SUBROUT     ; Extended Jump to Subroutine

VAR_A   EQU     $50         ; Direct adresleme için
MEM_LOC EQU     $BEE0       ; Extended adresleme için
BIG_ADDR EQU    $CDEF
SUBROUT EQU     $0888

        END