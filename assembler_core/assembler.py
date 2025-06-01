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

if __package__:
    print(f"assembler.py: Paket '{__package__}' olarak algılandı. Göreceli importlar deneniyor (.lexer vb.)...")
    from .lexer import parse_line, LABEL_REGEX
    from .m6800_opcodes import OPCODE_TABLE, ADDR_MODE_IMMEDIATE, ADDR_MODE_DIRECT, \
                               ADDR_MODE_EXTENDED, ADDR_MODE_INDEXED, ADDR_MODE_RELATIVE, \
                               ADDR_MODE_INHERENT, PSEUDO_OPS # PSEUDO_OPS buradan gelmeli
    from .symbol_table import SymbolTable  # Örneğin başka bir dosyada ise
    print("assembler.py: Göreceli importlar denendi.")
else:
    print("assembler.py: Paket bilgisi yok. Doğrudan importlar deneniyor...")
    from lexer import parse_line, LABEL_REGEX
    from m6800_opcodes import OPCODE_TABLE, ADDR_MODE_IMMEDIATE, ADDR_MODE_DIRECT, \
                               ADDR_MODE_EXTENDED, ADDR_MODE_INDEXED, ADDR_MODE_RELATIVE, \
                               ADDR_MODE_INHERENT, PSEUDO_OPS
    from .symbol_table import SymbolTable  # Örneğin başka bir dosyada ise
    print("assembler.py: Doğrudan importlar tamamlandı.")

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
    # Bu fonksiyon bir önceki versiyonunuzdaki gibi kalabilir.
    # ... (fonksiyon içeriği öncekiyle aynı) ...
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
        except ValueError: pass
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
        except ValueError: pass
    if ADDR_MODE_EXTENDED in op_details_for_mnemonic:
        return ADDR_MODE_EXTENDED, int(op_details_for_mnemonic[ADDR_MODE_EXTENDED][1]), None
    elif ADDR_MODE_DIRECT in op_details_for_mnemonic:
        return ADDR_MODE_DIRECT, int(op_details_for_mnemonic[ADDR_MODE_DIRECT][1]), None
    return None, 0, f"'{mnemonic}' için operand '{operand_str}' ile uygun adresleme modu bulunamadı veya desteklenmiyor."


def parse_operand_for_equ(operand_str, symbol_table, line_num): # RMB için de kullanılacak, mesajı güncelleyelim
    if operand_str is None:
        return None, f"Satır {line_num}: EQU/ORG/RMB için operand eksik."
    operand_str = operand_str.strip()
    if HEX_REGEX.match(operand_str): return int(operand_str[1:], 16), None
    elif BIN_REGEX.match(operand_str): return int(operand_str[1:], 2), None
    elif DEC_REGEX.match(operand_str): return int(operand_str), None
    elif is_label_like(operand_str):
        if symbol_table:
            value = symbol_table.get_symbol_value(operand_str.upper())
            if value is not None: return value, None
            else: return None, f"Satır {line_num}: EQU/ORG/RMB için tanımsız etiket referansı: {operand_str}"
        else: return None, f"Satır {line_num}: EQU/ORG/RMB etiketi için sembol tablosu eksik: {operand_str}"
    else: return None, f"Satır {line_num}: EQU/ORG/RMB için geçersiz değer: {operand_str}"

