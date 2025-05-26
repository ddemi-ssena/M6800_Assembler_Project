; tests/pseudo_ops.asm
; Pseudo-Operasyon Testleri

        ORG     $0600       ; Program başlangıç adresini ayarla

START_ADDR EQU  $0600       ; Bir etikete değer ata
BYTE_VAL   EQU  $AA
WORD_VAL   EQU  $BEEF

        LDAA    #BYTE_VAL   ; EQU ile tanımlı etiketi kullan

        ORG     $0650       ; Adresi yeniden ayarla
DATA_AREA
        FCB     $01, $02, BYTE_VAL, 10, %00001111 ; Form Constant Byte
        FDB     $1234, WORD_VAL, START_ADDR+1 ; Form Double Byte (Word)
        FCC     "Hello"     ; Form Constant Characters (string)
        FCC     'M6800!'    ; Tek tırnak ile string

        ORG     $0700       ; Başka bir ORG
CODE_CONT
        LDX     #DATA_AREA
        NOP

        END                 ; Assembly sonu
FINAL_CMD LDAA #$CC         ; Bu komut END'den sonra işlenmemeli