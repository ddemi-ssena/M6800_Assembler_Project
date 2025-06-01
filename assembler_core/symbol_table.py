# assembler_core/memory_viewer.py
import tkinter as tk
from tkinter import messagebox

class MemoryViewer(tk.Frame):
    """
    Bellek görüntüleme ve düzenleme arayüzü için sınıf.
    Bellek içeriğini tablo şeklinde gösterir ve kullanıcıya düzenleme imkanı tanır.
    """

    def __init__(self, master=None, memory=None, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master
        self.memory = memory if memory is not None else [0] * 0x10000  # Varsayılan olarak 64KB bellek
        self.initUI()

    def initUI(self):
        """
        Kullanıcı arayüzünü başlatır ve bileşenleri oluşturur.
        """
        self.tree = None  # Ağaç görünümünü daha sonra tanımlayacağız

        # Üst çerçeve için bir çerçeve
        frame_top = tk.Frame(self)
        frame_top.pack(side=tk.TOP, fill=tk.X)

        # Aşağıdaki çerçeve için
        frame_bottom = tk.Frame(self)
        frame_bottom.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        # Bellek adresi girişi için etiket ve giriş kutusu
        lbl_address = tk.Label(frame_top, text="Adres:")
        lbl_address.pack(side=tk.LEFT, padx=5, pady=5)

        self.ent_address = tk.Entry(frame_top, width=10)
        self.ent_address.pack(side=tk.LEFT, padx=5, pady=5)

        # Bellek değeri girişi için etiket ve giriş kutusu
        lbl_value = tk.Label(frame_top, text="Değer:")
        lbl_value.pack(side=tk.LEFT, padx=5, pady=5)

        self.ent_value = tk.Entry(frame_top, width=10)
        self.ent_value.pack(side=tk.LEFT, padx=5, pady=5)

        # Belleği güncellemek için bir buton
        btn_update = tk.Button(frame_top, text="Güncelle", command=self.update_memory)
        btn_update.pack(side=tk.LEFT, padx=5, pady=5)

        # Ağaç görünümünü oluştur
        self.populate()

        # Çift tıklama ile düzenleme
        self.tree.bind("<Double-1>", self._on_double_click)

    def populate(self):
        """
        Ağaç görünümünü bellekteki mevcut verilerle doldurur.
        """
        if self.tree is not None:
            self.tree.destroy()  # Mevcut ağaç görünümünü yok et

        # Yeni bir ağaç görünümü oluştur
        self.tree = tk.ttk.Treeview(self, columns=("value"), show="headings")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Yatay kaydırma çubuğu
        scrollbar = tk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.configure(xscroll=scrollbar.set)

        # Dikey kaydırma çubuğu
        scrollbar = tk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscroll=scrollbar.set)

        # Sütun başlıklarını ayarla
        self.tree.heading("value", text="Değer")
        self.tree.column("value", width=100)

        # Bellek içeriğini ağaç görünümüne ekle
        for i in range(0, len(self.memory), 16):
            # Her satır için bellek adresi ve değerlerini al
            addr = f"${i:04X}"
            values = [f"${x:02X}" for x in self.memory[i:i+16]]
            # Boş değerleri '-' ile doldur
            values += ['-'] * (16 - len(values))
            self.tree.insert("", "end", iid=addr, text=addr, values=values)

    def update_memory(self):
        """
        Kullanıcının girdiği adres ve değere göre belleği günceller.
        """
        try:
            addr = int(self.ent_address.get(), 16)
            value = int(self.ent_value.get(), 16)
            self.memory[addr] = value & 0xFF  # Sadece düşük byte'ı al
            self.populate()  # Ağaç görünümünü güncelle
        except Exception as e:
            messagebox.showerror("Hata", f"Geçersiz adres veya değer: {e}")

    def _on_double_click(self, event):
        """
        Ağaç görünümünde çift tıklama olayı için işlemci.
        Kullanıcıya bellek değerini düzenleme imkanı tanır.
        """
        item = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        if not item or column != "#2":  # Sadece değerler sütunu düzenlenebilir
            return
        addr_str = self.tree.item(item, "values")[0]
        addr = int(addr_str[1:], 16)
        # Basit bir input dialog ile yeni değer al
        import tkinter.simpledialog
        new_val = tkinter.simpledialog.askstring("Bellek Düzenle", f"{addr_str} adresindeki 16 byte'ı girin (hex, boşluklu):")
        if new_val:
            try:
                vals = [int(x, 16) for x in new_val.strip().split()]
                if len(vals) != 16:
                    raise ValueError("16 adet byte girilmeli.")
                for i, v in enumerate(vals):
                    self.memory[addr + i] = v & 0xFF
                self.populate()
            except Exception as e:
                messagebox.showerror("Hata", f"Geçersiz giriş: {e}")

class SymbolTable:
    def __init__(self):
        self.symbols = {}

    def add_symbol(self, name, value, line_num=None):
        if name in self.symbols:
            raise ValueError(f"Etiket zaten tanımlı: {name}")
        self.symbols[name] = (value, line_num)

    def get_symbol_value(self, name):
        entry = self.symbols.get(name)
        return entry[0] if entry else None

    def __str__(self):
        lines = ["Sembol Tablosu:"]
        for name, (value, line_num) in sorted(self.symbols.items()):
            lines.append(f"{name:<12} = ${value:04X} (Satır: {line_num})")
        return "\n".join(lines)

# Sınıfın nasıl kullanılacağını göstermek için basit bir test bloğu
if __name__ == '__main__':
    root = tk.Tk()
    root.title("Bellek Görüntüleyici")

    # Örnek bellek verisi ile
    example_memory = [i for i in range(256)] * 64  # Toplamda 16KB

    viewer = MemoryViewer(master=root, memory=example_memory)
    viewer.pack(fill=tk.BOTH, expand=True)

    root.mainloop()