# --- Birinci Geçiş (Pass 1) ---
def pass_one(source_lines):
    symbol_table = SymbolTable()
    processed_lines_data = []
    errors = []
    location_counter = 0

    for i, line_text in enumerate(source_lines):
        parsed_line_info = parse_line(i + 1, line_text)

        current_line_data = {
            **parsed_line_info,
            "address": location_counter,
            "size": 0,
            "addressing_mode": None,
        }

        if parsed_line_info.get("error"): # Lexer'dan hata geldiyse
            # Hata mesajını errors listesine ekle
            formatted_lexer_error = f"Satır {current_line_data['line_num']} (Lexer): {parsed_line_info['error']}"
            if formatted_lexer_error not in errors:
                errors.append(formatted_lexer_error)
            # current_line_data['error'] zaten parsed_line_info'dan kopyalandı.
            processed_lines_data.append(current_line_data)
            continue # Bu satır için başka işlem yapma

        if not current_line_data["label"] and not current_line_data["mnemonic"]: # Boş veya sadece yorum
            processed_lines_data.append(current_line_data)
            continue

        # Etiket Tanımlama (EQU ve RMB hariç)
        if current_line_data["label"]:
            label_name_upper = current_line_data["label"].upper()
            is_equ_or_rmb = current_line_data["mnemonic"] and current_line_data["mnemonic"].upper() in ["EQU", "RMB"]
            if not is_equ_or_rmb:
                try:
                    symbol_table.add_symbol(label_name_upper, location_counter, current_line_data["line_num"])
                except ValueError as e:
                    err_msg = str(e)
                    errors.append(err_msg)
                    current_line_data["error"] = err_msg
                    # print(f"DEBUG P1 (Normal Etiket): Tekrarlayan etiket: {err_msg}")

        # Mnemonic İşleme (Eğer hata yoksa)
        if current_line_data["mnemonic"] and not current_line_data.get("error"):
            mnemonic_upper = current_line_data["mnemonic"].upper()

            if mnemonic_upper == "ORG":
                if current_line_data["operand_str"]:
                    try:
                        val, err = parse_operand_for_equ(current_line_data["operand_str"], symbol_table, current_line_data["line_num"])
                        if err: raise ValueError(err)
                        location_counter = val
                        current_line_data["address"] = location_counter
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
                        symbol_table.add_symbol(current_line_data["label"].upper(), value, current_line_data["line_num"])
                        current_line_data["address"] = None
                    except ValueError as e:
                        err_msg = str(e)
                        errors.append(err_msg); current_line_data["error"] = err_msg
                current_line_data["size"] = 0

            elif mnemonic_upper == "RMB":
                if current_line_data["label"]:
                    try:
                        symbol_table.add_symbol(current_line_data["label"].upper(), location_counter, current_line_data["line_num"])
                    except ValueError as e:
                        err_msg = str(e)
                        errors.append(err_msg); current_line_data["error"] = err_msg
                
                if not current_line_data.get("error"): # Etiket hatası yoksa devam et
                    if current_line_data["operand_str"]:
                        try:
                            num_bytes, err_rmb = parse_operand_for_equ(current_line_data["operand_str"], symbol_table, current_line_data["line_num"])
                            if err_rmb: raise ValueError(err_rmb)
                            if not isinstance(num_bytes, int) or num_bytes < 0:
                                raise ValueError(f"RMB için geçersiz byte sayısı: {current_line_data['operand_str']}")
                            current_line_data["size"] = num_bytes
                        except ValueError as e:
                            err_msg = f"Satır {current_line_data['line_num']}: RMB - {e}"
                            errors.append(err_msg); current_line_data["error"] = err_msg
                            current_line_data["size"] = 0
                    else:
                        err_msg = f"Satır {current_line_data['line_num']}: RMB için operand eksik."
                        errors.append(err_msg); current_line_data["error"] = err_msg
                        current_line_data["size"] = 0

            elif mnemonic_upper == "FCB":
                if current_line_data["operand_str"]:
                    try:
                        vals = [s.strip() for s in current_line_data["operand_str"].split(',')]
                        current_line_data["size"] = len(vals)
                        for v_str in vals:
                            _, err = parse_operand_for_equ(v_str, symbol_table, current_line_data["line_num"])
                            if err and not is_label_like(v_str): raise ValueError(f"geçersiz byte değeri: '{v_str}' ({err})")
                    except ValueError as e:
                        err_msg = f"Satır {current_line_data['line_num']}: FCB - {e}"
                        errors.append(err_msg); current_line_data["error"] = err_msg
                        current_line_data["size"] = 0
                else:
                    err_msg = f"Satır {current_line_data['line_num']}: FCB için operand eksik."
                    errors.append(err_msg); current_line_data["error"] = err_msg

            elif mnemonic_upper == "FDB": # FDB BLOĞU EKLENDİ/GÜNCELLENDİ
                if current_line_data["operand_str"]:
                    try:
                        vals = [s.strip() for s in current_line_data["operand_str"].split(',')]
                        current_line_data["size"] = len(vals) * 2
                        for v_str in vals:
                            _, err = parse_operand_for_equ(v_str, symbol_table, current_line_data["line_num"])
                            if err and not is_label_like(v_str): raise ValueError(f"geçersiz word değeri: '{v_str}' ({err})")
                    except ValueError as e:
                        err_msg = f"Satır {current_line_data['line_num']}: FDB - {e}"
                        errors.append(err_msg); current_line_data["error"] = err_msg
                        current_line_data["size"] = 0
                else:
                    err_msg = f"Satır {current_line_data['line_num']}: FDB için operand eksik."
                    errors.append(err_msg); current_line_data["error"] = err_msg

            elif mnemonic_upper == "FCC": # FCC BLOĞU EKLENDİ/GÜNCELLENDİ
                op_str = current_line_data["operand_str"]
                if op_str:
                    if len(op_str) >= 2 and \
                       ((op_str.startswith('"') and op_str.endswith('"')) or \
                        (op_str.startswith("'") and op_str.endswith("'"))):
                        current_line_data["size"] = len(op_str) - 2
                    else:
                        err_msg = f"Satır {current_line_data['line_num']}: FCC için geçersiz string formatı: {op_str}"
                        errors.append(err_msg); current_line_data["error"] = err_msg
                        current_line_data["size"] = 0
                else:
                    err_msg = f"Satır {current_line_data['line_num']}: FCC için operand eksik."
                    errors.append(err_msg); current_line_data["error"] = err_msg
            
            elif mnemonic_upper == "END":
                current_line_data["size"] = 0
                processed_lines_data.append(current_line_data)
                break

            else: # Normal M6800 Komutları
                mode, size, err_addr = determine_addressing_mode_and_size(
                    mnemonic_upper, current_line_data["operand_str"], symbol_table, location_counter
                )
                if err_addr:
                    err_msg = f"Satır {current_line_data['line_num']}: {err_addr}"
                    errors.append(err_msg); current_line_data["error"] = err_addr
                else:
                    current_line_data["size"] = size
                    current_line_data["addressing_mode"] = mode
        
        elif current_line_data["label"] and not current_line_data["mnemonic"]: # Sadece etiket
            if not current_line_data.get("error"): # Etiket tanımında hata yoksa
                current_line_data["size"] = 0

        # Location Counter Güncellemesi
        if not current_line_data.get("error"):
            mne_lc = current_line_data["mnemonic"].upper() if current_line_data["mnemonic"] else ""
            if mne_lc not in ["EQU", "ORG", "END"]:
                 location_counter += current_line_data["size"]
        
        processed_lines_data.append(current_line_data)

    return symbol_table, processed_lines_data, list(set(errors))

