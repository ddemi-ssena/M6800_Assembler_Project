# assembler_core/assembler.py
import re
import os
import sys

# --- Debug Printleri (Sorun çözüldükten sonra kaldırılabilir) ---
print(f"--- assembler.py Yükleniyor ---")
print(f"assembler.py: Mevcut Çalışma Dizini (os.getcwd()): {os.getcwd()}")
print(f"assembler.py: __name__ = {__name__}")
print(f"assembler.py: __file__ = {os.path.abspath(__file__)}")
print(f"assembler.py: __package__ = {__package__}")
print(f"assembler.py: sys.path = {sys.path}")
# --- Debug Printleri Sonu ---

# __package__ doluysa (yani bir paket içinden import edildiyse) göreceli import dene
if __package__: # __package__ None veya boş string değilse
    print(f"assembler.py: Paket '{__package__}' olarak algılandı. Göreceli importlar deneniyor (.lexer vb.)...")
    # TRY-EXCEPT'İ ŞİMDİLİK KALDIRALIM VEYA BASİTLEŞTİRELİM
    # try:
    from .lexer import parse_line, LABEL_REGEX
    from .m6800_opcodes import OPCODE_TABLE, ADDR_MODE_IMMEDIATE, ADDR_MODE_DIRECT, \
                               ADDR_MODE_EXTENDED, ADDR_MODE_INDEXED, ADDR_MODE_RELATIVE, \
                               ADDR_MODE_INHERENT, PSEUDO_OPS
    from .symbol_table import SymbolTable
    print("assembler.py: Göreceli importlar denendi (başarılı veya başarısız olacak).")
    # except ImportError as e_rel:
    #     print(f"assembler.py: Göreceli importlar (__package__='{__package__}') BAŞARISIZ: {e_rel}")
    #     # Acil durum bloğunu tamamen kaldırın veya yorumlayın
    #     raise # Orijinal hatayı görmek için
else:
    # Bu blok __main__ testi için kalabilir
    print("assembler.py: Paket bilgisi yok veya boş (__package__ is None/empty). Doğrudan (noktasız) importlar deneniyor (lexer vb.)...")
    from lexer import parse_line, LABEL_REGEX
    from m6800_opcodes import OPCODE_TABLE, ADDR_MODE_IMMEDIATE, ADDR_MODE_DIRECT, \
                               ADDR_MODE_EXTENDED, ADDR_MODE_INDEXED, ADDR_MODE_RELATIVE, \
                               ADDR_MODE_INHERENT, PSEUDO_OPS
    from symbol_table import SymbolTable
    print("assembler.py: Doğrudan (noktasız) importlar tamamlandı (başarılı veya başarısız olacak).")

# --- Sabitler ve Regex'ler ---
IMM_REGEX = re.compile(r"^#.*")
HEX_REGEX = re.compile(r"^\$[0-9A-Fa-f]+$")
BIN_REGEX = re.compile(r"^%[01]+$")
DEC_REGEX = re.compile(r"^[0-9]+$")
IND_REGEX = re.compile(r"^(.*?),\s*[Xx]$")

RELATIVE_MNEMONICS = {
    "BCC", "BCS", "BEQ", "BGE", "BGT", "BHI", "BLE", "BLS", "BLT",
    "BMI", "BNE", "BPL", "BRA", "BSR", "BVC", "BVS"
}

# --- Yardımcı Fonksiyonlar ---
def is_label_like(operand_str):
    if not operand_str:
        return False
    return not (IMM_REGEX.match(operand_str) or \
                HEX_REGEX.match(operand_str) or \
                BIN_REGEX.match(operand_str) or \
                DEC_REGEX.match(operand_str) or \
                IND_REGEX.match(operand_str)) and \
           LABEL_REGEX.match(operand_str)

