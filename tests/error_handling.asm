; tests/error_handling.asm
; Hata Yönetimi Testleri

        ORG     $0A00

START   LDAA    #$1000      ; HATA: Immediate değer 8-bit olmalı
        LDAB    UNDEFINED_LABEL ; HATA: Tanımsız etiket
        BADCMD  $10         ; HATA: Bilinmeyen komut
        NOP     EXTRA_OPERAND ; HATA: NOP operand almaz
        LDAA                ; HATA: LDAA operand bekler
        STAA    $00,Y       ; HATA: M6800'de ,Y ile indexed mod yok (genellikle)
        BNE     $FF0000     ; HATA: Relative offset menzil dışı
        
LABEL1  EQU     $10
LABEL1  EQU     $20         ; HATA: Etiket yeniden tanımlama

        FCB     $100        ; HATA: FCB değeri 8-bit olmalı
        FDB     $100000     ; HATA: FDB değeri 16-bit olmalı
        FCC     "MissingQuote ; HATA: String tırnağı kapanmamış
        FCC     NoQuotes    ; HATA: FCC string tırnak içinde olmalı

        ORG     BAD_VAL     ; HATA: ORG için geçersiz değer (etiket tanımsızsa)
        
ANOTHER ORG     $0B00       ; HATA: Etiket ve ORG aynı satırda olmamalı (lexer'a bağlı)
                            ; Ya da ORG'nin etiketi olmamalı (assembler kuralına bağlı)
                            ; Bizim lexer bunu "ANOTHER" label, "ORG" mnemonic, "$0B00" operand olarak alabilir.
                            ; Ama eğer ORG'nin label almaması gerekiyorsa bu bir semantic hata olurdu.
BAD_EQU         $50         ; HATA: EQU için etiket eksik (eğer EQU komutu label bekliyorsa)
                            ; Bizim lexer bunu BAD_EQU label, $50 mnemonic olarak alabilir -> Bilinmeyen komut
MY_EQU  EQU                 ; HATA: EQU için değer eksik

        END
        LDAA    #0          ; Bu satır işlenmemeli (END'den sonra)