# m6800_opcodes.py

# Adresleme modları için sabitler (okunurluk için)
ADDR_MODE_IMMEDIATE = "IMM"
ADDR_MODE_DIRECT = "DIR"
ADDR_MODE_EXTENDED = "EXT"
ADDR_MODE_INDEXED = "IND"
ADDR_MODE_RELATIVE = "REL"
ADDR_MODE_INHERENT = "INH" # Hem operand almayanlar hem de A, B acc. adresleme için

PSEUDO_OPS = {"ORG", "EQU", "FCB", "FDB", "FCC", "END", "RMB"}

OPCODE_TABLE = {
    # Table 2'den başlayarak: Accumulator and Memory Operations
    "ADDA": {
        ADDR_MODE_IMMEDIATE: ("8B", 2, None), # OP: 8B, #: 2
        ADDR_MODE_DIRECT:    ("9B", 2, None), # OP: 9B, #: 2
        ADDR_MODE_INDEXED:   ("AB", 2, None), # OP: AB, #: 2
        ADDR_MODE_EXTENDED:  ("BB", 3, None)  # OP: BB, #: 3
    },
    "ADDB": {
        ADDR_MODE_IMMEDIATE: ("CB", 2, None), # OP: CB, #: 2
        ADDR_MODE_DIRECT:    ("DB", 2, None), # OP: DB, #: 2
        ADDR_MODE_INDEXED:   ("EB", 2, None), # OP: EB, #: 2
        ADDR_MODE_EXTENDED:  ("FB", 3, None)  # OP: FB, #: 3
    },
    "ABA":  { # Implied
        ADDR_MODE_INHERENT:  ("1B", 1, None)  # OP: 1B, #: 1
    },
    "ADCA": {
        ADDR_MODE_IMMEDIATE: ("89", 2, None),
        ADDR_MODE_DIRECT:    ("99", 2, None),
        ADDR_MODE_INDEXED:   ("A9", 2, None),
        ADDR_MODE_EXTENDED:  ("B9", 3, None)
    },
    "ADCB": {
        ADDR_MODE_IMMEDIATE: ("C9", 2, None),
        ADDR_MODE_DIRECT:    ("D9", 2, None),
        ADDR_MODE_INDEXED:   ("E9", 2, None),
        ADDR_MODE_EXTENDED:  ("F9", 3, None)
    },
    "ANDA": {
        ADDR_MODE_IMMEDIATE: ("84", 2, None),
        ADDR_MODE_DIRECT:    ("94", 2, None),
        ADDR_MODE_INDEXED:   ("A4", 2, None),
        ADDR_MODE_EXTENDED:  ("B4", 3, None)
    },
    "ANDB": {
        ADDR_MODE_IMMEDIATE: ("C4", 2, None),
        ADDR_MODE_DIRECT:    ("D4", 2, None),
        ADDR_MODE_INDEXED:   ("E4", 2, None),
        ADDR_MODE_EXTENDED:  ("F4", 3, None)
    },
    "BITA": {
        ADDR_MODE_IMMEDIATE: ("85", 2, None),
        ADDR_MODE_DIRECT:    ("95", 2, None),
        ADDR_MODE_INDEXED:   ("A5", 2, None),
        ADDR_MODE_EXTENDED:  ("B5", 3, None)
    },
    "BITB": {
        ADDR_MODE_IMMEDIATE: ("C5", 2, None),
        ADDR_MODE_DIRECT:    ("D5", 2, None),
        ADDR_MODE_INDEXED:   ("E5", 2, None),
        ADDR_MODE_EXTENDED:  ("F5", 3, None)
    },
    "CLR":  { # Memory operand
        ADDR_MODE_INDEXED:   ("6F", 2, None), # **** OP: 6F, #: 2 (Table 2'de # 7 diyor ama bu çevrim sayısı olmalı, byte sayısı 2'dir)
        ADDR_MODE_EXTENDED:  ("7F", 3, None)  # ****OP: 7F, #: 3 (Table 2'de # 6 diyor ama bu çevrim sayısı olmalı, byte sayısı 3'tür)
    },
    "CLRA": { # Implied
        ADDR_MODE_INHERENT:  ("4F", 1, None)
    },
    "CLRB": { # Implied
        ADDR_MODE_INHERENT:  ("5F", 1, None)
    },
    "CMPA": {
        ADDR_MODE_IMMEDIATE: ("81", 2, None),
        ADDR_MODE_DIRECT:    ("91", 2, None),
        ADDR_MODE_INDEXED:   ("A1", 2, None),
        ADDR_MODE_EXTENDED:  ("B1", 3, None)
    },
    "CMPB": {
        ADDR_MODE_IMMEDIATE: ("C1", 2, None),
        ADDR_MODE_DIRECT:    ("D1", 2, None),
        ADDR_MODE_INDEXED:   ("E1", 2, None),
        ADDR_MODE_EXTENDED:  ("F1", 3, None)
    },
    "CBA":  { # Implied
        ADDR_MODE_INHERENT:  ("11", 1, None)
    },
    "COM":  { # Memory operand
        ADDR_MODE_INDEXED:   ("63", 2, None), # Çevrim:7, Byte:2
        ADDR_MODE_EXTENDED:  ("73", 3, None)  # Çevrim:6, Byte:3
    },
    "COMA": { # Implied
        ADDR_MODE_INHERENT:  ("43", 1, None)
    },
    "COMB": { # Implied
        ADDR_MODE_INHERENT:  ("53", 1, None)
    },
    "NEG":  { # Memory operand
        ADDR_MODE_INDEXED:   ("60", 2, None), # Çevrim:7, Byte:2
        ADDR_MODE_EXTENDED:  ("70", 3, None)  # Çevrim:6, Byte:3
    },
    "NEGA": { # Implied
        ADDR_MODE_INHERENT:  ("40", 1, None)
    },
    "NEGB": { # Implied
        ADDR_MODE_INHERENT:  ("50", 1, None)
    },
    "DAA":  { # Implied
        ADDR_MODE_INHERENT:  ("19", 1, None)
    },
    "DEC":  { # Memory operand
        ADDR_MODE_INDEXED:   ("6A", 2, None), # Çevrim:7, Byte:2
        ADDR_MODE_EXTENDED:  ("7A", 3, None)  # Çevrim:6, Byte:3
    },
    "DECA": { # Implied
        ADDR_MODE_INHERENT:  ("4A", 1, None)
    },
    "DECB": { # Implied
        ADDR_MODE_INHERENT:  ("5A", 1, None)
    },
    "EORA": {
        ADDR_MODE_IMMEDIATE: ("88", 2, None),
        ADDR_MODE_DIRECT:    ("98", 2, None),
        ADDR_MODE_INDEXED:   ("A8", 2, None),
        ADDR_MODE_EXTENDED:  ("B8", 3, None)
    },
    "EORB": {
        ADDR_MODE_IMMEDIATE: ("C8", 2, None),
        ADDR_MODE_DIRECT:    ("D8", 2, None),
        ADDR_MODE_INDEXED:   ("E8", 2, None),
        ADDR_MODE_EXTENDED:  ("F8", 3, None)
    },
    "INC":  { # Memory operand
        ADDR_MODE_INDEXED:   ("6C", 2, None), # Çevrim:7, Byte:2
        ADDR_MODE_EXTENDED:  ("7C", 3, None)  # Çevrim:6, Byte:3
    },
    "INCA": { # Implied
        ADDR_MODE_INHERENT:  ("4C", 1, None)
    },
    "INCB": { # Implied
        ADDR_MODE_INHERENT:  ("5C", 1, None)
    },
    "LDAA": {
        ADDR_MODE_IMMEDIATE: ("86", 2, None),
        ADDR_MODE_DIRECT:    ("96", 2, None),
        ADDR_MODE_INDEXED:   ("A6", 2, None),
        ADDR_MODE_EXTENDED:  ("B6", 3, None)
    },
    "LDAB": {
        ADDR_MODE_IMMEDIATE: ("C6", 2, None),
        ADDR_MODE_DIRECT:    ("D6", 2, None),
        ADDR_MODE_INDEXED:   ("E6", 2, None),
        ADDR_MODE_EXTENDED:  ("F6", 3, None)
    },
    "ORAA": {
        ADDR_MODE_IMMEDIATE: ("8A", 2, None),
        ADDR_MODE_DIRECT:    ("9A", 2, None),
        ADDR_MODE_INDEXED:   ("AA", 2, None),
        ADDR_MODE_EXTENDED:  ("BA", 3, None)
    },
    "ORAB": {
        ADDR_MODE_IMMEDIATE: ("CA", 2, None),
        ADDR_MODE_DIRECT:    ("DA", 2, None),
        ADDR_MODE_INDEXED:   ("EA", 2, None),
        ADDR_MODE_EXTENDED:  ("FA", 3, None)
    },
    "PSHA": { # Implied
        ADDR_MODE_INHERENT:  ("36", 1, None) # Byte:1 (Çevrim 4)
    },
    "PSHB": { # Implied
        ADDR_MODE_INHERENT:  ("37", 1, None) # Byte:1 (Çevrim 4)
    },
    "PULA": { # Implied
        ADDR_MODE_INHERENT:  ("32", 1, None) # Byte:1 (Çevrim 4)
    },
    "PULB": { # Implied
        ADDR_MODE_INHERENT:  ("33", 1, None) # Byte:1 (Çevrim 4)
    },
    "ROL":  { # Memory operand
        ADDR_MODE_INDEXED:   ("69", 2, None), # Çevrim:7, Byte:2
        ADDR_MODE_EXTENDED:  ("79", 3, None)  # Çevrim:6, Byte:3
    },
    "ROLA": { # Implied
        ADDR_MODE_INHERENT:  ("49", 1, None)
    },
    "ROLB": { # Implied
        ADDR_MODE_INHERENT:  ("59", 1, None)
    },
    "ROR":  { # Memory operand
        ADDR_MODE_INDEXED:   ("66", 2, None), # Çevrim:7, Byte:2
        ADDR_MODE_EXTENDED:  ("76", 3, None)  # Çevrim:6, Byte:3
    },
    "RORA": { # Implied
        ADDR_MODE_INHERENT:  ("46", 1, None)
    },
    "RORB": { # Implied
        ADDR_MODE_INHERENT:  ("56", 1, None)
    },
    "ASL":  { # Memory operand (Arithmetic Shift Left)
        ADDR_MODE_INDEXED:   ("68", 2, None), # OP: 68 (Table 1'de 78 gibi görünüyor ama Table 2'de 68) -> Table 2'yi esas alalım
        ADDR_MODE_EXTENDED:  ("78", 3, None)  # OP: 78
    },
    "ASLA": { # Implied
        ADDR_MODE_INHERENT:  ("48", 1, None)
    },
    "ASLB": { # Implied
        ADDR_MODE_INHERENT:  ("58", 1, None)
    },
    "ASR":  { # Memory operand (Arithmetic Shift Right)
        ADDR_MODE_INDEXED:   ("67", 2, None), # Çevrim:7, Byte:2
        ADDR_MODE_EXTENDED:  ("77", 3, None)  # Çevrim:6, Byte:3
    },
    "ASRA": { # Implied
        ADDR_MODE_INHERENT:  ("47", 1, None)
    },
    "ASRB": { # Implied
        ADDR_MODE_INHERENT:  ("57", 1, None)
    },
    "LSR":  { # Memory operand (Logical Shift Right)
        ADDR_MODE_INDEXED:   ("64", 2, None), # Çevrim:7, Byte:2
        ADDR_MODE_EXTENDED:  ("74", 3, None)  # Çevrim:6, Byte:3
    },
    "LSRA": { # Implied
        ADDR_MODE_INHERENT:  ("44", 1, None)
    },
    "LSRB": { # Implied
        ADDR_MODE_INHERENT:  ("54", 1, None)
    },
    "STAA": { # Memory operand
        ADDR_MODE_DIRECT:    ("97", 2, None),
        ADDR_MODE_INDEXED:   ("A7", 2, None), # Çevrim:6, Byte:2
        ADDR_MODE_EXTENDED:  ("B7", 3, None)  # Çevrim:5, Byte:3
    },
    "STAB": { # Memory operand
        ADDR_MODE_DIRECT:    ("D7", 2, None), # Table 1'de D7, Table 2'de 07 diyor. Table 1 (D7) daha mantıklı.
        ADDR_MODE_INDEXED:   ("E7", 2, None), # Çevrim:6, Byte:2
        ADDR_MODE_EXTENDED:  ("F7", 3, None)  # Çevrim:5, Byte:3
    },
    "SUBA": {
        ADDR_MODE_IMMEDIATE: ("80", 2, None),
        ADDR_MODE_DIRECT:    ("90", 2, None),
        ADDR_MODE_INDEXED:   ("A0", 2, None),
        ADDR_MODE_EXTENDED:  ("B0", 3, None)
    },
    "SUBB": {
        ADDR_MODE_IMMEDIATE: ("C0", 2, None),
        ADDR_MODE_DIRECT:    ("D0", 2, None),
        ADDR_MODE_INDEXED:   ("E0", 2, None),
        ADDR_MODE_EXTENDED:  ("F0", 3, None)
    },
    "SBA":  { # Implied
        ADDR_MODE_INHERENT:  ("10", 1, None)
    },
    "SBCA": { # Subtract with Carry
        ADDR_MODE_IMMEDIATE: ("82", 2, None),
        ADDR_MODE_DIRECT:    ("92", 2, None),
        ADDR_MODE_INDEXED:   ("A2", 2, None),
        ADDR_MODE_EXTENDED:  ("B2", 3, None)
    },
    "SBCB": {
        ADDR_MODE_IMMEDIATE: ("C2", 2, None),
        ADDR_MODE_DIRECT:    ("D2", 2, None),
        ADDR_MODE_INDEXED:   ("E2", 2, None),
        ADDR_MODE_EXTENDED:  ("F2", 3, None)
    },
    "TAB":  { # Implied
        ADDR_MODE_INHERENT:  ("16", 1, None)
    },
    "TBA":  { # Implied
        ADDR_MODE_INHERENT:  ("17", 1, None)
    },
    "TST":  { # Memory operand
        ADDR_MODE_INDEXED:   ("6D", 2, None), # Çevrim:7, Byte:2
        ADDR_MODE_EXTENDED:  ("7D", 3, None)  # Çevrim:6, Byte:3
    },
    "TSTA": { # Implied
        ADDR_MODE_INHERENT:  ("4D", 1, None)
    },
    "TSTB": { # Implied
        ADDR_MODE_INHERENT:  ("5D", 1, None)
    },

    # Table 3'ten: Index Register and Stack Pointer Operations
    "CPX":  { # Compare Index Register
        ADDR_MODE_IMMEDIATE: ("8C", 3, None), # OP: 8C, #: 3
        ADDR_MODE_DIRECT:    ("9C", 2, None), # OP: 9C, #: 2
        ADDR_MODE_INDEXED:   ("AC", 2, None), # OP: AC, #: 2
        ADDR_MODE_EXTENDED:  ("BC", 3, None)  # OP: BC, #: 3
    },
    "DEX":  { # Implied
        ADDR_MODE_INHERENT:  ("09", 1, None) # OP: 09, #: 1
    },
    "DES":  { # Implied
        ADDR_MODE_INHERENT:  ("34", 1, None) # OP: 34, #: 1
    },
    "INX":  { # Implied
        ADDR_MODE_INHERENT:  ("08", 1, None) # OP: 08, #: 1
    },
    "INS":  { # Implied
        ADDR_MODE_INHERENT:  ("31", 1, None) # OP: 31, #: 1
    },
    "LDX":  {
        ADDR_MODE_IMMEDIATE: ("CE", 3, None), # OP: CE, #: 3
        ADDR_MODE_DIRECT:    ("DE", 2, None), # OP: DE, #: 2
        ADDR_MODE_INDEXED:   ("EE", 2, None), # OP: EE, #: 2
        ADDR_MODE_EXTENDED:  ("FE", 3, None)  # OP: FE, #: 3
    },
    "LDS":  {
        ADDR_MODE_IMMEDIATE: ("8E", 3, None), # OP: 8E, #: 3
        ADDR_MODE_DIRECT:    ("9E", 2, None), # OP: 9E, #: 2
        ADDR_MODE_INDEXED:   ("AE", 2, None), # OP: AE, #: 2
        ADDR_MODE_EXTENDED:  ("BE", 3, None)  # OP: BE, #: 3
    },
    "STX":  { # Store Index Register
        ADDR_MODE_DIRECT:    ("DF", 2, None), # OP: DF, #: 2
        ADDR_MODE_INDEXED:   ("EF", 2, None), # OP: EF, #: 2
        ADDR_MODE_EXTENDED:  ("FF", 3, None)  # OP: FF, #: 3
    },
    "STS":  { # Store Stack Pointer
        ADDR_MODE_DIRECT:    ("9F", 2, None), # OP: 9F, #: 2
        ADDR_MODE_INDEXED:   ("AF", 2, None), # OP: AF, #: 2
        ADDR_MODE_EXTENDED:  ("BF", 3, None)  # OP: BF, #: 3
    },
    "TXS":  { # Implied
        ADDR_MODE_INHERENT:  ("35", 1, None) # OP: 35, #: 1
    },
    "TSX":  { # Implied
        ADDR_MODE_INHERENT:  ("30", 1, None) # OP: 30, #: 1
    },

    # Table 4'ten: Jump and Branch Operations
    "BRA":  { ADDR_MODE_RELATIVE: ("20", 2, None) }, # OP: 20, #: 2
    "BCC":  { ADDR_MODE_RELATIVE: ("24", 2, None) }, # AKA BLOS (Branch if LOwer or Same for unsigned)
    "BCS":  { ADDR_MODE_RELATIVE: ("25", 2, None) }, # AKA BHIS (Branch if HIgher or Same for unsigned)
    "BEQ":  { ADDR_MODE_RELATIVE: ("27", 2, None) },
    "BGE":  { ADDR_MODE_RELATIVE: ("2C", 2, None) },
    "BGT":  { ADDR_MODE_RELATIVE: ("2E", 2, None) },
    "BHI":  { ADDR_MODE_RELATIVE: ("22", 2, None) },
    "BLE":  { ADDR_MODE_RELATIVE: ("2F", 2, None) },
    "BLS":  { ADDR_MODE_RELATIVE: ("23", 2, None) }, # Table 4'te BLS, Table 1'de de 23
    "BLT":  { ADDR_MODE_RELATIVE: ("2D", 2, None) },
    "BMI":  { ADDR_MODE_RELATIVE: ("2B", 2, None) },
    "BNE":  { ADDR_MODE_RELATIVE: ("26", 2, None) },
    "BVC":  { ADDR_MODE_RELATIVE: ("28", 2, None) },
    "BVS":  { ADDR_MODE_RELATIVE: ("29", 2, None) },
    "BPL":  { ADDR_MODE_RELATIVE: ("2A", 2, None) },
    "BSR":  { ADDR_MODE_RELATIVE: ("8D", 2, None) }, # OP: 8D, #: 2
    "JMP":  {
        ADDR_MODE_INDEXED:   ("6E", 2, None), # OP: 6E, #: 2
        ADDR_MODE_EXTENDED:  ("7E", 3, None)  # OP: 7E, #: 3
    },
    "JSR":  {
        ADDR_MODE_INDEXED:   ("AD", 2, None), # OP: AD, #: 2
        ADDR_MODE_EXTENDED:  ("BD", 3, None)  # OP: BD, #: 3
    },
    "NOP":  { ADDR_MODE_INHERENT: ("01", 1, None) }, # OP: 01, #: 1
    "RTI":  { ADDR_MODE_INHERENT: ("3B", 1, None) }, # OP: 3B, #: 1
    "RTS":  { ADDR_MODE_INHERENT: ("39", 1, None) }, # OP: 39, #: 1
    "SWI":  { ADDR_MODE_INHERENT: ("3F", 1, None) }, # OP: 3F, #: 1
    "WAI":  { ADDR_MODE_INHERENT: ("3E", 1, None) }, # OP: 3E, #: 1

    # Table 5'ten: Condition Code Register Operations
    "CLC":  { ADDR_MODE_INHERENT: ("0C", 1, None) }, # OP: 0C, #: 1
    "CLI":  { ADDR_MODE_INHERENT: ("0E", 1, None) }, # OP: 0E, #: 1
    "CLV":  { ADDR_MODE_INHERENT: ("0A", 1, None) }, # OP: 0A, #: 1
    "SEC":  { ADDR_MODE_INHERENT: ("0D", 1, None) }, # OP: 0D, #: 1
    "SEI":  { ADDR_MODE_INHERENT: ("0F", 1, None) }, # OP: 0F, #: 1
    "SEV":  { ADDR_MODE_INHERENT: ("0B", 1, None) }, # OP: 0B, #: 1
    "TAP":  { ADDR_MODE_INHERENT: ("06", 1, None) }, # OP: 06, #: 1
    "TPA":  { ADDR_MODE_INHERENT: ("07", 1, None) }, # OP: 07, #: 1
}