# --- İkinci Geçiş (Pass 2) için Yardımcı Fonksiyon ---
def parse_operand_value_for_pass2(operand_str, symbol_table, line_num, current_address_plus_size_for_relative=0):
    # Bu fonksiyon bir önceki versiyonunuzdaki gibi (ETİKET+SAYI desteğiyle) kalabilir.
    # ... (fonksiyon içeriği öncekiyle aynı) ...
    if operand_str is None: return 0, None
    operand_str = operand_str.strip()
    match_plus = re.fullmatch(r"([a-zA-Z_][a-zA-Z0-9_]*)\s*\+\s*([0-9]+|\$[0-9A-Fa-f]+|%[01]+)", operand_str, re.IGNORECASE)
    match_minus = re.fullmatch(r"([a-zA-Z_][a-zA-Z0-9_]*)\s*-\s*([0-9]+|\$[0-9A-Fa-f]+|%[01]+)", operand_str, re.IGNORECASE)
    if match_plus:
        label_name, offset_str = match_plus.groups()
        label_value = symbol_table.get_symbol_value(label_name.upper())
        if label_value is None: return None, f"Satır {line_num}: İfadede tanımsız etiket: {label_name}"
        offset_value, err_offset = parse_operand_value_for_pass2(offset_str, symbol_table, line_num)
        if err_offset: return None, f"Satır {line_num}: İfadede geçersiz offset: {offset_str} ({err_offset})"
        return label_value + offset_value, None
    elif match_minus:
        label_name, offset_str = match_minus.groups()
        label_value = symbol_table.get_symbol_value(label_name.upper())
        if label_value is None: return None, f"Satır {line_num}: İfadede tanımsız etiket: {label_name}"
        offset_value, err_offset = parse_operand_value_for_pass2(offset_str, symbol_table, line_num)
        if err_offset: return None, f"Satır {line_num}: İfadede geçersiz offset: {offset_str} ({err_offset})"
        return label_value - offset_value, None
    if IMM_REGEX.match(operand_str): return parse_operand_value_for_pass2(operand_str[1:], symbol_table, line_num)
    indexed_match = IND_REGEX.match(operand_str)
    if indexed_match:
        offset_str = indexed_match.group(1).strip()
        return (0, None) if not offset_str else parse_operand_value_for_pass2(offset_str, symbol_table, line_num)
    if HEX_REGEX.match(operand_str):
        try: return int(operand_str[1:], 16), None
        except ValueError: return None, f"Satır {line_num}: Geçersiz hex değer: {operand_str}"
    if BIN_REGEX.match(operand_str):
        try: return int(operand_str[1:], 2), None
        except ValueError: return None, f"Satır {line_num}: Geçersiz binary değer: {operand_str}"
    if is_label_like(operand_str):
        value = symbol_table.get_symbol_value(operand_str.upper())
        return (value, None) if value is not None else (None, f"Satır {line_num}: Tanımsız etiket: {operand_str}")
    if DEC_REGEX.match(operand_str):
        try: return int(operand_str), None
        except ValueError: return None, f"Satır {line_num}: Geçersiz decimal değer: {operand_str}"
    return None, f"Satır {line_num}: Operand ayrıştırılamadı: {operand_str}"


