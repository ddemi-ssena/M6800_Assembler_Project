; Test Kodu 2: Koşullu Dallanma
        ORG     $1000
MAIN:   LDAA    #$10      ; A'ya bir değer yükle
        CMPA    #$05      ; A'yı 5 ile karşılaştır
        BEQ     EQUAL     ; Eğer eşitse EQUAL etiketine git
                          ; Değilse (eşit değilse) devam et
NOT_EQUAL_PATH:
        LDAB    #$AA      ; B'ye $AA yükle (eşit değil yolu)
        BRA     FINISH    ; FINISH etiketine git
EQUAL_PATH:
EQUAL:  LDAB    #$BB      ; B'ye $BB yükle (eşit yolu)
FINISH: STAB    $2001     ; B'yi $2001 adresine kaydet
        RTS