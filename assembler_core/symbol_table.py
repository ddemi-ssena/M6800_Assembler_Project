# assembler_core/symbol_table.py

class SymbolTable:
    """
    Assembler için sembol tablosunu (etiketler ve değerleri) yöneten sınıf.
    Etiketler büyük/küçük harf duyarsız olarak saklanır (genellikle büyük harfe çevrilir).
    """

    def __init__(self):
        """
        Yeni bir boş sembol tablosu oluşturur.
        self.table: Etiket adlarını (string) değerlerine (integer) eşleyen bir sözlük.
                     {'ETIKET_ADI': adres_veya_deger}
        self.definitions: Etiketin hangi satırda tanımlandığını tutar, hata mesajları için.
                          {'ETIKET_ADI': satir_numarasi}
        """
        self.table = {}
        self.definitions = {} # Hangi etiketin hangi satırda tanımlandığını izlemek için

    def add_symbol(self, name, value, line_num):
        """
        Sembol tablosuna yeni bir etiket ve değerini ekler.

        Args:
            name (str): Eklenecek etiketin adı.
            value (int): Etikete atanacak değer (adres veya sabit).
            line_num (int): Etiketin tanımlandığı kaynak koddaki satır numarası (hata raporlama için).

        Raises:
            ValueError: Eğer etiket zaten tabloda tanımlıysa.
        """
        # Etiket adlarını standart bir formatta (büyük harf) saklamak iyi bir pratiktir.
        # Bu, 'Loop' ve 'LOOP' gibi etiketlerin aynı kabul edilmesini sağlar.
        normalized_name = name.upper()

        if normalized_name in self.table:
            original_definition_line = self.definitions.get(normalized_name, "bilinmiyor")
            raise ValueError(
                f"Satır {line_num}: '{name}' etiketi zaten Satır {original_definition_line}'da tanımlanmış."
            )
        
        self.table[normalized_name] = value
        self.definitions[normalized_name] = line_num

    def get_symbol_value(self, name):
        """
        Verilen bir etiketin değerini sembol tablosundan alır.

        Args:
            name (str): Değeri sorgulanacak etiketin adı.

        Returns:
            int or None: Etiketin değeri (eğer bulunursa), aksi takdirde None.
        """
        normalized_name = name.upper()
        return self.table.get(normalized_name) # Sözlükte yoksa None döner

    def is_defined(self, name):
        """
        Verilen bir etiketin sembol tablosunda tanımlı olup olmadığını kontrol eder.

        Args:
            name (str): Kontrol edilecek etiketin adı.

        Returns:
            bool: Etiket tanımlıysa True, değilse False.
        """
        normalized_name = name.upper()
        return normalized_name in self.table

    def __str__(self):
        """
        Sembol tablosunun string temsilini döndürür (yazdırma ve hata ayıklama için).
        Değerleri hex formatında göstermek okunurluğu artırabilir.
        """
        if not self.table:
            return "Sembol Tablosu Boş."
        
        # Okunurluk için etiketleri sıralayabilir ve değerleri hex formatında gösterebiliriz
        sorted_symbols = sorted(self.table.items())
        
        output = "Sembol Tablosu:\n"
        output += "--------------------\n"
        output += "{:<15} | {:<10} | {:<10}\n".format("Etiket Adı", "Değer (Hex)", "Tanım Satırı")
        output += "--------------------\n"
        for name, value in sorted_symbols:
            # Değerin tipine göre formatlama yapabiliriz, ama genellikle int olacak
            hex_value = f"${value:04X}" if isinstance(value, int) else str(value)
            definition_line = self.definitions.get(name, '-') # Tanım satırı bilgisi
            output += "{:<15} | {:<10} | {:<10}\n".format(name, hex_value, definition_line)
        output += "--------------------\n"
        return output

    def clear(self):
        """
        Sembol tablosundaki tüm girişleri temizler.
        Yeniden assemble etme durumlarında kullanışlı olabilir.
        """
        self.table.clear()
        self.definitions.clear()

# Sınıfın nasıl kullanılacağını göstermek için basit bir test bloğu
if __name__ == '__main__':
    st = SymbolTable()

    try:
        st.add_symbol("START", 0x0100, 1)
        st.add_symbol("LOOP", 0x010A, 5)
        st.add_symbol("COUNTER", 0x0200, 10)
        st.add_symbol("VAL_EQU", 255, 12) # EQU ile tanımlanmış gibi

        print(st)

        print(f"\nLOOP etiketinin değeri: ${st.get_symbol_value('loop'):04X}") # Büyük/küçük harf duyarsız sorgu
        print(f"START etiketi tanımlı mı? {st.is_defined('START')}")
        print(f"UNKNOWN etiketi tanımlı mı? {st.is_defined('UNKNOWN')}")
        print(f"UNKNOWN etiketinin değeri: {st.get_symbol_value('UNKNOWN')}")

        # Aynı etiketi tekrar eklemeye çalışma (hata vermeli)
        print("\n'START' etiketini tekrar eklemeye çalışılıyor...")
        st.add_symbol("START", 0x0150, 15)

    except ValueError as e:
        print(f"HATA: {e}")

    st.clear()
    print("\nTablo temizlendikten sonra:")
    print(st)