# --- İkinci Geçiş (Pass 2) ---
def pass_two(processed_lines_pass1, symbol_table):
    # Bu fonksiyon bir önceki versiyonunuzdaki gibi kalabilir.
    # (RMB'yi pas geçme ve diğer Pass 2 hata kontrolleri zaten vardı)
    # ... (fonksiyon içeriği öncekiyle aynı) ...
    listing_output = []
    machine_code_segments = []
    current_segment_address = -1
    current_segment_bytes = []
    errors_pass2 = [] # Sadece Pass 2'de YENİ oluşan hatalar için
    for line_data_p1 in processed_lines_pass1:
        current_listing_entry = {
            "line_num": line_data_p1["line_num"],
            "address_hex": f"${line_data_p1['address']:04X}" if line_data_p1['address'] is not None else "----",
            "machine_code_hex": "", "label": line_data_p1["label"], "mnemonic": line_data_p1["mnemonic"],
            "operand_str": line_data_p1["operand_str"], "original_line": line_data_p1["original_line"],
            "comment": line_data_p1["comment"], "error": line_data_p1.get("error") # Pass 1'den gelen hatayı al
        }
        if current_listing_entry["error"]: # Pass 1'den hata geldiyse, Pass 2'de daha fazla işlem yapma
            listing_output.append(current_listing_entry)
            continue
        # ... (pass_two'nun geri kalanı, Pass 2'ye özgü hataları errors_pass2'ye ekler
        #      ve current_listing_entry["error"] alanını günceller)
        if current_segment_address != -1 and line_data_p1["address"] != current_segment_address:
            if current_segment_bytes: machine_code_segments.append((current_segment_address, current_segment_bytes))
            current_segment_bytes = []
        current_segment_address = line_data_p1["address"]
        generated_bytes_for_line = []
        if line_data_p1["mnemonic"]:
            mnemonic_upper = line_data_p1["mnemonic"].upper()
            operand_str_p1 = line_data_p1["operand_str"]
            addressing_mode_p1 = line_data_p1.get("addressing_mode")
            if mnemonic_upper in ["ORG", "EQU", "END", "RMB"]: pass
            elif mnemonic_upper == "FCB":
                # ... (FCB işleme ve Pass 2 hata kontrolü) ...
                if operand_str_p1:
                    byte_strs = [s.strip() for s in operand_str_p1.split(',')]
                    for b_str in byte_strs:
                        val, err = parse_operand_value_for_pass2(b_str, symbol_table, line_data_p1["line_num"])
                        if err: current_listing_entry["error"] = err; errors_pass2.append(err); generated_bytes_for_line.clear(); break
                        if not (0 <= val <= 255): err = f"Satır {line_data_p1['line_num']}: FCB değeri (${val:02X}) 8-bit aralığı dışında."; current_listing_entry["error"] = err; errors_pass2.append(err); generated_bytes_for_line.clear(); break
                        generated_bytes_for_line.append(val & 0xFF)
                    if current_listing_entry["error"]: generated_bytes_for_line.clear()
                else: err = f"Satır {line_data_p1['line_num']}: FCB için operand eksik (P2)."; current_listing_entry["error"] = err; errors_pass2.append(err) # Bu P1 hatası olmalıydı
            elif mnemonic_upper == "FDB":
                # ... (FDB işleme ve Pass 2 hata kontrolü) ...
                if operand_str_p1:
                    word_strs = [s.strip() for s in operand_str_p1.split(',')]
                    for w_str in word_strs:
                        val, err = parse_operand_value_for_pass2(w_str, symbol_table, line_data_p1["line_num"])
                        if err: current_listing_entry["error"] = err; errors_pass2.append(err); generated_bytes_for_line.clear(); break
                        if not (0 <= val <= 65535): err = f"Satır {line_data_p1['line_num']}: FDB değeri (${val:04X}) 16-bit aralığı dışında."; current_listing_entry["error"] = err; errors_pass2.append(err); generated_bytes_for_line.clear(); break
                        generated_bytes_for_line.extend([(val >> 8) & 0xFF, val & 0xFF])
                    if current_listing_entry["error"]: generated_bytes_for_line.clear()
                else: err = f"Satır {line_data_p1['line_num']}: FDB için operand eksik (P2)."; current_listing_entry["error"] = err; errors_pass2.append(err) # Bu P1 hatası olmalıydı
            elif mnemonic_upper == "FCC":
                # ... (FCC işleme ve Pass 2 hata kontrolü) ...
                if operand_str_p1: # Format P1'de kontrol edildi
                    text_content = operand_str_p1[1:-1]
                    for char_code in [ord(c) for c in text_content]:
                        if not (0 <= char_code <= 255): err = f"Satır {line_data_p1['line_num']}: FCC için geçersiz karakter kodu: {char_code}"; current_listing_entry["error"] = err; errors_pass2.append(err); generated_bytes_for_line.clear(); break
                        generated_bytes_for_line.append(char_code)
                    if current_listing_entry["error"]: generated_bytes_for_line.clear()
                # else: P1 hatası olmalıydı
            else: # Opcode'lar
                # ... (Opcode işleme ve Pass 2 hata kontrolü) ...
                op_hex, num_bytes_str, _ = OPCODE_TABLE[mnemonic_upper][addressing_mode_p1]
                num_bytes = int(num_bytes_str)
                generated_bytes_for_line.append(int(op_hex, 16))
                operand_value = 0
                if num_bytes > 1:
                    val, err_op = parse_operand_value_for_pass2(operand_str_p1, symbol_table, line_data_p1["line_num"])
                    if err_op: current_listing_entry["error"] = err_op; errors_pass2.append(err_op)
                    else: operand_value = val

                if not current_listing_entry.get("error"): # Operand parse hatası yoksa devam et
                    if addressing_mode_p1 == ADDR_MODE_IMMEDIATE:
                        if num_bytes == 2 and not (0 <= operand_value <= 255): err = f"Satır {line_data_p1['line_num']}: Immediate değer ({operand_value}) 8-bit aralığı dışında."
                        elif num_bytes == 3 and not (0 <= operand_value <= 65535): err = f"Satır {line_data_p1['line_num']}: Immediate değer ({operand_value}) 16-bit aralığı dışında."
                        else: generated_bytes_for_line.extend([(operand_value >> 8) & 0xFF, operand_value & 0xFF] if num_bytes == 3 else [operand_value & 0xFF])
                    elif addressing_mode_p1 == ADDR_MODE_DIRECT and not (0 <= operand_value <= 255): err = f"Satır {line_data_p1['line_num']}: Direct adres ({operand_value}) 8-bit aralığı dışında."
                    elif addressing_mode_p1 == ADDR_MODE_INDEXED and not (0 <= operand_value <= 255): err = f"Satır {line_data_p1['line_num']}: Indexed offset ({operand_value}) 8-bit aralığı dışında."
                    elif addressing_mode_p1 == ADDR_MODE_EXTENDED and not (0 <= operand_value <= 65535): err = f"Satır {line_data_p1['line_num']}: Extended adres ({operand_value}) 16-bit aralığı dışında."
                    elif addressing_mode_p1 == ADDR_MODE_RELATIVE:
                        target_address = operand_value
                        offset = target_address - (line_data_p1["address"] + num_bytes)
                        if not (-128 <= offset <= 127): err = f"Satır {line_data_p1['line_num']}: Relative offset ({offset}) menzil dışı."
                        else: generated_bytes_for_line.append(offset & 0xFF)
                    
                    if 'err' in locals() and err: # Eğer yukarıdaki kontrollerde bir err tanımlandıysa
                        current_listing_entry["error"] = err; errors_pass2.append(err)
                    elif addressing_mode_p1 not in [ADDR_MODE_IMMEDIATE, ADDR_MODE_RELATIVE, ADDR_MODE_INHERENT]:
                        if num_bytes == 2: generated_bytes_for_line.append(operand_value & 0xFF)
                        elif num_bytes == 3: generated_bytes_for_line.extend([(operand_value >> 8) & 0xFF, operand_value & 0xFF])
                if current_listing_entry.get("error"): generated_bytes_for_line.clear()

        if not current_listing_entry.get("error") and generated_bytes_for_line:
            current_listing_entry["machine_code_hex"] = "".join([f"{b:02X}" for b in generated_bytes_for_line])
            current_segment_bytes.extend(generated_bytes_for_line)
        listing_output.append(current_listing_entry)
    if current_segment_bytes and current_segment_address != -1 : machine_code_segments.append((current_segment_address, current_segment_bytes))
    return listing_output, machine_code_segments, list(set(errors_pass2))


