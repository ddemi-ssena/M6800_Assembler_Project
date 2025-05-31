; pass1_label_equ_errors.asm
; Tekrarlayan etiketleri ve EQU için operand eksikliğini test eder.

START   EQU     $C000       ; Bu geçerli
        ORG     START

; Aşağıdaki satırı aktif bırakabilirsiniz, lexer hatası vermeli
BAD:SYNTAX RMB 1            ; Hata: Lexer bu satırı işlemeli (önceki testten)

GOOD_EQU  EQU   $20

DUP_LABEL EQU   $30
DUP_LABEL EQU   $40         ; Hata: Tekrarlayan EQU etiket tanımı

ANOTHER_DUP_LABEL           ; İlk tanım (geçerli)
ANOTHER_DUP_LABEL RMB 1     ; Hata: Tekrarlayan normal etiket tanımı

NO_OPERAND_EQU EQU          ; Hata: EQU için operand eksik

NO_OPERAND_RMB RMB          ; Hata: RMB için operand eksik

NO_OPERAND_ORG ORG          ; Hata: ORG için operand eksik

LABEL_ONLY_VALID            ; Bu sadece bir etiket, hata olmamalı
        LDAA    #GOOD_EQU

        END