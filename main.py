# main.py

import argparse # Komut satırı argümanlarını işlemek için
import os
import sys


# Proje kök dizinini Python'un arama yoluna ekleyelim ki
# assembler_core paketini bulabilsin.
# Bu, main.py'nin proje kök dizininde olduğunu varsayar.
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from assembler_core.assembler import pass_one, pass_two
    # from assembler_core.symbol_table import SymbolTable # pass_one zaten döndürüyor
except ImportError as e:
    print(f"HATA: Gerekli modüller yüklenemedi. Proje yapınızı kontrol edin.")
    print(f"Detay: {e}")
    print("PYTHONPATH ortam değişkeninizin doğru ayarlandığından veya")
    print("bu script'i proje kök dizininden çalıştırdığınızdan emin olun.")
    sys.exit(1)

def assemble_file(input_filepath, output_list_filepath=None, output_hex_filepath=None):
    """
    Verilen assembly dosyasını assemble eder ve çıktıları üretir.
    """
    if not os.path.exists(input_filepath):
        print(f"HATA: Giriş dosyası bulunamadı: {input_filepath}")
        return

    print(f"'{input_filepath}' dosyası assemble ediliyor...")

    try:
        with open(input_filepath, 'r', encoding='utf-8') as f:
            source_lines = f.read().strip().split('\n')
    except Exception as e:
        print(f"HATA: Giriş dosyası okunurken bir sorun oluştu: {e}")
        return

    # --- Pass 1 ---
    print("\n--- PASS 1 Başlatılıyor ---")
    symbol_table, processed_lines_p1, errors_p1 = pass_one(source_lines)

    print("\nSembol Tablosu (Pass 1 sonrası):")
    print(symbol_table) # SymbolTable'ın __str__ metodu çağrılacak

    if errors_p1:
        print("\nPass 1 Hataları:")
        for err in errors_p1:
            print(f"  {err}")
        # İsteğe bağlı: Pass 1'de hata varsa devam etme
        # print("\nPass 1'de hatalar bulunduğu için assemble işlemi durduruldu.")
        # return
    else:
        print("\nPass 1 başarıyla tamamlandı, hata bulunamadı.")

    # --- Pass 2 ---
    print("\n--- PASS 2 Başlatılıyor ---")
    final_listing, machine_code_segments, errors_p2 = pass_two(processed_lines_p1, symbol_table)

    if errors_p2: # Sadece Pass 2'de oluşan yeni/farklı hatalar
        unique_p2_errors = [err for err in errors_p2 if err not in errors_p1]
        if unique_p2_errors:
            print("\nPass 2 Hataları:")
            for err in unique_p2_errors:
                print(f"  {err}")
    
    if not errors_p1 and not errors_p2 : # Veya daha esnek bir hata kontrolü
         print("\nPass 2 başarıyla tamamlandı, ek hata bulunamadı.")


    # Çıktı dosyalarını oluşturma
    base_filename = os.path.splitext(os.path.basename(input_filepath))[0]

    # 1. Listeleme Dosyası (.lst)
    if output_list_filepath is None:
        output_list_filepath = base_filename + ".lst"
    
    print(f"\nListeleme dosyası oluşturuluyor: {output_list_filepath}")
    try:
        with open(output_list_filepath, 'w', encoding='utf-8') as lst_file:
            lst_file.write(f"Kaynak Dosya: {os.path.basename(input_filepath)}\n")
            lst_file.write("Assembler Listeleme Çıktısı\n")
            lst_file.write("=" * 80 + "\n")
            lst_file.write(f"{'Satır':<5} {'Adres':<7} {'Mak.Kodu':<12} {'Etiket':<10} {'Komut':<7} {'Operand':<20} {'Yorum'}\n")
            lst_file.write("-" * 80 + "\n")
            for entry in final_listing:
                addr_hex = entry['address_hex'] if entry['address_hex'] != "----" else "      "
                mc_hex = entry['machine_code_hex'] if entry['machine_code_hex'] else ""
                label = entry['label'] if entry['label'] else ""
                mnemonic = entry['mnemonic'] if entry['mnemonic'] else ""
                operand = entry['operand_str'] if entry['operand_str'] else ""
                comment = entry['comment'] if entry['comment'] else ""
                
                lst_file.write(f"{entry['line_num']:<5} {addr_hex:<7} {mc_hex:<12} {label:<10} {mnemonic:<7} {operand:<20} {comment}\n")
                if entry['error']:
                    lst_file.write(f"***** HATA: {entry['error']}\n")
            lst_file.write("=" * 80 + "\n")
            if errors_p1 or errors_p2:
                 lst_file.write("\nToplam Hatalar:\n")
                 for err in set(errors_p1 + errors_p2): # Tekrarları önle
                     lst_file.write(f"- {err}\n")
            lst_file.write("Listeleme Sonu.\n")
        print(f"Listeleme dosyası '{output_list_filepath}' başarıyla oluşturuldu.")
    except Exception as e:
        print(f"HATA: Listeleme dosyası oluşturulurken bir sorun oluştu: {e}")

    # 2. Makine Kodu Dosyası (.hex veya .bin - şimdilik basit bir hex formatı)
    # Gerçek bir .hex dosyası (Intel HEX, S-Record) formatı daha karmaşıktır.
    # Şimdilik sadece adres ve byte'ları yazdıracağız.
    if machine_code_segments and not (errors_p1 or errors_p2): # Hata yoksa oluştur
        if output_hex_filepath is None:
            output_hex_filepath = base_filename + ".hex" # Basit hex dökümü
        
        print(f"\nMakine kodu dosyası oluşturuluyor: {output_hex_filepath}")
        try:
            with open(output_hex_filepath, 'w', encoding='utf-8') as hex_file:
                hex_file.write(f"; {os.path.basename(input_filepath)} için makine kodu dökümü\n")
                for address, byte_codes in machine_code_segments:
                    hex_string = " ".join([f"{b:02X}" for b in byte_codes])
                    hex_file.write(f"${address:04X}: {hex_string}\n")
            print(f"Makine kodu dosyası '{output_hex_filepath}' başarıyla oluşturuldu.")
        except Exception as e:
            print(f"HATA: Makine kodu dosyası oluşturulurken bir sorun oluştu: {e}")
    elif errors_p1 or errors_p2:
        print("\nHatalar nedeniyle makine kodu dosyası oluşturulmadı.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Motorola M6800 Assembler")
    parser.add_argument("input_file", help="Assemble edilecek .asm kaynak dosyası")
    parser.add_argument("-o_lst", "--output_list", help="Oluşturulacak listeleme dosyasının adı (örn: output.lst)", default=None)
    parser.add_argument("-o_hex", "--output_hex", help="Oluşturulacak makine kodu döküm dosyasının adı (örn: output.hex)", default=None)
    
    args = parser.parse_args()
    
    assemble_file(args.input_file, args.output_list, args.output_hex)