# --- Ana Test Bloğu ---
if __name__ == '__main__':
    # --- Test Dosyası Seçimi ---
    # test_file_name = "pass1_invalid_label_test.asm"
    test_file_name = "pass1_label_equ_errors.asm"
    # test_file_name = "pass2_errors.asm"
    # test_file_name = "successful_all_features.asm"
    # test_file_name = None # Gömülü test için

    # ... (if __name__ == '__main__' bloğunun geri kalanı aynı kalabilir) ...
    if test_file_name: # Eğer bir dosya adı belirtilmişse, o dosyayı test et
        print(f"\n\n--- ASSEMBLER TESTİ ({test_file_name}) ---")
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(script_dir)
            current_test_file_path = os.path.join(project_root, "tests", test_file_name)
            if not os.path.exists(current_test_file_path):
                alt_path = os.path.join("..", "tests", test_file_name) # Eğer assembler_core'dan çalıştırılıyorsa
                if os.path.exists(alt_path): current_test_file_path = alt_path
                else: raise FileNotFoundError(f"Test dosyası bulunamadı: {current_test_file_path} veya {alt_path}")
            with open(current_test_file_path, 'r', encoding='utf-8') as f:
                source_lines_current_test = f.read().strip().split('\n')
            print(f"'{current_test_file_path}' dosyasından {len(source_lines_current_test)} satır yüklendi.")
        except FileNotFoundError as e:
            print(f"HATA: Test dosyası yüklenemedi: {e}")
            source_lines_current_test = []

        if source_lines_current_test:
            print(f"\n--- PASS 1 ({test_file_name}) ---")
            sym_table_test, proc_lines_p1_test, errs_p1_test = pass_one(source_lines_current_test)
            print("\nSembol Tablosu:")
            print(sym_table_test)
            if errs_p1_test:
                print("\nPass 1 Hataları:")
                for idx, err in enumerate(errs_p1_test): print(f"  P1 Hata {idx+1}: {err}")
            else: print("\nPass 1'de hata bulunamadı.")

            print(f"\n--- PASS 2 ({test_file_name}) ---")
            final_listing_test, mc_segments_test, errs_p2_test = pass_two(proc_lines_p1_test, sym_table_test)
            
            print("\nSon Listeleme:")
            for entry in final_listing_test:
                mc_hex = entry['machine_code_hex'] if entry['machine_code_hex'] else "    "
                label = entry['label'] if entry['label'] else ""
                mnemonic = entry['mnemonic'] if entry['mnemonic'] else ""
                operand = entry['operand_str'] if entry['operand_str'] else ""
                comment = f"; {entry['comment']}" if entry['comment'] else ""
                error_msg = f" <<< HATA: {entry['error']}" if entry.get('error') else ""
                
                print(f"L:{entry['line_num']:<3} Adr:{entry['address_hex']:<6} Kod:{mc_hex:<12} {label:<10} {mnemonic:<7} {operand:<20} {comment}{error_msg}")

            if errs_p2_test: # Bunlar sadece Pass 2'de YENİ oluşan hatalar olmalı
                print("\nPass 2'de Oluşan Ek Hatalar:")
                for idx, err in enumerate(errs_p2_test): print(f"  P2 Hata {idx+1}: {err}")
            # else: # Eğer errs_p1_test varsa ama errs_p2_test boşsa, sadece P1 hataları vardı.
            #     if not errs_p1_test: print("\nPass 2'de ek hata bulunamadı.")

            if not errs_p1_test and not errs_p2_test:
                print(f"\n'{test_file_name}' için derleme başarıyla tamamlandı, hata bulunamadı.")


            print("\nMakine Kodu Segmentleri:")
            if mc_segments_test:
                for addr, byte_codes in mc_segments_test:
                    print(f"  Segment @ ${addr:04X}: {' '.join([f'{b:02X}' for b in byte_codes])}")
            else: print("  (Makine kodu segmenti üretilmedi.)")
    else: # Gömülü test
        # ... (gömülü test kodunuz aynı kalabilir) ...
        print("Gömülü test çalıştırılıyor...")
        # ...