def determine_addressing_mode_and_size(mnemonic, operand_str, symbol_table=None, current_lc_for_pass1=0):
    if mnemonic not in OPCODE_TABLE:
        return None, 0, f"Bilinmeyen komut: {mnemonic}"

    op_details_for_mnemonic = OPCODE_TABLE[mnemonic]

    if operand_str is None:
        if ADDR_MODE_INHERENT in op_details_for_mnemonic:
            return ADDR_MODE_INHERENT, int(op_details_for_mnemonic[ADDR_MODE_INHERENT][1]), None
        else:
            return None, 0, f"'{mnemonic}' komutu operandsız kullanılamaz."

    if IMM_REGEX.match(operand_str):
        if ADDR_MODE_IMMEDIATE in op_details_for_mnemonic:
            return ADDR_MODE_IMMEDIATE, int(op_details_for_mnemonic[ADDR_MODE_IMMEDIATE][1]), None
        else:
            return None, 0, f"'{mnemonic}' komutu Immediate adresleme modunu desteklemiyor: {operand_str}"

    indexed_match = IND_REGEX.match(operand_str)
    if indexed_match:
        if ADDR_MODE_INDEXED in op_details_for_mnemonic:
            return ADDR_MODE_INDEXED, int(op_details_for_mnemonic[ADDR_MODE_INDEXED][1]), None
        else:
            return None, 0, f"'{mnemonic}' komutu Indexed adresleme modunu desteklemiyor: {operand_str}"

    if mnemonic in RELATIVE_MNEMONICS:
        if ADDR_MODE_RELATIVE in op_details_for_mnemonic:
            return ADDR_MODE_RELATIVE, int(op_details_for_mnemonic[ADDR_MODE_RELATIVE][1]), None
        else:
            return None, 0, f"'{mnemonic}' için Relative adresleme tanımı bulunamadı."

    if HEX_REGEX.match(operand_str):
        hex_val_str = operand_str[1:]
        try:
            value = int(hex_val_str, 16)
            if ADDR_MODE_DIRECT in op_details_for_mnemonic and 0 <= value <= 0xFF:
                return ADDR_MODE_DIRECT, int(op_details_for_mnemonic[ADDR_MODE_DIRECT][1]), None
            elif ADDR_MODE_EXTENDED in op_details_for_mnemonic and 0 <= value <= 0xFFFF:
                return ADDR_MODE_EXTENDED, int(op_details_for_mnemonic[ADDR_MODE_EXTENDED][1]), None
        except ValueError:
            pass 

    is_potentially_label = is_label_like(operand_str)
    if is_potentially_label:
        if ADDR_MODE_EXTENDED in op_details_for_mnemonic:
            return ADDR_MODE_EXTENDED, int(op_details_for_mnemonic[ADDR_MODE_EXTENDED][1]), None
        elif ADDR_MODE_DIRECT in op_details_for_mnemonic:
            return ADDR_MODE_DIRECT, int(op_details_for_mnemonic[ADDR_MODE_DIRECT][1]), None

    elif DEC_REGEX.match(operand_str):
        try:
            value = int(operand_str)
            if ADDR_MODE_DIRECT in op_details_for_mnemonic and 0 <= value <= 0xFF:
                return ADDR_MODE_DIRECT, int(op_details_for_mnemonic[ADDR_MODE_DIRECT][1]), None
            elif ADDR_MODE_EXTENDED in op_details_for_mnemonic and 0 <= value <= 0xFFFF:
                return ADDR_MODE_EXTENDED, int(op_details_for_mnemonic[ADDR_MODE_EXTENDED][1]), None
        except ValueError:
            pass

    if ADDR_MODE_EXTENDED in op_details_for_mnemonic: # Fallback to Extended for unresolved labels in Pass 1
        return ADDR_MODE_EXTENDED, int(op_details_for_mnemonic[ADDR_MODE_EXTENDED][1]), None
    elif ADDR_MODE_DIRECT in op_details_for_mnemonic: # Fallback to Direct if Extended not available
        return ADDR_MODE_DIRECT, int(op_details_for_mnemonic[ADDR_MODE_DIRECT][1]), None
        
    return None, 0, f"'{mnemonic}' için operand '{operand_str}' ile uygun adresleme modu bulunamadı veya desteklenmiyor."

def parse_operand_for_equ(operand_str, symbol_table, line_num):
    if operand_str is None:
        return None, f"Satır {line_num}: EQU/ORG için operand eksik."
    
    operand_str = operand_str.strip()

    if HEX_REGEX.match(operand_str):
        return int(operand_str[1:], 16), None
    elif BIN_REGEX.match(operand_str):
        return int(operand_str[1:], 2), None
    elif DEC_REGEX.match(operand_str):
        return int(operand_str), None
    elif is_label_like(operand_str): 
        if symbol_table:
            value = symbol_table.get_symbol_value(operand_str.upper()) # Etiketler büyük harfle aranır
            if value is not None:
                return value, None
            else:
                return None, f"Satır {line_num}: EQU/ORG için tanımsız etiket referansı: {operand_str}"
        else: 
             return None, f"Satır {line_num}: EQU/ORG etiketi için sembol tablosu eksik: {operand_str}"
    else:
        return None, f"Satır {line_num}: EQU/ORG için geçersiz değer: {operand_str}"

# assembler_core/assembler.py
# ... (dosyanın başındaki importlar ve diğer fonksiyonlar aynı kalacak) ...

