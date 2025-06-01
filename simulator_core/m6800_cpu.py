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
        # CCR başlangıç değeri: İlk iki bit her zaman 1, I (Interrupt Mask) reset'te set edilir.
        self.ccr = 0xC0 | CCR_INTERRUPT

        # Bellek
        self.memory = bytearray(65536) # 64KB RAM

        # Simülasyon durumu
        self.halted = False
        self.cycles = 0 # Geçen çevrim sayısı

        # Opcode -> işleyici fonksiyon eşlemesi
        self.opcodes = {
            # Yükleme Komutları (Örnekler)
            0x86: self._ldaa_imm,  # LDAA Immediate
            0xB6: self._ldaa_ext,  # LDAA Extended
            0x96: self._ldaa_dir,  # LDAA Direct
            0xA6: self._ldaa_idx,  # LDAA Indexed
            0xC6: self._ldab_imm,  # LDAB Immediate (EKLENDİ)
            # ... diğer LDAB, LDX, LDS adresleme modları eklenecek ...

            # Saklama Komutları (Örnekler)
            0x97: self._staa_dir,  # STAA Direct
            0xB7: self._staa_ext,  # STAA Extended
            0xA7: self._staa_idx,  # STAA Indexed
            0xD7: self._stab_dir,  # STAB Direct (EKLENDİ)
            # ... diğer STAB, STX, STS adresleme modları eklenecek ...

            # Aritmetik Komutlar (Örnekler)
            0x8B: self._adda_imm,  # ADDA Immediate
            0xBB: self._adda_ext,  # ADDA Extended (Zaten vardı, CCR güncellenecek)
            0xCB: self._addb_imm,  # ADDB Immediate (EKLENDİ)
            0x80: self._suba_imm,  # SUBA Immediate (EKLENDİ)
            0xC0: self._subb_imm,  # SUBB Immediate (EKLENDİ)
            # ... diğer ADDA, ADDB, SUBA, SUBB, ADCA, ADCB, SBCA, SBCB adresleme modları ...

            # Artırma/Azaltma Komutları (Örnekler)
            0x4C: self._inca,      # INCA (EKLENDİ)
            0x5C: self._incb,      # INCB (EKLENDİ)
            0x4A: self._deca,      # DECA (EKLENDİ)
            0x5A: self._decb,      # DECB (EKLENDİ)
            # ... INC, DEC (bellek), INX, DEX, INS, DES ...

            # Mantıksal Komutlar (Örnekler)
            0x84: self._anda_imm,  # ANDA Immediate (EKLENDİ)
            0x8A: self._oraa_imm,  # ORAA Immediate (EKLENDİ)
            0x88: self._eora_imm,  # EORA Immediate (EKLENDİ)
            # ... diğer AND, ORA, EOR, BIT, COM, NEG ...

            # Karşılaştırma Komutları (Örnekler)
            0x81: self._cmpa_imm,  # CMPA Immediate (EKLENDİ)
            0x11: self._cba,       # CBA (EKLENDİ)
            # ... diğer CMPA, CMPB, CPX ...

            # Dallanma ve Atlama Komutları (Örnekler)
            0x20: self._bra,       # BRA (EKLENDİ)
            0x27: self._beq,       # BEQ (EKLENDİ)
            0x26: self._bne,       # BNE (EKLENDİ)
            0x7E: self._jmp_ext,   # JMP Extended (EKLENDİ)
            # ... diğer dallanma komutları (BCC, BCS, BMI, BPL vb.) ve JMP/JSR modları ...

            # Stack İşlemleri (Örnekler)
            0x36: self._psha,      # PSHA (EKLENDİ)
            0x32: self._pula,      # PULA (EKLENDİ)
            # ... PSHB, PULB, TSX, TXS, LDS, STS ...

            # CCR İşlemleri (Örnekler)
            0x0C: self._clc,       # CLC (EKLENDİ)
            0x0D: self._sec,       # SEC (EKLENDİ)
            0x0E: self._cli,       # CLI (EKLENDİ)
            0x0F: self._sei,       # SEI (EKLENDİ)
            # ... CLV, SEV, TAP, TPA ...

            # Diğer Komutlar
            0x01: self._nop,       # NOP (Zaten vardı)
            0x3F: self._swi,       # SWI (Zaten vardı)
            # ... RTI, RTS, WAI, DAA, TAB, TBA, TSTA, TSTB, TST ...
        }

    # --- CCR Güncelleme Yardımcı Metotları ---
    def _set_ccr_flag(self, flag_mask, condition):
        """Belirtilen bayrağı koşula göre set eder veya temizler."""
        if condition:
            self.ccr |= flag_mask
        else:
            self.ccr &= ~flag_mask
        self.ccr |= 0xC0 # CCR'nin ilk iki biti her zaman 1 olmalı.

    def _update_ccr_nz(self, value, byte_size=1):
        """Verilen değere göre N ve Z bayraklarını günceller."""
        if byte_size == 1: # 8-bit
            is_zero = (value == 0)
            is_negative = (value & 0x80) != 0
        else: # 16-bit (örn: LDX, CPX)
            is_zero = (value == 0)
            is_negative = (value & 0x8000) != 0

        self._set_ccr_flag(CCR_ZERO, is_zero)
        self._set_ccr_flag(CCR_NEGATIVE, is_negative)

    def _update_ccr_v_add(self, operand1, operand2, result_byte):
        """8-bit toplama (operand1 + operand2 = result_byte) sonrası Overflow (V) bayrağını günceller."""
        op1_msb = (operand1 & 0x80) != 0
        op2_msb = (operand2 & 0x80) != 0
        res_msb = (result_byte & 0x80) != 0
        overflow = (not op1_msb and not op2_msb and res_msb) or \
                   (op1_msb and op2_msb and not res_msb)
        self._set_ccr_flag(CCR_OVERFLOW, overflow)

    def _update_ccr_v_sub(self, operand1, operand2, result_byte):
        """8-bit çıkarma (operand1 - operand2 = result_byte) sonrası Overflow (V) bayrağını günceller."""
        op1_msb = (operand1 & 0x80) != 0
        op2_msb = (operand2 & 0x80) != 0
        res_msb = (result_byte & 0x80) != 0
        overflow = (op1_msb and not op2_msb and not res_msb) or \
                   (not op1_msb and op2_msb and res_msb)
        self._set_ccr_flag(CCR_OVERFLOW, overflow)

    def _update_ccr_c_add(self, result_wider_than_byte):
        """Toplama sonrası Carry bayrağını günceller (8-bit işlemler için)."""
        self._set_ccr_flag(CCR_CARRY, result_wider_than_byte > 0xFF)

    def _update_ccr_c_sub(self, operand1_byte, operand2_byte):
        """Çıkarma (operand1 - operand2) sonrası Carry (Borrow) bayrağını günceller."""
        self._set_ccr_flag(CCR_CARRY, operand2_byte > operand1_byte)

    def _update_ccr_h_add(self, operand1_byte, operand2_byte):
        """Toplama sonrası Half-Carry bayrağını günceller."""
        h_set = ((operand1_byte & 0x0F) + (operand2_byte & 0x0F)) > 0x0F
        self._set_ccr_flag(CCR_HALF_CARRY, h_set)

    def _update_ccr_h_sub(self, operand1_byte, operand2_byte):
        """Çıkarma sonrası Half-Carry (Half-Borrow) bayrağını günceller."""
        h_set = (operand1_byte & 0x0F) < (operand2_byte & 0x0F)
        self._set_ccr_flag(CCR_HALF_CARRY, h_set)
    # --- CCR Güncelleme Yardımcı Metotları SONU ---

    # --- Bellek Erişim Metotları ---
    def read_byte(self, address):
        self.cycles += 1 # Basit çevrim sayacı
        return self.memory[address & 0xFFFF]

    def write_byte(self, address, value):
        self.cycles += 1
        self.memory[address & 0xFFFF] = value & 0xFF

    def read_word(self, address):
        high_byte = self.read_byte(address)
        low_byte = self.read_byte((address + 1) & 0xFFFF)
        return (high_byte << 8) | low_byte

    def write_word(self, address, value):
        high_byte = (value >> 8) & 0xFF
        low_byte = value & 0xFF
        self.write_byte(address, high_byte)
        self.write_byte((address + 1) & 0xFFFF, low_byte)
    # --- Bellek Erişim Metotları SONU ---

    # --- Stack İşlemleri için Yardımcı Metotlar ---
    def _push_byte(self, value):
        self.write_byte(self.sp, value)
        self.sp = (self.sp - 1) & 0xFFFF

    def _pull_byte(self):
        self.sp = (self.sp + 1) & 0xFFFF
        return self.read_byte(self.sp)

    def _push_word(self, value):
        # SP önce azalır, sonra yazılır. Önce düşük byte (SP), sonra yüksek byte (SP-1).
        # M6800 stack'e yüksek byte'ı düşük adrese (SP'nin yeni değerine daha yakın) yazar.
        self._push_byte(value & 0xFF)       # Düşük byte'ı SP'ye yaz, SP--
        self._push_byte((value >> 8) & 0xFF)# Yüksek byte'ı SP'ye yaz, SP--

    def _pull_word(self):
        # Önce yüksek byte (SP+1), sonra düşük byte (SP+2). SP sonra artar.
        high_byte = self._pull_byte() # SP++, SP'den oku
        low_byte = self._pull_byte()  # SP++, SP'den oku
        return (high_byte << 8) | low_byte
    # --- Stack İşlemleri için Yardımcı Metotlar SONU ---


    # --- Program Yükleme ve Reset ---
    def load_memory(self, segments):
        self.memory = bytearray(65536)
        for address, data_bytes in segments:
            for i, byte_val in enumerate(data_bytes):
                self.write_byte(address + i, byte_val)
        # print(f"Simülatör: Program belleğe yüklendi. {len(segments)} segment.") # GUI'de gösteriliyor

    def reset(self):
        # Reset vektöründen PC'yi yükle
        # Gerçek bir sistemde, eğer 0xFFFE/FFFF okunamazsa veya hatalıysa tanımsız davranış olur.
        # Simülatörde varsayılan bir PC atayabiliriz veya hata verebiliriz.
        try:
            self.pc = self.read_word(0xFFFE)
        except IndexError: # Bellek sınırları dışında bir okuma denemesi (nadir)
            print("Uyarı: Reset vektörü (0xFFFE) okunamadı. PC varsayılana (0xC000) ayarlandı.")
            self.pc = 0xC000 # Güvenli bir varsayılan
            
        # SP genellikle RAM'in sonuna yakın bir yere ayarlanır, ancak bu programcıya bağlıdır.
        # Simülatör için mantıklı bir varsayılan belirleyebiliriz.
        self.sp = 0x01FF # Örnek bir stack başlangıcı (örn: $0000-$01FF arası sayfa 0 RAM)
        self.acc_a = 0x00
        self.acc_b = 0x00
        self.ix = 0x0000
        self.ccr = 0xC0 | CCR_INTERRUPT # I bayrağı reset'te set edilir
        self.halted = False
        self.cycles = 0
        # print(f"Simülatör: CPU resetlendi. PC = ${self.pc:04X}, SP = ${self.sp:04X}")

    # --- Komut Çekme ve Çalıştırma ---
    def fetch_byte(self):
        value = self.read_byte(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        return value

    def fetch_word(self):
        value = self.read_word(self.pc)
        self.pc = (self.pc + 2) & 0xFFFF
        return value

    def step(self):
        if self.halted:
            return False

        current_pc_before_fetch = self.pc # Hata ayıklama için
        opcode = self.fetch_byte()
        self.cycles += 1 # Opcode fetch için temel çevrim

        if opcode in self.opcodes:
            handler = self.opcodes[opcode]
            # print(f"DEBUG: PC=${current_pc_before_fetch:04X}, Opcode=${opcode:02X} ({handler.__name__})") # Debug
            handler()
            return True
        else:
            print(f"Simülatör: Bilinmeyen Opcode ${opcode:02X} @ ${current_pc_before_fetch:04X}")
            self.halted = True
            return False
    # --- Komut Çekme ve Çalıştırma SONU ---

    # --- KOMUT İŞLEYİCİLERİ ---
    def _nop(self): # Opcode 0x01
        # CCR etkilenmez
        pass

    def _swi(self): # Opcode 0x3F
        # SWI, tüm registerları stack'e atar, I'yı set eder ve SWI vektörüne ($FFFA/$FFFB) atlar.
        # Şimdilik simülasyonu durduralım.
        # Gerçek implementasyon:
        # self._push_word(self.pc)    # PC (sonraki komutun adresi)
        # self._push_word(self.ix)
        # self._push_byte(self.acc_a)
        # self._push_byte(self.acc_b)
        # self._push_byte(self.ccr)
        # self._set_ccr_flag(CCR_INTERRUPT, True) # I = 1
        # self.pc = self.read_word(0xFFFA)
        print(f"Simülatör: SWI komutu @ ${self.pc-1:04X}. CPU durduruluyor (basit mod).")
        self.halted = True

    # --- Yükleme Komutları ---
    def _ldaa_imm(self): # Opcode 0x86
        operand = self.fetch_byte()
        self.acc_a = operand
        self._update_ccr_nz(self.acc_a)
        self._set_ccr_flag(CCR_OVERFLOW, False) # V = 0
        # H, I, C etkilenmez

    def _ldaa_ext(self): # Opcode 0xB6
        address = self.fetch_word()
        self.acc_a = self.read_byte(address)
        self._update_ccr_nz(self.acc_a)
        self._set_ccr_flag(CCR_OVERFLOW, False) # V = 0

    def _ldaa_dir(self): # Opcode 0x96
        address_offset = self.fetch_byte()
        self.acc_a = self.read_byte(address_offset) # Direct adres 0-255
        self._update_ccr_nz(self.acc_a)
        self._set_ccr_flag(CCR_OVERFLOW, False) # V = 0
        
    def _ldaa_idx(self): # Opcode 0xA6
        offset = self.fetch_byte() # 8-bit işaretsiz offset
        effective_address = (self.ix + offset) & 0xFFFF
        self.acc_a = self.read_byte(effective_address)
        self._update_ccr_nz(self.acc_a)
        self._set_ccr_flag(CCR_OVERFLOW, False) # V = 0

    def _ldab_imm(self): # Opcode 0xC6
        operand = self.fetch_byte()
        self.acc_b = operand
        self._update_ccr_nz(self.acc_b)
        self._set_ccr_flag(CCR_OVERFLOW, False) # V = 0

    # --- Saklama Komutları ---
    def _staa_dir(self): # Opcode 0x97
        address_offset = self.fetch_byte()
        self.write_byte(address_offset, self.acc_a)
        self._update_ccr_nz(self.acc_a) # N,Z saklanan değere göre
        self._set_ccr_flag(CCR_OVERFLOW, False) # V = 0

    def _staa_ext(self): # Opcode 0xB7
        address = self.fetch_word()
        self.write_byte(address, self.acc_a)
        self._update_ccr_nz(self.acc_a)
        self._set_ccr_flag(CCR_OVERFLOW, False)

    def _staa_idx(self): # Opcode 0xA7
        offset = self.fetch_byte()
        effective_address = (self.ix + offset) & 0xFFFF
        self.write_byte(effective_address, self.acc_a)
        self._update_ccr_nz(self.acc_a)
        self._set_ccr_flag(CCR_OVERFLOW, False)

    def _stab_dir(self): # Opcode 0xD7
        address_offset = self.fetch_byte()
        self.write_byte(address_offset, self.acc_b)
        self._update_ccr_nz(self.acc_b)
        self._set_ccr_flag(CCR_OVERFLOW, False)

    # --- Aritmetik Komutlar ---
    def _adda_imm(self): # Opcode 0x8B
        operand = self.fetch_byte()
        acc_before = self.acc_a
        result_wider = acc_before + operand
        self.acc_a = result_wider & 0xFF
        self._update_ccr_h_add(acc_before, operand)
        self._update_ccr_nz(self.acc_a)
        self._update_ccr_v_add(acc_before, operand, self.acc_a)
        self._update_ccr_c_add(result_wider)

    def _adda_ext(self): # Opcode 0xBB
        address = self.fetch_word()
        operand = self.read_byte(address)
        acc_before = self.acc_a
        result_wider = acc_before + operand
        self.acc_a = result_wider & 0xFF
        self._update_ccr_h_add(acc_before, operand)
        self._update_ccr_nz(self.acc_a)
        self._update_ccr_v_add(acc_before, operand, self.acc_a)
        self._update_ccr_c_add(result_wider)

    def _addb_imm(self): # Opcode 0xCB
        operand = self.fetch_byte()
        acc_before = self.acc_b
        result_wider = acc_before + operand
        self.acc_b = result_wider & 0xFF
        self._update_ccr_h_add(acc_before, operand)
        self._update_ccr_nz(self.acc_b)
        self._update_ccr_v_add(acc_before, operand, self.acc_b)
        self._update_ccr_c_add(result_wider)

    def _suba_imm(self): # Opcode 0x80
        operand = self.fetch_byte()
        acc_before = self.acc_a
        result_byte = (acc_before - operand) & 0xFF
        self._update_ccr_h_sub(acc_before, operand)
        self._update_ccr_nz(result_byte)
        self._update_ccr_v_sub(acc_before, operand, result_byte)
        self._update_ccr_c_sub(acc_before, operand)
        self.acc_a = result_byte

    def _subb_imm(self): # Opcode 0xC0
        operand = self.fetch_byte()
        acc_before = self.acc_b
        result_byte = (acc_before - operand) & 0xFF
        self._update_ccr_h_sub(acc_before, operand)
        self._update_ccr_nz(result_byte)
        self._update_ccr_v_sub(acc_before, operand, result_byte)
        self._update_ccr_c_sub(acc_before, operand)
        self.acc_b = result_byte

    # --- Artırma/Azaltma Komutları ---
    def _inca(self): # Opcode 0x4C
        acc_before = self.acc_a
        self.acc_a = (acc_before + 1) & 0xFF
        self._update_ccr_nz(self.acc_a)
        v_set = (acc_before == 0x7F) # V=1 if $7F -> $80
        self._set_ccr_flag(CCR_OVERFLOW, v_set)
        # C bayrağı etkilenmez

    def _incb(self): # Opcode 0x5C
        acc_before = self.acc_b
        self.acc_b = (acc_before + 1) & 0xFF
        self._update_ccr_nz(self.acc_b)
        v_set = (acc_before == 0x7F)
        self._set_ccr_flag(CCR_OVERFLOW, v_set)
        # C bayrağı etkilenmez

    def _deca(self): # Opcode 0x4A
        acc_before = self.acc_a
        self.acc_a = (acc_before - 1) & 0xFF
        self._update_ccr_nz(self.acc_a)
        v_set = (acc_before == 0x80) # V=1 if $80 -> $7F (signed overflow)
        self._set_ccr_flag(CCR_OVERFLOW, v_set)
        # C bayrağı etkilenmez

    def _decb(self): # Opcode 0x5A
        acc_before = self.acc_b
        self.acc_b = (acc_before - 1) & 0xFF
        self._update_ccr_nz(self.acc_b)
        v_set = (acc_before == 0x80)
        self._set_ccr_flag(CCR_OVERFLOW, v_set)
        # C bayrağı etkilenmez

    # --- Mantıksal Komutlar ---
    def _common_logical_op(self, acc_value, operand):
        # Bu _anda_imm, _oraa_imm, _eora_imm için ortak CCR güncellemesi
        self._update_ccr_nz(acc_value)
        self._set_ccr_flag(CCR_OVERFLOW, False) # V = 0
        # H, I, C etkilenmez

    def _anda_imm(self): # Opcode 0x84
        operand = self.fetch_byte()
        self.acc_a &= operand
        self._common_logical_op(self.acc_a, operand)

    def _oraa_imm(self): # Opcode 0x8A
        operand = self.fetch_byte()
        self.acc_a |= operand
        self._common_logical_op(self.acc_a, operand)

    def _eora_imm(self): # Opcode 0x88
        operand = self.fetch_byte()
        self.acc_a ^= operand
        self._common_logical_op(self.acc_a, operand)

    # --- Karşılaştırma Komutları ---
    def _cmpa_imm(self): # Opcode 0x81 (A - M)
        operand = self.fetch_byte()
        # Karşılaştırma, çıkarma gibidir ama sonuç saklanmaz, sadece CCR etkilenir.
        acc_val = self.acc_a
        result_temp = (acc_val - operand) & 0xFF # Geçici sonuç
        
        # H, N, Z, V, C bayrakları çıkarma gibi etkilenir.
        self._update_ccr_h_sub(acc_val, operand)
        self._update_ccr_nz(result_temp)
        self._update_ccr_v_sub(acc_val, operand, result_temp)
        self._update_ccr_c_sub(acc_val, operand)

    def _cba(self): # Opcode 0x11 (A - B)
        # Akümülatör A'yı Akümülatör B ile karşılaştırır
        val_a = self.acc_a
        val_b = self.acc_b
        result_temp = (val_a - val_b) & 0xFF
        
        self._update_ccr_h_sub(val_a, val_b)
        self._update_ccr_nz(result_temp)
        self._update_ccr_v_sub(val_a, val_b, result_temp)
        self._update_ccr_c_sub(val_a, val_b)
        # I etkilenmez

    # --- Dallanma ve Atlama Komutları ---
    def _calculate_relative_addr(self):
        offset_signed = self.fetch_byte()
        # 8-bit offset'i işaretli sayıya çevir
        if offset_signed > 127: # Eğer 0x80-0xFF arasındaysa negatiftir
            offset_signed -= 256
        # Relative adres, dallanma komutunun bir sonraki byte'ından itibaren hesaplanır.
        # fetch_byte PC'yi zaten 1 artırdı, offset de okundu, PC şu an offset'in bir sonrası.
        # Yani PC, komutun (opcode + offset) hemen sonrasını gösteriyor.
        # Effective_address = (PC + offset_signed)
        return (self.pc + offset_signed) & 0xFFFF

    def _bra(self): # Opcode 0x20 (Branch Always)
        self.pc = self._calculate_relative_addr()
        # CCR etkilenmez

    def _beq(self): # Opcode 0x27 (Branch if Equal, Z=1)
        if (self.ccr & CCR_ZERO) != 0: # Z bayrağı set ise
            self.pc = self._calculate_relative_addr()
        else:
            self.pc = (self.pc + 1) & 0xFFFF # Sadece offset byte'ını atla
        # CCR etkilenmez

    def _bne(self): # Opcode 0x26 (Branch if Not Equal, Z=0)
        if (self.ccr & CCR_ZERO) == 0: # Z bayrağı clear ise
            self.pc = self._calculate_relative_addr()
        else:
            self.pc = (self.pc + 1) & 0xFFFF # Sadece offset byte'ını atla
        # CCR etkilenmez
        
    def _jmp_ext(self): # Opcode 0x7E
        self.pc = self.fetch_word() # PC yeni adrese set edilir
        # CCR etkilenmez

    # --- Stack İşlemleri ---
    def _psha(self): # Opcode 0x36
        self._push_byte(self.acc_a)
        # CCR etkilenmez

    def _pula(self): # Opcode 0x32
        self.acc_a = self._pull_byte()
        # CCR etkilenmez

    # --- CCR İşlemleri ---
    def _clc(self): # Opcode 0x0C (Clear Carry)
        self._set_ccr_flag(CCR_CARRY, False) # C = 0
        # Diğer bayraklar etkilenmez

    def _sec(self): # Opcode 0x0D (Set Carry)
        self._set_ccr_flag(CCR_CARRY, True) # C = 1
        # Diğer bayraklar etkilenmez

    def _cli(self): # Opcode 0x0E (Clear Interrupt Mask)
        self._set_ccr_flag(CCR_INTERRUPT, False) # I = 0
        # Diğer bayraklar etkilenmez

    def _sei(self): # Opcode 0x0F (Set Interrupt Mask)
        self._set_ccr_flag(CCR_INTERRUPT, True) # I = 1
        # Diğer bayraklar etkilenmez

    # --- KOMUT İŞLEYİCİLERİ SONU ---


if __name__ == '__main__':
    cpu = M6800CPU()
    
    # Test 1: LDAA #$10, ADDA #$F0 -> A=$00, C=1, H=0, Z=1, N=0, V=0
    #         86 10   8B F0
    print("--- Test 1: ADDA ve Bayraklar ---")
    test_program1 = [
        (0xC000, [0x86, 0x10, 0x8B, 0xF0, 0x3F]) # LDAA #$10, ADDA #$F0, SWI
    ]
    cpu.load_memory(test_program1)
    cpu.reset() # Reset sonrası PC, 0xFFFE/FFFF'deki değere (genelde $C000 test için) veya varsayılana ayarlanır.
    cpu.pc = 0xC000 # Test için PC'yi manuel ayarla
    
    print(f"Başlangıç: PC=${cpu.pc:04X} A=${cpu.acc_a:02X} CCR=${cpu.ccr:02X}")
    cpu.step() # LDAA #$10
    print(f"LDAA sonrası: PC=${cpu.pc:04X} A=${cpu.acc_a:02X} CCR=${cpu.ccr:02X}")
    cpu.step() # ADDA #$F0
    print(f"ADDA sonrası: PC=${cpu.pc:04X} A=${cpu.acc_a:02X} CCR=${cpu.ccr:02X} (HINZVC: {cpu.ccr&0x20>>5}{cpu.ccr&0x10>>4}{cpu.ccr&0x08>>3}{cpu.ccr&0x04>>2}{cpu.ccr&0x02>>1}{cpu.ccr&0x01})")
    # Beklenen CCR: $10 + $F0 = $100. A = $00. C=1, Z=1.
    # H: (0+0)>F? Hayır. (0x10 & 0x0F) = 0, (0xF0 & 0x0F) = 0. 0+0=0. H=0.
    # V: op1_msb=0, op2_msb=1. Toplamanın V'si: (0&1&!0) || (1&0&1) = 0. V=0.
    # N: A=$00 olduğu için N=0.
    # Sonuç CCR: $C0 | C | Z = $C0 | $01 | $04 = $C5 olmalı (eğer I=0 ise $C4). Reset'te I=1.
    # $C0 (11000000) | I (00010000) = $D0. $D0 | C | Z = $D0 | $01 | $04 = $D5

    # Test 2: SUBA ve Bayraklar
    # LDAA #$05, SUBA #$0A -> A=$FB, C(borrow)=1, H(borrow)=1, N=1, Z=0, V=0
    #         86 05   80 0A
    print("\n--- Test 2: SUBA ve Bayraklar ---")
    test_program2 = [
        (0xC010, [0x86, 0x05, 0x80, 0x0A, 0x3F]) # LDAA #$05, SUBA #$0A, SWI
    ]
    cpu.load_memory(test_program2) # Yeni programı yükle
    cpu.reset()
    cpu.pc = 0xC010

    print(f"Başlangıç: PC=${cpu.pc:04X} A=${cpu.acc_a:02X} CCR=${cpu.ccr:02X}")
    cpu.step() # LDAA #$05
    print(f"LDAA sonrası: PC=${cpu.pc:04X} A=${cpu.acc_a:02X} CCR=${cpu.ccr:02X}")
    cpu.step() # SUBA #$0A
    print(f"SUBA sonrası: PC=${cpu.pc:04X} A=${cpu.acc_a:02X} CCR=${cpu.ccr:02X} (HINZVC: {cpu.ccr&0x20>>5}{cpu.ccr&0x10>>4}{cpu.ccr&0x08>>3}{cpu.ccr&0x04>>2}{cpu.ccr&0x02>>1}{cpu.ccr&0x01})")
    # Beklenen: A=$FB. $05 - $0A.
    # H_sub: (5&F=5) < (A&F=A) ? Evet. H=1.
    # N: $FB (11111011) -> N=1.
    # Z: $FB != 0 -> Z=0.
    # V_sub: op1_msb=0, op2_msb=0, res_msb=1. (0&!0&!1) || (!0&0&1) = 0. V=0.
    # C_sub: op2(A) > op1(5) ? Evet. C=1.
    # Sonuç CCR: $C0 | I | H | N | C = $D0 | $20 | $08 | $01 = $F9

    # Test 3: INCA
    # LDAA #$7F, INCA -> A=$80, V=1, N=1, Z=0
    #         86 7F   4C
    print("\n--- Test 3: INCA ve Bayraklar ---")
    test_program3 = [
        (0xC020, [0x86, 0x7F, 0x4C, 0x3F]) # LDAA #$7F, INCA, SWI
    ]
    cpu.load_memory(test_program3)
    cpu.reset()
    cpu.pc = 0xC020
    cpu.step() # LDAA
    cpu.step() # INCA
    print(f"INCA sonrası: PC=${cpu.pc:04X} A=${cpu.acc_a:02X} CCR=${cpu.ccr:02X} (HINZVC: {cpu.ccr&0x20>>5}{cpu.ccr&0x10>>4}{cpu.ccr&0x08>>3}{cpu.ccr&0x04>>2}{cpu.ccr&0x02>>1}{cpu.ccr&0x01})")
    # Beklenen: A=$80.
    # N: $80 -> N=1.
    # Z: $80 != 0 -> Z=0.
    # V: acc_before ($7F) == $7F ? Evet. V=1.
    # C etkilenmez. H etkilenmez.
    # Sonuç CCR: $C0 | I | N | V = $D0 | $08 | $02 = $DA