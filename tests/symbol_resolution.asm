; tests/symbol_resolution.asm
; Sembol (Etiket) Çözümleme Testleri

        ORG     $0800

        JMP     LATER_LABEL ; İleri referans (LATER_LABEL henüz tanımlanmadı)

EARLY_LABEL
        LDAA    #$01
        STAA    MEM_VAR     ; İleri referans

        LDX     #EARLY_LABEL ; Geri referans (EARLY_LABEL zaten tanımlı)

LATER_LABEL
        LDAB    #$02
        STAB    MEM_VAR     ; MEM_VAR hala ileri referans olabilir

        BNE     EARLY_LABEL ; Geri referanslı dallanma

MEM_VAR EQU     $0A00       ; Uzak bir adreste tanımlı bir değişken
        
        ORG     $0900
ANOTHER_BLOCK
        FCB     VAL1, VAL2
VAL1    EQU     $11
VAL2    EQU     VAL1 + $11  ; Başka bir EQU'ya referans

        END