# --- Birinci Geçiş (Pass 1) ---
def pass_one(source_lines):
    symbol_table = SymbolTable()
    processed_lines_data = []
    errors = []
    location_counter = 0

    # PSEUDO_OPS'a RMB'yi ekleyelim ki lexer'da mnemonic olarak tanınsın
    # Eğer PSEUDO_OPS m6800_opcodes.py'de tanımlıysa ve oradan import ediliyorsa
    # oraya eklemek daha doğru olur. Şimdilik burada kontrol edelim.
    # Veya PSEUDO_OPS = {"ORG", "EQU", "FCB", "FDB", "FCC", "END", "RMB"} şeklinde
    # m6800_opcodes.py içinde güncellenmeli.
    # Bu örnekte, PSEUDO_OPS'ın zaten RMB'yi içerdiğini varsayıyorum
    # (ya da lexer'ın mnemonic olarak tanıdığını).

    for i, line_text in enumerate(source_lines):
        parsed_line_info = parse_line(i + 1, line_text)

        if parsed_line_info["error"]:
            errors.append(f"Satır {parsed_line_info['line_num']} (Lexer): {parsed_line_info['error']}")
            processed_lines_data.append({
                **parsed_line_info, "address": location_counter, "size": 0, "addressing_mode": None
            })
            continue

        if not parsed_line_info["label"] and not parsed_line_info["mnemonic"]:
            processed_lines_data.append({
                **parsed_line_info, "address": location_counter, "size": 0, "addressing_mode": None
            })
            continue

        current_line_data = {
            **parsed_line_info, "address": location_counter, "size": 0, "addressing_mode": None,
        }

        if current_line_data["label"]:
            # RMB için etiket ataması RMB bloğunda yapılacak, EQU için ise EQU bloğunda.
            # Diğer durumlarda etiketi mevcut location_counter ile ekle.
            if not (current_line_data["mnemonic"] and current_line_data["mnemonic"].upper() in ["EQU", "RMB"]):
                try:
                    symbol_table.add_symbol(current_line_data["label"].upper(), location_counter, current_line_data["line_num"])
                except ValueError as e:
                    err_msg = str(e); errors.append(err_msg); current_line_data["error"] = err_msg

        if current_line_data["mnemonic"]:
            mnemonic_upper = current_line_data["mnemonic"].upper()

            if mnemonic_upper == "ORG":
                if current_line_data["operand_str"]:
                    try:
                        val, err = parse_operand_for_equ(current_line_data["operand_str"], symbol_table, current_line_data["line_num"])
                        if err: raise ValueError(err)
                        location_counter = val
                        current_line_data["address"] = location_counter # Adresi güncelle
                    except ValueError as e:
                        err_msg = f"Satır {current_line_data['line_num']}: ORG - {e}"
                        errors.append(err_msg); current_line_data["error"] = err_msg
                else:
                    err_msg = f"Satır {current_line_data['line_num']}: ORG için operand eksik."
                    errors.append(err_msg); current_line_data["error"] = err_msg
                current_line_data["size"] = 0

            elif mnemonic_upper == "EQU":
                if not current_line_data["label"]:
                    err_msg = f"Satır {current_line_data['line_num']}: EQU için etiket eksik."
                    errors.append(err_msg); current_line_data["error"] = err_msg
                elif not current_line_data["operand_str"]:
                    err_msg = f"Satır {current_line_data['line_num']}: EQU için değer eksik."
                    errors.append(err_msg); current_line_data["error"] = err_msg
                else:
                    try:
                        value, err_equ = parse_operand_for_equ(current_line_data["operand_str"], symbol_table, current_line_data["line_num"])
                        if err_equ: raise ValueError(err_equ)
                        # EQU etiketi, location_counter'ı değil, hesaplanan değeri alır.
                        symbol_table.add_symbol(current_line_data["label"].upper(), value, current_line_data["line_num"])
                        current_line_data["address"] = None # EQU'nun adresi yoktur, değeri vardır.
                    except ValueError as e:
                        err_msg = str(e); errors.append(err_msg); current_line_data["error"] = err_msg
                current_line_data["size"] = 0

            # RMB İÇİN YENİ EKlenen BLOK BAŞLANGICI
            elif mnemonic_upper == "RMB":
                if current_line_data["label"]: # RMB satırında etiket varsa
                    try:
                        symbol_table.add_symbol(current_line_data["label"].upper(), location_counter, current_line_data["line_num"])
                    except ValueError as e:
                        err_msg = str(e); errors.append(err_msg); current_line_data["error"] = err_msg

                if current_line_data["operand_str"]:
                    try:
                        # RMB'nin operandı bir sayı olmalı (kaç byte ayrılacağı)
                        # parse_operand_for_equ basit sayıları ve etiketleri çözebilir
                        num_bytes_to_reserve, err_rmb = parse_operand_for_equ(current_line_data["operand_str"], symbol_table, current_line_data["line_num"])
                        if err_rmb: raise ValueError(err_rmb)
                        if not isinstance(num_bytes_to_reserve, int) or num_bytes_to_reserve < 0:
                            raise ValueError(f"RMB için geçersiz byte sayısı: {current_line_data['operand_str']}")

                        current_line_data["size"] = num_bytes_to_reserve # Ayrılan byte sayısı
                        # location_counter bu bloğun sonunda artırılacak
                    except ValueError as e:
                        err_msg = f"Satır {current_line_data['line_num']}: RMB - {e}"
                        errors.append(err_msg); current_line_data["error"] = err_msg
                        current_line_data["size"] = 0 # Hata durumunda boyut 0
                else:
                    err_msg = f"Satır {current_line_data['line_num']}: RMB için operand (ayrılacak byte sayısı) eksik."
                    errors.append(err_msg); current_line_data["error"] = err_msg
                    current_line_data["size"] = 0
                # RMB için makine kodu üretilmez, bu yüzden addressing_mode None kalır
            # RMB İÇİN YENİ EKlenen BLOK SONU

            elif mnemonic_upper == "END":
                current_line_data["size"] = 0
                processed_lines_data.append(current_line_data)
                break

            elif mnemonic_upper == "FCB":
                if current_line_data["operand_str"]:
                    try:
                        byte_value_strs = [s.strip() for s in current_line_data["operand_str"].split(',')]
                        current_line_data["size"] = len(byte_value_strs)
                        for val_str in byte_value_strs:
                            # FCB'nin operandları Pass1'de etiket olabilir, bu yüzden sembol tablosuyla çözmeye çalış
                            val, err_parse = parse_operand_for_equ(val_str, symbol_table, current_line_data["line_num"])
                            if err_parse and not is_label_like(val_str): # Eğer etiket değilse ve parse hatası varsa
                                 raise ValueError(f"FCB için geçersiz byte değeri: {val_str} ({err_parse})")
                            # Değer aralığı kontrolü Pass2'de yapılabilir veya burada da temel bir kontrol yapılabilir
                    except ValueError as e:
                        err_msg = f"Satır {current_line_data['line_num']}: {e}"; errors.append(err_msg)
                        current_line_data["error"] = err_msg; current_line_data["size"] = 0
                else:
                    err_msg = f"Satır {current_line_data['line_num']}: FCB için operand eksik."
                    errors.append(err_msg); current_line_data["error"] = err_msg

            elif mnemonic_upper == "FDB":
                if current_line_data["operand_str"]:
                    try:
                        word_value_strs = [s.strip() for s in current_line_data["operand_str"].split(',')]
                        current_line_data["size"] = len(word_value_strs) * 2
                        for val_str in word_value_strs:
                            val, err_parse = parse_operand_for_equ(val_str, symbol_table, current_line_data["line_num"])
                            if err_parse and not is_label_like(val_str):
                                 raise ValueError(f"FDB için geçersiz word değeri: {val_str} ({err_parse})")
                    except ValueError as e:
                        err_msg = f"Satır {current_line_data['line_num']}: {e}"; errors.append(err_msg)
                        current_line_data["error"] = err_msg; current_line_data["size"] = 0
                else:
                    err_msg = f"Satır {current_line_data['line_num']}: FDB için operand eksik."
                    errors.append(err_msg); current_line_data["error"] = err_msg

            elif mnemonic_upper == "FCC":
                op_str = current_line_data["operand_str"]
                if op_str and len(op_str) >= 2 and \
                   ((op_str.startswith('"') and op_str.endswith('"')) or \
                    (op_str.startswith("'") and op_str.endswith("'"))):
                    current_line_data["size"] = len(op_str) - 2
                else:
                    err_msg = f"Satır {current_line_data['line_num']}: FCC için geçersiz string formatı: {op_str}"
                    errors.append(err_msg); current_line_data["error"] = err_msg; current_line_data["size"] = 0

            else: # Diğer tüm komutlar (opcode'lar)
                mode, size, err_addr = determine_addressing_mode_and_size(
                    mnemonic_upper, current_line_data["operand_str"], symbol_table, location_counter
                )
                if err_addr:
                    err_msg = f"Satır {current_line_data['line_num']}: {err_addr}"; errors.append(err_msg)
                    current_line_data["error"] = err_msg
                else:
                    current_line_data["size"] = size
                    current_line_data["addressing_mode"] = mode

        elif current_line_data["label"] and not current_line_data["mnemonic"]:
            # Sadece etiket içeren bir satır (örn: LOOP_END)
            # Bu durumda etiket zaten yukarıda (if current_line_data["label"] bloğunda)
            # mevcut location_counter ile eklenmiş olmalı.
            # Boyutu 0'dır.
            current_line_data["size"] = 0

        # Hata yoksa ve işlenen satır ORG, EQU, END değilse location_counter'ı artır
        if not current_line_data.get("error"):
            mne_for_lc = current_line_data["mnemonic"].upper() if current_line_data["mnemonic"] else ""
            if mne_for_lc not in ["EQU", "ORG", "END"]: # RMB de LC'yi artırır
                 location_counter += current_line_data["size"]

        processed_lines_data.append(current_line_data)

    return symbol_table, processed_lines_data, errors

