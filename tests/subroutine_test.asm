; Test Kodu 3: Alt Program Çağrısı
        ORG     $C000
MAIN_PROG:
        LDAA    #$01
        JSR     MY_SUB    ; MY_SUB alt programını çağır
        ADDA    #$02
        RTS

MY_SUB:
        PSHA              ; A'yı yığına kaydet
        LDAB    #$F0
        PULA              ; A'yı yığından geri al
        RTS               ; Alt programdan dön