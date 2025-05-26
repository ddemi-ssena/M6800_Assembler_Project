; tests/immediate_ops.asm
; Immediate Adresleme Modu Testleri

        ORG     $0200

START   LDAA    #$FF        ; Load A with FF
        LDAB    #10         ; Load B with decimal 10
        ADDA    #$01        ; Add 01 to A
        ADDB    #%00000101  ; Add binary 5 to B
        SUBA    #LABEL_VAL  ; Subtract value of LABEL_VAL from A
        SUBB    #5
        ANDA    #$F0
        ANDB    #%11110000
        ORAA    #$0F
        ORAB    #%00001111
        EORA    #$AA
        EORB    #%01010101
        BITA    #$55        ; Test bits in A
        BITB    #$CC
        CMPA    #$7F        ; Compare A with 7F
        CMPB    #128        ; Compare B with 128 (dikkat: işaretli/işaretsiz)
        SBCA    #$00        ; Subtract with Carry
        SBCB    #$00
        ADCA    #$00        ; Add with Carry
        ADCB    #$00

        LDS     #$1FFF      ; Load Stack Pointer (16-bit immediate)
        LDX     #POINTER    ; Load Index Register (16-bit immediate)
        CPX     #$BEEF      ; Compare Index Register (16-bit immediate)

LABEL_VAL EQU   $0A         ; Bir etiket tanımı
POINTER EQU     $C000

        END