# --- İkinci Geçiş (Pass 2) için Yardımcı Fonksiyon ---
def parse_operand_value_for_pass2(operand_str, symbol_table, line_num, current_address_plus_size_for_relative=0):
    if operand_str is None:
        return 0, None

    operand_str = operand_str.strip()

    # Basit ifade ayrıştırma (ETİKET+SAYI veya ETİKET-SAYI)
    # Daha karmaşık ifadeler için daha gelişmiş bir parser gerekebilir.
    match_plus = re.fullmatch(r"([a-zA-Z_][a-zA-Z0-9_]*)\s*\+\s*([0-9]+|\$[0-9A-Fa-f]+|%[01]+)", operand_str, re.IGNORECASE)
    match_minus = re.fullmatch(r"([a-zA-Z_][a-zA-Z0-9_]*)\s*-\s*([0-9]+|\$[0-9A-Fa-f]+|%[01]+)", operand_str, re.IGNORECASE)

    if match_plus:
        label_name = match_plus.group(1)
        offset_str = match_plus.group(2)
        label_value = symbol_table.get_symbol_value(label_name.upper())
        if label_value is None:
            return None, f"Satır {line_num}: İfadede tanımsız etiket: {label_name}"

        offset_value, err_offset = parse_operand_value_for_pass2(offset_str, symbol_table, line_num) # offset_str zaten basit bir sayı olmalı
        if err_offset:
            return None, f"Satır {line_num}: İfadede geçersiz offset: {offset_str} ({err_offset})"
        return label_value + offset_value, None
    elif match_minus:
        label_name = match_minus.group(1)
        offset_str = match_minus.group(2)
        label_value = symbol_table.get_symbol_value(label_name.upper())
        if label_value is None:
            return None, f"Satır {line_num}: İfadede tanımsız etiket: {label_name}"

        offset_value, err_offset = parse_operand_value_for_pass2(offset_str, symbol_table, line_num)
        if err_offset:
            return None, f"Satır {line_num}: İfadede geçersiz offset: {offset_str} ({err_offset})"
        return label_value - offset_value, None


    if IMM_REGEX.match(operand_str):
        val_str = operand_str[1:]
        return parse_operand_value_for_pass2(val_str, symbol_table, line_num) # Rekürsif çağrı # olmadan

    indexed_match = IND_REGEX.match(operand_str)
    if indexed_match:
        offset_str = indexed_match.group(1).strip()
        if not offset_str: # Sadece ,X veya ,x ise offset 0'dır
            return 0, None
        return parse_operand_value_for_pass2(offset_str, symbol_table, line_num)

    if HEX_REGEX.match(operand_str):
        try: return int(operand_str[1:], 16), None
        except ValueError: return None, f"Satır {line_num}: Geçersiz hex değer: {operand_str}"

    if BIN_REGEX.match(operand_str):
        try: return int(operand_str[1:], 2), None
        except ValueError: return None, f"Satır {line_num}: Geçersiz binary değer: {operand_str}"

    if is_label_like(operand_str): # Bu artık sadece tek bir etiket için çalışır
        value = symbol_table.get_symbol_value(operand_str.upper())
        if value is not None: return value, None
        else: return None, f"Satır {line_num}: Tanımsız etiket: {operand_str}"

    if DEC_REGEX.match(operand_str):
        try: return int(operand_str), None
        except ValueError: return None, f"Satır {line_num}: Geçersiz decimal değer: {operand_str}"

    return None, f"Satır {line_num}: Operand ayrıştırılamadı: {operand_str}"


