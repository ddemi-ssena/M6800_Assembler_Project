# simulator_core/m6800_cpu.py

# CCR Bayrakları için sabitler (bit pozisyonları - M6800 sırasına göre)
# Bit:  7  6  5  4  3  2  1  0
#      (1)(1) H  I  N  Z  V  C
# En üst iki bit her zaman 1'dir.
CCR_CARRY     = 0x01  # Bit 0: Carry/Borrow
CCR_OVERFLOW  = 0x02  # Bit 1: Overflow
CCR_ZERO      = 0x04  # Bit 2: Zero
CCR_NEGATIVE  = 0x08  # Bit 3: Negative
CCR_INTERRUPT = 0x10  # Bit 4: Interrupt Mask
CCR_HALF_CARRY= 0x20  # Bit 5: Half Carry

class M6800CPU:
    def __init__(self):
        # Register'lar
        self.pc = 0x0000  # Program Counter (16-bit)
        self.sp = 0x0000  # Stack Pointer (16-bit)
        self.acc_a = 0x00 # Akümülatör A (8-bit)
        self.acc_b = 0x00 # Akümülatör B (8-bit)
        self.ix = 0x0000  # Index Register X (16-bit)
        self.ccr = 0xC0   # Condition Code Register (8-bit), ilk iki bit her zaman 1 (0b11000000)

        # Bellek
        self.memory = bytearray(65536) # 64KB RAM

        # Simülasyon durumu
        self.halted = False
        self.cycles = 0 # Geçen çevrim sayısı (daha gelişmiş simülasyonlar için)

        # Basit bir opcode -> işleyici fonksiyon eşlemesi (zamanla doldurulacak)
        # Opcode'lar hex olarak değil, integer olarak kullanılacak
        self.opcodes = {
            0x86: self._ldaa_imm,  # LDAA Immediate
            0xB6: self._ldaa_ext,  # LDAA Extended
            0x96: self._ldaa_dir,  # LDAA Direct (Eğer direct page'de ise)
            0xA6: self._ldaa_idx,  # LDAA Indexed
            # ... Diğer komutlar buraya eklenecek ...
            0x8B: self._adda_imm,  # ADDA Immediate
            0xBB: self._adda_ext,  # ADDA Extended
            0x97: self._staa_dir,  # STAA Direct
            0xB7: self._staa_ext,  # STAA Extended
            0xA7: self._staa_idx,  # STAA Indexed
            0x01: self._nop,       # NOP
            0x3F: self._swi,       # SWI
            # ... Diğer komutlar ...
        }

    def _update_ccr_nz(self, value, byte_size=1):
        """Verilen değere göre N ve Z bayraklarını günceller."""
        if byte_size == 1: # 8-bit
            is_zero = (value == 0)
            is_negative = (value & 0x80) != 0 # En anlamlı bit 1 mi?
        else: # 16-bit (örn: LDX, CPX sonuçları için)
            is_zero = (value == 0)
            # 16-bit değerlerde negatiflik, MSB'nin (bit 15) 1 olmasıyla belirlenir.
            # Ancak M6800'de CPX gibi bazı 16-bit işlemleri sonucu N bayrağını
            # sonucun 8-bitlik MSB'sine göre ayarlar. Bu detaylara dikkat etmek gerekir.
            # Şimdilik basit tutalım, 16-bit N için MSB (bit 15) kontrolü.
            is_negative = (value & 0x8000) != 0

        if is_zero:
            self.ccr |= CCR_ZERO    # Z bitini set et
        else:
            self.ccr &= ~CCR_ZERO   # Z bitini clear et

        if is_negative:
            self.ccr |= CCR_NEGATIVE  # N bitini set et
        else:
            self.ccr &= ~CCR_NEGATIVE # N bitini clear et

    def _update_ccr_v(self, operand1, operand2, result, byte_size=1):
        """Toplama/Çıkarma işlemleri için Overflow (V) bayrağını günceller."""
        # V = A7*B7*/R7 + /A7*/B7*R7  (A, B operandlar, R sonuç; 7. bitler)
        # A7, B7, R7 -> MSB'ler (0 veya 1)
        if byte_size == 1:
            msb_mask = 0x80
        else: # 16-bit (bu M6800'de nadir, ama genel bir fikir)
            msb_mask = 0x8000
        
        op1_msb = (operand1 & msb_mask) != 0
        op2_msb = (operand2 & msb_mask) != 0
        res_msb = (result & msb_mask) != 0

        # Toplama için overflow: (+)+(+)=(-) veya (-)+(-)=(+)
        # Çıkarma (A-B = A + (-B)) için overflow: (+)-(+)=(-) veya (-)-(+)=(+)
        # Bu, komutun toplama mı çıkarma mı olduğuna göre değişir.
        # Basit bir yaklaşım: İki pozitifin toplamı negatifse veya iki negatifin toplamı pozitifse.
        # Şimdilik sadece toplama için:
        overflow = False
        if not op1_msb and not op2_msb and res_msb: # P + P = N
            overflow = True
        elif op1_msb and op2_msb and not res_msb: # N + N = P
            overflow = True
        
        if overflow:
            self.ccr |= CCR_OVERFLOW
        else:
            self.ccr &= ~CCR_OVERFLOW

    def _update_ccr_c_add(self, result_wider):
        """Toplama sonrası Carry bayrağını günceller (8-bit işlemler için)."""
        if result_wider > 0xFF: # 8-bit toplama sonucu 8 biti aştıysa
            self.ccr |= CCR_CARRY
        else:
            self.ccr &= ~CCR_CARRY

    # --- Bellek Erişim Metotları ---
    def read_byte(self, address):
        self.cycles += 1 # Bellek okuma çevrimi
        return self.memory[address & 0xFFFF] # Adres 16-bit olmalı

    def write_byte(self, address, value):
        self.cycles += 1 # Bellek yazma çevrimi
        self.memory[address & 0xFFFF] = value & 0xFF # Değer 8-bit olmalı

    def read_word(self, address):
        # M6800 Big-Endian: Yüksek byte düşük adreste
        high_byte = self.read_byte(address)
        low_byte = self.read_byte(address + 1)
        return (high_byte << 8) | low_byte

    def write_word(self, address, value):
        high_byte = (value >> 8) & 0xFF
        low_byte = value & 0xFF
        self.write_byte(address, high_byte)
        self.write_byte(address + 1, low_byte)

    # --- Program Yükleme ve Reset ---
    def load_memory(self, segments):
        """
        Assembler'dan gelen makine kodu segmentlerini belleğe yükler.
        segments: [(address1, [byte1, byte2, ...]), (address2, [byte_a, byte_b, ...]), ...]
        """
        self.memory = bytearray(65536) # Belleği temizle
        for address, data_bytes in segments:
            for i, byte_val in enumerate(data_bytes):
                self.write_byte(address + i, byte_val)
        print(f"Simülatör: Program belleğe yüklendi. {len(segments)} segment.")

    def reset(self):
        """CPU'yu resetler. Reset vektöründen PC'yi yükler."""
        self.pc = self.read_word(0xFFFE) # Reset vektörü
        self.sp = 0xDFFF # Genellikle stack başlangıcı (isteğe bağlı ayarlanabilir)
        self.acc_a = 0x00
        self.acc_b = 0x00
        self.ix = 0x0000
        self.ccr = 0xC0 | CCR_INTERRUPT # I bayrağı reset'te set edilir.
        self.halted = False
        self.cycles = 0
        print(f"Simülatör: CPU resetlendi. PC = ${self.pc:04X}, SP = ${self.sp:04X}")


    # --- Komut Çekme ve Çalıştırma ---
    def fetch_byte(self):
        """PC'nin gösterdiği yerden bir byte okur ve PC'yi artırır."""
        value = self.read_byte(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF # PC'yi 16-bit sınırında tut
        return value

    def fetch_word(self):
        """PC'nin gösterdiği yerden bir word okur ve PC'yi 2 artırır."""
        value = self.read_word(self.pc)
        self.pc = (self.pc + 2) & 0xFFFF
        return value

    def step(self):
        """Bir sonraki komutu çalıştırır."""
        if self.halted:
            print("Simülatör: CPU durdurulmuş.")
            return False # Daha fazla adım atılamaz

        opcode = self.fetch_byte()
        self.cycles += 1 # Opcode fetch çevrimi

        if opcode in self.opcodes:
            handler = self.opcodes[opcode]
            handler() # İlgili komut işleyici fonksiyonunu çağır
            return True # Adım başarılı
        else:
            print(f"Simülatör: Bilinmeyen Opcode ${opcode:02X} @ ${self.pc-1:04X}")
            self.halted = True # Bilinmeyen komutta dur
            return False

    def run(self, max_cycles=1000000):
        """Programı self.halted olana veya max_cycles'a ulaşana kadar çalıştırır."""
        count = 0
        while not self.halted and count < max_cycles:
            if not self.step(): # Eğer step False dönerse (hata veya bilinmeyen opcode)
                break
            count += 1
        if count >= max_cycles:
            print(f"Simülatör: Maksimum çevrim sayısına ({max_cycles}) ulaşıldı.")
        print(f"Simülatör: Çalıştırma tamamlandı. Toplam çevrim: {self.cycles}")


    # --- ÖRNEK KOMUT İŞLEYİCİLERİ ---
    # (Zamanla tüm komutlar için eklenecek)

    def _nop(self): # Opcode 0x01
        # Hiçbir şey yapma
        pass

    def _swi(self): # Opcode 0x3F
        # Yazılım kesmesi, genellikle simülasyonu durdurur
        print(f"Simülatör: SWI komutu @ ${self.pc-1:04X}. CPU durduruluyor.")
        # Gerçek M6800'de register'lar stack'e push edilir ve SWI vektörüne dallanılır.
        # Şimdilik sadece durduralım.
        self.halted = True

    # LDAA Komutları
    def _ldaa_imm(self): # Opcode 0x86
        operand = self.fetch_byte()
        self.acc_a = operand
        self._update_ccr_nz(self.acc_a)
        self.ccr &= ~CCR_OVERFLOW # V bayrağını temizle

    def _ldaa_ext(self): # Opcode 0xB6
        address = self.fetch_word()
        self.acc_a = self.read_byte(address)
        self._update_ccr_nz(self.acc_a)
        self.ccr &= ~CCR_OVERFLOW

    def _ldaa_dir(self): # Opcode 0x96
        # Direct adresleme 0x00 - 0xFF arasını hedefler.
        # Genellikle 0x00XX olarak yorumlanır ama bazı assemblerlar sadece XX bekler.
        # Opcode 1 byte operand alır.
        address_offset = self.fetch_byte()
        # Direct page genellikle 0x0000'dadır. Eğer base register varsa (M6809 gibi), o eklenir.
        # M6800 için effective_address = 0x0000 + address_offset (genellikle)
        effective_address = address_offset # M6800'de direct adres 0-255 arasıdır.
        self.acc_a = self.read_byte(effective_address)
        self._update_ccr_nz(self.acc_a)
        self.ccr &= ~CCR_OVERFLOW
        
    def _ldaa_idx(self): # Opcode 0xA6
        offset = self.fetch_byte() # 8-bit işaretsiz offset
        effective_address = (self.ix + offset) & 0xFFFF
        self.acc_a = self.read_byte(effective_address)
        self._update_ccr_nz(self.acc_a)
        self.ccr &= ~CCR_OVERFLOW

    # ADDA Komutları
    def _adda_imm(self): # Opcode 0x8B
        operand = self.fetch_byte()
        # 8-bit toplama için daha geniş bir alanda yapıp sonra sonucu daraltmak
        # carry ve half-carry'yi doğru hesaplamak için önemlidir.
        result_wider = self.acc_a + operand
        old_a = self.acc_a
        self.acc_a = result_wider & 0xFF

        # CCR Güncellemeleri
        # H: (A3&B3) | (B3&/R3) | (/R3&A3) -- A, B operand, R sonuç. 3. bitler.
        # Şimdilik H bayrağını atlayalım, daha karmaşık.
        self._update_ccr_nz(self.acc_a)
        self._update_ccr_v(old_a, operand, self.acc_a) # Toplama için V
        self._update_ccr_c_add(result_wider) # Toplama için C

    def _adda_ext(self): # Opcode 0xBB
        address = self.fetch_word()
        operand = self.read_byte(address)
        result_wider = self.acc_a + operand
        old_a = self.acc_a
        self.acc_a = result_wider & 0xFF
        self._update_ccr_nz(self.acc_a)
        self._update_ccr_v(old_a, operand, self.acc_a)
        self._update_ccr_c_add(result_wider)

    # STAA Komutları
    def _staa_dir(self): # Opcode 0x97
        address_offset = self.fetch_byte()
        effective_address = address_offset
        self.write_byte(effective_address, self.acc_a)
        self._update_ccr_nz(self.acc_a) # STAA N ve Z'yi etkiler
        self.ccr &= ~CCR_OVERFLOW     # V bayrağını temizler

    def _staa_ext(self): # Opcode 0xB7
        address = self.fetch_word()
        self.write_byte(address, self.acc_a)
        self._update_ccr_nz(self.acc_a)
        self.ccr &= ~CCR_OVERFLOW

    def _staa_idx(self): # Opcode 0xA7
        offset = self.fetch_byte()
        effective_address = (self.ix + offset) & 0xFFFF
        self.write_byte(effective_address, self.acc_a)
        self._update_ccr_nz(self.acc_a)
        self.ccr &= ~CCR_OVERFLOW


if __name__ == '__main__':
    # Basit bir test
    cpu = M6800CPU()
    
    # Örnek program: LDAA #$10, ADDA #$20, STAA $0030, SWI
    # Opcode'lar: 86 10 (LDAA #$10)
    #              8B 20 (ADDA #$20)
    #              97 30 (STAA $30 - Direct)
    #              3F    (SWI)
    test_program_segments = [
        (0xC000, [0x86, 0x10, 0x8B, 0x20, 0x97, 0x30, 0x3F])
    ]
    
    cpu.load_memory(test_program_segments)
    cpu.pc = 0xC000 # Programı başlangıç adresine ayarla
    # cpu.reset() # veya reset ile başlat (reset vektörü 0xFFFE, 0xFFFF'de olmalı)

    print(f"Başlangıç: PC=${cpu.pc:04X} A=${cpu.acc_a:02X} B=${cpu.acc_b:02X} X=${cpu.ix:04X} SP=${cpu.sp:04X} CCR=${cpu.ccr:02X}")

    # Adım adım çalıştır
    for _ in range(10): # En fazla 10 adım
        if cpu.halted:
            break
        print(f"\nAdım öncesi: PC=${cpu.pc:04X}")
        cpu.step()
        print(f"Adım sonrası: PC=${cpu.pc:04X} A=${cpu.acc_a:02X} B=${cpu.acc_b:02X} X=${cpu.ix:04X} SP=${cpu.sp:04X} CCR=${cpu.ccr:02X}")
        print(f"Bellek[$0030]: ${cpu.memory[0x0030]:02X}")

    # Veya cpu.run() ile tamamını çalıştır
    # cpu.run()
    # print(f"Son Durum: PC=${cpu.pc:04X} A=${cpu.acc_a:02X} B=${cpu.acc_b:02X} X=${cpu.ix:04X} SP=${cpu.sp:04X} CCR=${cpu.ccr:02X}")
    # print(f"Bellek[$0030]: ${cpu.memory[0x0030]:02X}")