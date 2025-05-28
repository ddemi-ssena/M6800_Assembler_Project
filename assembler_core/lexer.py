# assembler_core/lexer.py
import re
# OPCODE_TABLE'ı import etmemiz gerekecek, bu yüzden bir üst dizindeki
# m6800_opcodes.py dosyasından alacağız.
# Proje yapınıza göre bu import yolu değişebilir.
# Eğer lexer.py ve m6800_opcodes.py aynı dizindeyse:
# from .m6800_opcodes import OPCODE_TABLE
# Eğer assembler_core bir paketse ve ana dizinden çalıştırıyorsanız:
from .m6800_opcodes import OPCODE_TABLE, PSEUDO_OPS # Bu satırı ana script'ten çalıştırırken kullanın


# Etiketler için geçerli karakterler (basit bir regex)
# İlk karakter harf, sonrakiler harf, rakam veya alt çizgi olabilir.
# M6800 etiketleri genellikle 6 karakterle sınırlıydı, ama modern assembler'lar daha esnek olabilir.
# Şimdilik uzunluk kontrolü eklemeyelim.
LABEL_REGEX = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")

def parse_line(line_number, text_line):
    """
    Bir assembly satırını etiket, mnemonic, operand ve yorum olarak ayırır.
    OPCODE_TABLE ve PSEUDO_OPS kullanarak etiket ve mnemonic ayrımını yapar.
    Dönüş: {"line_num": int, "original_line": str, "label": str|None,
            "mnemonic": str|None, "operand_str": str|None, "comment": str|None, "error": str|None}
    """
    original_line = text_line
    processed_line = text_line.strip() # Başta ve sonda olabilecek tüm boşlukları kaldır

    result = {
        "line_num": line_number,
        "original_line": original_line.rstrip('\n'),
        "label": None,
        "mnemonic": None,
        "operand_str": None,
        "comment": None,
        "error": None
    }

    if not processed_line: # Boş satır
        return result

    # 1. Yorumu ayır
    if ';' in processed_line:
        code_part, comment_part = processed_line.split(';', 1)
        result["comment"] = comment_part.strip()
        processed_line = code_part.strip() # Yorumsuz kısmı tekrar işle
    
    if not processed_line: # Sadece yorum içeren satır
        return result

    # Satırı boşluklara göre bölelim.
    # Örnekler:
    # LABEL MNEM OPERAND
    #       MNEM OPERAND
    # LABEL MNEM
    #       MNEM
    # LABEL
    # LABEL EQU VALUE
    parts = processed_line.split(maxsplit=2) # En fazla 3 parçaya böl (etiket/komut, komut/operand, operand)
                                             # maxsplit=2 -> 3 parça döner
                                             # maxsplit=1 -> 2 parça döner
                                             # maxsplit=0 -> 1 parça döner (orijinal string listesi)

    first_word = parts[0].upper() # İlk kelimeyi büyük harfe çevir

    # 2. Etiket Kontrolü
    # M6800'de etiket satırın başında olmalı (boşluksuz).
    # Eğer ilk kelime geçerli bir etiket formatındaysa VE OPCODE_TABLE veya PSEUDO_OPS içinde DEĞİLSE,
    # o zaman etikettir.
    # Eğer satır sadece bir kelime içeriyorsa ve bu kelime bir komut değilse, etiket olabilir.
    
    # Önemli Not: Bir kelime hem geçerli bir etiket formatında hem de bir komut adı olabilir.
    # Örneğin, "BRA" hem bir komut hem de geçerli bir etikettir.
    # Bu durumda, satırın geri kalanına bakmak gerekir.
    # Klasik M6800 assembler'ları genellikle ilk kelimeyi etiket olarak alır eğer
    # satırın başında ise ve onu bir boşluk takip ediyorsa.
    # Veya, ilk kelime bir komut değilse, etiket kabul edilir.

    # Bizim yaklaşımımız:
    # Eğer satır girintili değilse (yani text_line.startswith(parts[0]))
    # ve parts[0] bir komut/pseudo-op değilse, o zaman etiket olabilir.
    if not text_line.startswith(" ") and \
       first_word not in OPCODE_TABLE and \
       first_word not in PSEUDO_OPS and \
       LABEL_REGEX.match(parts[0]): # parts[0] orijinal haliyle (büyük/küçük harf) etiket formatına uyuyor mu?
        result["label"] = parts[0] # Etiketi orijinal haliyle sakla, ama karşılaştırmalarda .upper() kullan
        if len(parts) > 1: # Etiketten sonra komut var
            result["mnemonic"] = parts[1].upper()
            if len(parts) > 2: # Komuttan sonra operand var
                result["operand_str"] = parts[2].strip() # Operandın başındaki/sonundaki boşlukları al
        # else: Sadece etiket var, mnemonic ve operand None kalacak (EQU için özel durum olabilir)

    elif first_word in OPCODE_TABLE or first_word in PSEUDO_OPS:
        # İlk kelime bir komut veya pseudo-op. Etiket yok.
        result["mnemonic"] = first_word # Zaten upper() yapılmıştı
        if len(parts) > 1: # Komuttan sonra operand var
            result["operand_str"] = parts[1].strip()
            if len(parts) > 2: # Operand birden fazla kelime olabilir (örn: FCC "HELLO WORLD")
                result["operand_str"] += " " + parts[2].strip() # Geri kalanını birleştir
        # else: Komut var ama operand yok (örn: NOP, INCA)
    
    else:
        # İlk kelime ne etiket (satır başında ve komut değil) ne de bilinen bir komut/pseudo-op.
        # Bu bir hata olabilir.
        # Veya sadece etiket içeren bir satır olabilir (örn: LOOP)
        # Bu durumu daha sonraki aşamalarda (Pass 1) daha iyi ele alabiliriz.
        # Şimdilik, eğer LABEL_REGEX ile eşleşiyorsa sadece etiket olarak alalım.
        if LABEL_REGEX.match(parts[0]) and len(parts) == 1:
            result["label"] = parts[0]
        elif parts: # parts boş değilse ama tanımsızsa
            result["error"] = f"Tanımsız ifade veya geçersiz komut: '{parts[0]}'"


    # Mnemonic'in geçerliliğini (eğer varsa) kontrol et.
    # Bu zaten yukarıdaki mantıkla büyük ölçüde yapıldı.
    # Ama yine de bir son kontrol:
    if result["mnemonic"] and \
       result["mnemonic"] not in OPCODE_TABLE and \
       result["mnemonic"] not in PSEUDO_OPS:
        result["error"] = f"Bilinmeyen komut veya pseudo-op: {result['mnemonic']}"
        result["mnemonic"] = None # Hatalıysa mnemonic'i temizle

    # Operand gerektiren komutlar için operand var mı kontrolü Pass1/Pass2'de daha detaylı yapılmalı.
    # Örneğin, LDAA komutu operand bekler. NOP beklemez.
    # Bu lexer aşamasında sadece yapısal ayrıştırma yapıyoruz.

    return result