# --- İkinci Geçiş (Pass 2) ---
# pass_two fonksiyonunda RMB için özel bir işlem yapmaya gerek yok,
# çünkü RMB makine kodu üretmez. Listelemede doğru görünmesi yeterlidir.
# Sadece VAR_A+1 gibi ifadelerin parse_operand_value_for_pass2 tarafından
# doğru çözüldüğünden emin olun.

# ... (pass_two ve __main__ bloğu aynı kalabilir) ...

# --- İkinci Geçiş (Pass 2) ---
def pass_two(processed_lines_pass1, symbol_table):
    listing_output = []
    machine_code_segments = [] 
    current_segment_address = -1
    current_segment_bytes = []
    errors_pass2 = []

    for line_data_p1 in processed_lines_pass1:
        current_listing_entry = {
            "line_num": line_data_p1["line_num"],
            "address_hex": f"${line_data_p1['address']:04X}" if line_data_p1['address'] is not None else "----",
            "machine_code_hex": "", 
            "label": line_data_p1["label"], "mnemonic": line_data_p1["mnemonic"],
            "operand_str": line_data_p1["operand_str"], "original_line": line_data_p1["original_line"],
            "comment": line_data_p1["comment"], "error": line_data_p1.get("error")
        }

        if current_listing_entry["error"]:
            listing_output.append(current_listing_entry)
            continue

        if current_segment_address != -1 and line_data_p1["address"] != current_segment_address:
            if current_segment_bytes:
                machine_code_segments.append((current_segment_address, current_segment_bytes))
            current_segment_bytes = []
        current_segment_address = line_data_p1["address"]
        
        generated_bytes_for_line = []

        if line_data_p1["mnemonic"]:
            mnemonic_upper = line_data_p1["mnemonic"].upper()
            operand_str_p1 = line_data_p1["operand_str"]
            addressing_mode_p1 = line_data_p1.get("addressing_mode")

            if mnemonic_upper in ["ORG", "EQU", "END", "RMB"]: # RMB EKLENDİ
                pass 
            elif mnemonic_upper == "FCB":
                if operand_str_p1:
                    byte_strs = [s.strip() for s in operand_str_p1.split(',')]
                    for b_str in byte_strs:
                        val, err = parse_operand_value_for_pass2(b_str, symbol_table, line_data_p1["line_num"])
                        if err: current_listing_entry["error"] = err; errors_pass2.append(err); generated_bytes_for_line.clear(); break
                        if not (0 <= val <= 255):
                            err = f"Satır {line_data_p1['line_num']}: FCB değeri (${val:02X}) 8-bit aralığı dışında."
                            current_listing_entry["error"] = err; errors_pass2.append(err); generated_bytes_for_line.clear(); break
                        generated_bytes_for_line.append(val & 0xFF)
                elif not current_listing_entry["error"]: 
                    err = f"Satır {line_data_p1['line_num']}: FCB için operand eksik (P2)."
                    current_listing_entry["error"] = err; errors_pass2.append(err)
            
            elif mnemonic_upper == "FDB":
                if operand_str_p1:
                    word_strs = [s.strip() for s in operand_str_p1.split(',')]
                    for w_str in word_strs:
                        val, err = parse_operand_value_for_pass2(w_str, symbol_table, line_data_p1["line_num"])
                        if err: current_listing_entry["error"] = err; errors_pass2.append(err); generated_bytes_for_line.clear(); break
                        if not (0 <= val <= 65535):
                            err = f"Satır {line_data_p1['line_num']}: FDB değeri (${val:04X}) 16-bit aralığı dışında."
                            current_listing_entry["error"] = err; errors_pass2.append(err); generated_bytes_for_line.clear(); break
                        generated_bytes_for_line.append((val >> 8) & 0xFF) 
                        generated_bytes_for_line.append(val & 0xFF)
                elif not current_listing_entry["error"]:
                    err = f"Satır {line_data_p1['line_num']}: FDB için operand eksik (P2)."
                    current_listing_entry["error"] = err; errors_pass2.append(err)

            elif mnemonic_upper == "FCC":
                if operand_str_p1 and not current_listing_entry["error"]:
                    text_content = operand_str_p1[1:-1] 
                    for char_code in [ord(c) for c in text_content]:
                        if not (0 <= char_code <= 255):
                           err = f"Satır {line_data_p1['line_num']}: FCC için geçersiz karakter kodu: {char_code}"
                           current_listing_entry["error"] = err; errors_pass2.append(err); break
                        generated_bytes_for_line.append(char_code)
                elif not current_listing_entry["error"]:
                    err = f"Satır {line_data_p1['line_num']}: FCC için geçersiz operand (P2)."
                    current_listing_entry["error"] = err; errors_pass2.append(err)

            else: 
                if mnemonic_upper not in OPCODE_TABLE: 
                    if not current_listing_entry["error"]:
                        err = f"Satır {line_data_p1['line_num']}: Bilinmeyen komut (P2): {mnemonic_upper}"
                        current_listing_entry["error"] = err; errors_pass2.append(err)
                elif not addressing_mode_p1: 
                    if not current_listing_entry["error"]:
                        err = f"Satır {line_data_p1['line_num']}: '{mnemonic_upper}' için adresleme modu P1'de belirlenemedi."
                        current_listing_entry["error"] = err; errors_pass2.append(err)
                else:
                    op_hex, num_bytes_str, _ = OPCODE_TABLE[mnemonic_upper][addressing_mode_p1]
                    num_bytes = int(num_bytes_str)
                    generated_bytes_for_line.append(int(op_hex, 16))

                    operand_value = 0
                    if num_bytes > 1:
                        next_instr_addr_for_rel = line_data_p1["address"] + num_bytes
                        val, err_op = parse_operand_value_for_pass2(
                            operand_str_p1, symbol_table, line_data_p1["line_num"], next_instr_addr_for_rel
                        )
                        if err_op: current_listing_entry["error"] = err_op; errors_pass2.append(err_op)
                        else: operand_value = val

                    if not current_listing_entry["error"]:
                        if addressing_mode_p1 == ADDR_MODE_IMMEDIATE:
                            if num_bytes == 2: 
                                if not (0 <= operand_value <= 255): err = f"Satır {line_data_p1['line_num']}: Immediate değer ({operand_value}) 8-bit aralığı dışında."; current_listing_entry["error"] = err; errors_pass2.append(err)
                                else: generated_bytes_for_line.append(operand_value & 0xFF)
                            elif num_bytes == 3: 
                                if not (0 <= operand_value <= 65535): err = f"Satır {line_data_p1['line_num']}: Immediate değer ({operand_value}) 16-bit aralığı dışında."; current_listing_entry["error"] = err; errors_pass2.append(err)
                                else: generated_bytes_for_line.append((operand_value >> 8) & 0xFF); generated_bytes_for_line.append(operand_value & 0xFF)
                        
                        elif addressing_mode_p1 == ADDR_MODE_DIRECT:
                            if not (0 <= operand_value <= 255): err = f"Satır {line_data_p1['line_num']}: Direct adres ({operand_value}) 8-bit aralığı dışında."; current_listing_entry["error"] = err; errors_pass2.append(err)
                            else: generated_bytes_for_line.append(operand_value & 0xFF)

                        elif addressing_mode_p1 == ADDR_MODE_INDEXED:
                            if not (0 <= operand_value <= 255): err = f"Satır {line_data_p1['line_num']}: Indexed offset ({operand_value}) 8-bit aralığı dışında."; current_listing_entry["error"] = err; errors_pass2.append(err)
                            else: generated_bytes_for_line.append(operand_value & 0xFF)

                        elif addressing_mode_p1 == ADDR_MODE_EXTENDED:
                            if not (0 <= operand_value <= 65535): err = f"Satır {line_data_p1['line_num']}: Extended adres ({operand_value}) 16-bit aralığı dışında."; current_listing_entry["error"] = err; errors_pass2.append(err)
                            else: generated_bytes_for_line.append((operand_value >> 8) & 0xFF); generated_bytes_for_line.append(operand_value & 0xFF)

                        elif addressing_mode_p1 == ADDR_MODE_RELATIVE:
                            target_address = operand_value
                            pc_after_branch_instruction = line_data_p1["address"] + num_bytes
                            offset = target_address - pc_after_branch_instruction
                            if not (-128 <= offset <= 127):
                                err = f"Satır {line_data_p1['line_num']}: Relative offset ({offset}) menzil dışı (-128 ila +127)."
                                current_listing_entry["error"] = err; errors_pass2.append(err)
                            else: generated_bytes_for_line.append(offset & 0xFF)
        
        if not current_listing_entry["error"] and generated_bytes_for_line:
            current_listing_entry["machine_code_hex"] = "".join([f"{b:02X}" for b in generated_bytes_for_line])
            current_segment_bytes.extend(generated_bytes_for_line)
        
        listing_output.append(current_listing_entry)

    if current_segment_bytes and current_segment_address != -1 :
        machine_code_segments.append((current_segment_address, current_segment_bytes))
    
    return listing_output, machine_code_segments, list(set(errors_pass2)) # Hataları benzersiz yap


