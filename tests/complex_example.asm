; tests/complex_example.asm
; Karmaşık Örnek Program

        ORG     $0C00
STACK_TOP EQU   $01FF       ; Stack için en üst adres

MAIN    LDS     #STACK_TOP  ; Stack pointer'ı ayarla
        LDX     #MESSAGE    ; Mesajın adresini X'e yükle
        JSR     PRINT_MSG   ; Mesajı yazdıracak alt programa git
        SWI                 ; Programı sonlandır (simülatörde durdur)

; ALT PROGRAM: PRINT_MSG
; X register'ında adresi verilen null-terminated string'i
; (varsayımsal bir) $E000 adresindeki bir çıkış portuna yazar.
; (Bu kısım daha çok simülatör için anlamlı olurdu, assembler sadece çevirir)
PRINT_MSG
        PSHA                ; A register'ını stack'e kaydet
PRINT_LOOP
        LDAA    0,X         ; X'in gösterdiği karakteri A'ya al
        BEQ     PRINT_DONE  ; Eğer null karakter ise (0), bitir
        STAA    $E000       ; Karakteri çıkış portuna yaz (varsayım)
        INX                 ; Sonraki karaktere geç
        BRA     PRINT_LOOP  ; Döngüye devam et
PRINT_DONE
        PULA                ; A register'ını stack'ten geri al
        RTS                 ; Çağıran yere dön

MESSAGE FCC     "M6800 ROCKS!"
        FCB     $00         ; String sonu (null terminator)

        END