# Kontrol amaçlı: Table 1'deki bazı opcode'lar Table 2'de yoksa veya farklıysa not alalım.
# Table 1'de 00-05 arası boş (NOP 01'de var).
# Table 1'de 02, 03, 04, 05, 07 (TPA hariç), 12, 13, 14, 15, 18 (ABA hariç), 1A, 1C, 1D, 1E, 1F boş.
# Çoğu komut Table 2'de daha detaylı verildiği için orayı esas aldık.
# Table 1'deki "87", "8D BSR", "C3", "C7", "CD", "CF", "D3", "D7 STA B DIR" (D7'yi aldık), "DC", "DD" (JSR IND, EXT aldık), "ED", "F3" gibi bazı boşluklar var.
# M6800'de toplam 197 geçerli makine kodu olduğu belirtilmiş. Bu tablo şu an bunu yansıtıyor olmalı.

# Örnek Kullanım:
if __name__ == '__main__':
    print(f"LDAA IMM Opcode: {OPCODE_TABLE['LDAA'][ADDR_MODE_IMMEDIATE]}")
    print(f"JMP EXT Opcode: {OPCODE_TABLE['JMP'][ADDR_MODE_EXTENDED]}")
    print(f"NOP Opcode: {OPCODE_TABLE['NOP'][ADDR_MODE_INHERENT]}")

    count = 0
    for mnemonic, modes in OPCODE_TABLE.items():
        count += len(modes)
    print(f"\nToplam tanımlanmış opcode/adresleme modu kombinasyonu: {count}")
    # Bu sayı 197 olmalı. Eğer değilse, eksik veya fazla bir şeyler var demektir.
    # Dokümanda (Page 13) "There are 197 valid machine codes" diyor.

    # 197'yi bulmak için bir kontrol:
    # "CLR" için Table 2'de sadece INDEXED ve EXTENDED var. Table 1'de de bu böyle.
    # CLR A ve CLR B ayrı komutlar (CLRA, CLRB) ve Inherent.
    # Byte sayılarını Table 2'deki '#' sütunundan aldım. Bazı yerlerde çevrim sayısı ile karıştırılmış olabilir (CLR için mesela),
    # ama genellikle # byte sayısını ifade eder. Mantıksal olarak da opcode + operand byte sayısıdır.
    # CLR $addr (EXT) -> 7F XX YY (3 byte)
    # CLR offs,X (IND) -> 6F XX (2 byte)
    # Bunlar doğru görünüyor.