# assembler_core/assembler.py
# ... (dosyanın başındaki importlar ve fonksiyon tanımları aynı kalacak) ...

# --- Ana Test Bloğu ---
if __name__ == '__main__':
    # --- Test Dosyası Seçimi ---
    # Aşağıdaki satırı test etmek istediğiniz dosya ile değiştirin.
    # test_file_name = "inherent_ops.asm"
    #test_file_name = "direct_extended_ops.asm" # << SADECE BURAYI DEĞİŞTİRİN
    # test_file_name = "error_handling.asm"
    test_file_name = "complex_example.asm"
    # test_file_name = None # Eğer aşağıdaki gömülü testi çalıştırmak isterseniz

    if test_file_name: # Eğer bir dosya adı belirtilmişse, o dosyayı test et
        print(f"\n\n--- ASSEMBLER TESTİ ({test_file_name}) ---")
        
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            # Proje kök dizinini bulmak için script_dir'in bir üst dizinine çıkıyoruz
            # Bu, assembler.py'nin assembler_core içinde olduğunu varsayar.
            project_root = os.path.dirname(script_dir) 
            current_test_file_path = os.path.join(project_root, "tests", test_file_name)
            
            print(f"Test dosyası yükleniyor: {current_test_file_path}")
            if not os.path.exists(current_test_file_path):
                # Eğer script_dir proje kökü ise (nadir bir durum, ama olabilir)
                current_test_file_path_alt = os.path.join("tests", test_file_name)
                if os.path.exists(current_test_file_path_alt):
                    current_test_file_path = current_test_file_path_alt
                else: # Alternatif yol (eğer CWD zaten assembler_core ise ve dosya bir üstteki tests klasöründe)
                    current_test_file_path_alt_2 = os.path.join("..", "tests", test_file_name)
                    if os.path.exists(current_test_file_path_alt_2):
                         current_test_file_path = current_test_file_path_alt_2
                    else:
                        raise FileNotFoundError(f"Test dosyası bulunamadı: {current_test_file_path}, {current_test_file_path_alt} veya {current_test_file_path_alt_2}")


            with open(current_test_file_path, 'r', encoding='utf-8') as f:
                source_lines_current_test = f.read().strip().split('\n')
            print(f"{current_test_file_path} dosyasından {len(source_lines_current_test)} satır başarıyla yüklendi.")

        except FileNotFoundError as e:
            print(f"HATA: Test dosyası yüklenemedi. {e}")
            print(f"Mevcut Çalışma Dizini (CWD): {os.getcwd()}")
            print(f"Script Dizini: {script_dir}")
            print(f"Proje Kökü (Tahmini): {project_root}")
            print("Lütfen dosya yolunu kontrol edin veya `assembler.py` içindeki `test_file_name` için doğru yolu sağlayın.")
            source_lines_current_test = [] 

        if source_lines_current_test:
            print(f"\n--- PASS 1 ({test_file_name}) ---")
            sym_table_test, proc_lines_p1_test, errs_p1_test = pass_one(source_lines_current_test)

            print(f"\nSembol Tablosu (Pass 1 sonrası, {test_file_name}):")
            print(sym_table_test)
            
            if errs_p1_test:
                print(f"\nPass 1 Hataları ({test_file_name}):")
                for err_idx, err in enumerate(errs_p1_test): print(f"  P1 Hata {err_idx+1}: {err}")
            else:
                print(f"\nPass 1'de hata bulunamadı ({test_file_name}).")

            print(f"\n--- PASS 2 ({test_file_name}) ---")
            final_listing_test, mc_segments_test, errs_p2_combined_test = pass_two(proc_lines_p1_test, sym_table_test)
            
            pass1_error_messages_set_test = set(errs_p1_test)
            # Sadece Pass 2'de ortaya çıkan veya Pass 1'dekinden farklı olan hataları bul
            errs_p2_only_test = []
            for p2_err in errs_p2_combined_test:
                is_from_pass1_or_similar = False
                for p1_err in pass1_error_messages_set_test:
                    # Basit bir karşılaştırma, daha sofistike olabilir
                    if p2_err == p1_err or p2_err in p1_err or p1_err in p2_err:
                        is_from_pass1_or_similar = True
                        break
                if not is_from_pass1_or_similar:
                    errs_p2_only_test.append(p2_err)


            print(f"\nSon Listeleme (Pass 2 Sonucu, {test_file_name}):")
            pass1_error_lines_test = {int(e.split(":")[0].split(" ")[1]) for e in errs_p1_test if "Satır" in e and e.split(":")[0].split(" ")[1].isdigit()}

            for entry in final_listing_test:
                mc_hex_display = entry['machine_code_hex'] if entry['machine_code_hex'] else "    "
                line_num_str = f"L:{entry['line_num']:<2}"
                addr_hex_str = f"Adr: {entry['address_hex']}"
                code_str = f"Kod: {mc_hex_display:<8}" # Genişletilmiş makine kodu alanı
                
                label_str = entry['label'] if entry['label'] else ""
                mnemonic_str = entry['mnemonic'] if entry['mnemonic'] else ""
                operand_str = entry['operand_str'] if entry['operand_str'] else ""
                comment_str = f"; {entry['comment']}" if entry['comment'] else ""
                
                print(f"{line_num_str} {addr_hex_str}  {code_str}  {label_str:<8} {mnemonic_str:<5} {operand_str:<15} {comment_str}")

                if entry['error']:
                    # Hatanın Pass 1'de zaten raporlanıp raporlanmadığını kontrol et
                    is_pass1_error_reported = False
                    for p1_err in errs_p1_test:
                        # Hata mesajlarının içeriğini daha esnek karşılaştır
                        if f"Satır {entry['line_num']}" in p1_err and entry['error'] in p1_err:
                            is_pass1_error_reported = True
                            break
                    if not is_pass1_error_reported:
                        print(f"    HATA (P2): {entry['error']}")


            if errs_p2_only_test: # Sadece Pass 2'ye özgü yeni hatalar varsa listele
                print(f"\nPass 2'de Oluşan Farklı Hatalar ({test_file_name}):")
                for err_idx, err in enumerate(errs_p2_only_test): 
                    print(f"  P2 Farklı Hata {err_idx+1}: {err}")
            elif errs_p1_test and not errs_p2_only_test : 
                 print("\n(Pass 2'de Pass 1 hataları dışında yeni hata bulunamadı.)")
            elif not errs_p1_test and not errs_p2_only_test:
                 print(f"\nPass 2'de ek hata bulunamadı ({test_file_name}).")
            # else: Pass 1'de hata yoktu ama Pass 2'de hata oluştu durumu yukarıda ele alındı.
                    
            print(f"\nMakine Kodu Segmentleri ({test_file_name}):")
            if mc_segments_test:
                for addr, byte_codes in mc_segments_test:
                    hex_codes = " ".join([f"{b:02X}" for b in byte_codes])
                    print(f"  Segment @ ${addr:04X}: {hex_codes}")
            else:
                print("  (Makine kodu segmenti üretilmedi veya hatalar nedeniyle boş.)")
        # Dosya bulunamadı veya boşsa buraya gelinir
        elif not source_lines_current_test and test_file_name : # Sadece dosya adı varsa ama yüklenemediyse
             print(f"'{test_file_name}' için test çalıştırılamadı (dosya yükleme hatası veya boş dosya).")

    else: # test_file_name None ise veya boş string ise, gömülü testi çalıştır
        print("\n\n--- GÖMÜLÜ TAM ASSEMBLER TESTİ (PASS 1 + PASS 2) ---")
        test_asm_code_full = """
START   LDAA    #$10        ; Load A with 16
        LDAB    #VAL1       ; VAL1 EQU ile tanımlı olacak
LOOP    ADDA    #1
        STAA    COUNTER     ; COUNTER ileri referans
        DECB
        BNE     LOOP
        SWI
VAL1    EQU     $20         ; VAL1 tanımı
COUNTER FCB     $00, $FF, 01 ; Test FCB
        ORG     $1000
RESET   FDB     START,LOOP, $ABCD  ; Reset Vector
DATA    FCC     "HI!"
        FCC     'Test'
NO_OP   EQU     $F0F0
        LDAA    NO_OP       ; EQU ile tanımlı etiketi kullan (Extended)
        LDAA    $50         ; Direct adresleme
        LDAA    $0500       ; Extended adresleme
        LDX     #$C0DE     ; 16-bit immediate
        LDAA    0,X         ; Indexed
        STAA    10,X
        BRA     EXITPLACE   ; İleri referanslı BRA
        FCB     $AA
EXITPLACE NOP
ADDR1   EQU     $0030
        LDAA    ADDR1       ; Direct (çünkü ADDR1 < 256)
        ORG     $2000
BADFCC  FCC     NOQUOTE     ; Hatalı FCC
BADFCB  FCB     $1000       ; Aralık dışı FCB
        FCB     UNKN_LBL    ; Tanımsız etiket hatası (Pass 2'de)
        END
FINAL   LDAA    #0          ; END'den sonra bu işlenmemeli
"""
        source_lines_full = test_asm_code_full.strip().split('\n')
        
        print("--- PASS 1 (Gömülü Test) ---")
        sym_table, proc_lines_p1, errs_p1 = pass_one(source_lines_full)

        print("\nSembol Tablosu (Pass 1 sonrası, Gömülü Test):")
        print(sym_table)
        
        if errs_p1:
            print("\nPass 1 Hataları (Gömülü Test):")
            for err_idx, err in enumerate(errs_p1): print(f"  P1 Hata {err_idx+1}: {err}")
        else:
            print("\nPass 1'de hata bulunamadı (Gömülü Test).")

        print("\n--- PASS 2 (Gömülü Test) ---")
        final_listing, mc_segments, errs_p2_combined_full = pass_two(proc_lines_p1, sym_table)

        pass1_error_messages_set_full = set(errs_p1)
        errs_p2_only_full = []
        for p2_err in errs_p2_combined_full:
            is_from_pass1_or_similar = False
            for p1_err in pass1_error_messages_set_full:
                if p2_err == p1_err or p2_err in p1_err or p1_err in p2_err:
                    is_from_pass1_or_similar = True
                    break
            if not is_from_pass1_or_similar:
                errs_p2_only_full.append(p2_err)
        

        print("\nSon Listeleme (Pass 2 Sonucu, Gömülü Test):")
        # ... (Gömülü test için listeleme yazdırma kodunuzu buraya kopyalayın,
        #      final_listing, errs_p1, errs_p2_only_full gibi değişkenleri kullanarak) ...
        pass1_error_lines_full = {int(e.split(":")[0].split(" ")[1]) for e in errs_p1 if "Satır" in e and e.split(":")[0].split(" ")[1].isdigit()}

        for entry in final_listing:
            mc_hex_display = entry['machine_code_hex'] if entry['machine_code_hex'] else "    "
            line_num_str = f"L:{entry['line_num']:<2}" # Satır numarası için sabit genişlik
            addr_hex_str = f"Adr: {entry['address_hex']}"
            code_str = f"Kod: {mc_hex_display:<10}" # Makine kodu için daha geniş alan
            
            label_str = entry['label'] if entry['label'] else ""
            mnemonic_str = entry['mnemonic'] if entry['mnemonic'] else ""
            operand_str = entry['operand_str'] if entry['operand_str'] else ""
            comment_str = f"; {entry['comment']}" if entry['comment'] else ""

            # Daha düzenli bir çıktı için f-string ile formatlama
            print(f"{line_num_str} {addr_hex_str}  {code_str}  {label_str:<8} {mnemonic_str:<5} {operand_str:<15} {comment_str}")

            if entry['error']:
                is_pass1_error_reported = False
                for p1_err in errs_p1:
                    if f"Satır {entry['line_num']}" in p1_err and entry['error'] in p1_err:
                        is_pass1_error_reported = True
                        break
                if not is_pass1_error_reported:
                    print(f"    HATA (P2): {entry['error']}")


        if errs_p2_only_full:
            print("\nPass 2'de Oluşan Farklı Hatalar (Gömülü Test):")
            for err_idx, err in enumerate(errs_p2_only_full): 
                print(f"  P2 Farklı Hata {err_idx+1}: {err}")
        elif errs_p1 and not errs_p2_only_full:
            print("\n(Pass 2'de Pass 1 hataları dışında yeni hata bulunamadı - Gömülü Test.)")
        elif not errs_p1 and not errs_p2_only_full:
            print("\nPass 2'de ek hata bulunamadı (Gömülü Test).")

        print("\nMakine Kodu Segmentleri (Gömülü Test):")
        if mc_segments:
            for addr, byte_codes in mc_segments:
                hex_codes = " ".join([f"{b:02X}" for b in byte_codes])
                print(f"  Segment @ ${addr:04X}: {hex_codes}")
        else:
            print("  (Makine kodu segmenti üretilmedi veya hatalar nedeniyle boş - Gömülü Test.)")