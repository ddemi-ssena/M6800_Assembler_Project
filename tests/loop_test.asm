; Test Kodu 1: Basit Bir Döngü
        ORG     $1000     ; Program başlangıç adresi (opsiyonel, flowchart'ı etkilemez)
START:  LDAA    #$03      ; A akümülatörüne 3 yükle
LOOP:   DECA              ; A'yı bir azalt
        BNE     LOOP      ; Eğer A sıfır değilse LOOP etiketine git
        STAA    $2000     ; A'yı $2000 adresine kaydet (döngü bittikten sonra)
        RTS               ; Alt programdan dön