if __name__ == '__main__':
    # Test için OPCODE_TABLE ve PSEUDO_OPS'ın bu scope'ta olması lazım
    # Ana script'ten çalıştırırken bu importlar zaten yukarıda olacak.
    # Eğer sadece bu dosyayı çalıştırıyorsanız, geçici olarak buraya ekleyebilirsiniz:
    # from m6800_opcodes import OPCODE_TABLE
    # PSEUDO_OPS = {"ORG", "EQU", "FCB", "FDB", "FCC", "END"}
    # LABEL_REGEX = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


    test_lines = [
        "START   LDAA #$10        ; Load A with 16", # Etiket, Komut, Operand, Yorum
        "        LDAB #$20        ; No label, Komut, Operand, Yorum",
        "LOOP    STAA $00,X       ; Store A indexed",
        "        DECA             ; No label, Komut (Inherent), Yorum",
        "        NOP",
        "        BNE  LOOP        ; Branch if Z=0",
        "        ORG  $FFFE       ; Pseudo-op",
        "RESET   FDB  START       ; Reset vector",
        "        END              ; Pseudo-op",
        "MYLABEL EQU $1000        ; EQU pseudo-op",
        "DATA    FCB  $0A,$0D,0   ; FCB with multiple operands",
        "STRING  FCC  \"HELLO\"     ; FCC with string",
        "STRING2 FCC  'WORLD!'    ; FCC with single quotes",
        "COMMENT ONLY ; This is just a comment",
        "",                       # Boş satır
        "MALFORMED LINE HERE",    # Hatalı satır (etiket değil, komut değil)
        "STILL   ; Sadece etiket ve yorum", # Bu aslında geçerli bir etiket tanımlaması
        "ANOTHER:",               # Hatalı etiket formatı (:)
        "BADCMD  $10",            # Bilinmeyen komut
        "LDAA",                   # Operand eksik (bu lexer'da hata vermez, parser'da verir)
        "START LDAA #$10,$20 ; fazla operand" # operand_str = "#$10,$20" olacak
    ]

    print("--- Lexer Test Sonuçları ---")
    for i, line_text in enumerate(test_lines):
        # OPCODE_TABLE'ın ana script'ten import edildiğini varsayıyoruz.
        # Eğer bu dosya bağımsız çalıştırılıyorsa, OPCODE_TABLE'ı bir şekilde sağlamanız gerekir.
        # Örneğin, `from assembler_core.m6800_opcodes import OPCODE_TABLE` satırını
        # ana script'inizden çalıştırdığınızda `assembler_core` paket olarak tanınır.
        # Eğer `lexer.py`'yi doğrudan `python lexer.py` olarak çalıştırıyorsanız,
        # Python `assembler_core` diye bir paket bulamayabilir.
        # Bu durumda, test için `OPCODE_TABLE`'ı doğrudan bu dosyaya kopyalayabilir
        # veya import yolunu `./m6800_opcodes.py` gibi göreceli yapabilirsiniz (eğer aynı dizindelerse).
        # Şimdilik, ana script'ten çağrıldığını varsayarak devam edelim.

        parsed = parse_line(i + 1, line_text)
        print(f"\nSatır {parsed['line_num']}: \"{parsed['original_line']}\"")
        print(f"  Etiket : {parsed['label']}")
        print(f"  Komut  : {parsed['mnemonic']}")
        print(f"  Operand: {parsed['operand_str']}")
        print(f"  Yorum  : {parsed['comment']}")
        if parsed['error']:
            print(f"  HATA   : {parsed['error']}")