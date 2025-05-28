# gui/main_window.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os # Dosya yolu işlemleri için

# assembler_core paketinden gerekli modülleri import et
# Proje kök dizininin Python path'ine eklenmiş olması gerekebilir
# veya main.py'den çalıştırırken bu importlar sorunsuz olmalı.
try:
    from assembler_core import assembler
except ImportError:
    # Eğer doğrudan bu dosyayı çalıştırmaya çalışıyorsak (test amaçlı)
    # ve assembler_core bir üst dizindeyse, sys.path'i ayarlamamız gerekebilir.
    # Genellikle main.py üzerinden çalıştıracağımız için bu bloğa ihtiyaç olmayabilir.
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from assembler_core import assembler


from .widgets import CodeEditor, OutputDisplay # Kendi widget'larımız
from .menu_bar import AppMenuBar # Menü çubuğumuz

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("M6800 Assembler - Tkinter")
        self.geometry("900x700")

        self.current_file_path = None # Açık olan dosyanın yolu

        self._setup_ui()
        self.menu_bar = AppMenuBar(self, self) # Menü çubuğunu oluştur ve app_logic olarak kendini (MainWindow) ver

    def _setup_ui(self):
        # Ana çerçeveyi PanedWindow ile ikiye bölmek daha esnek olabilir
        main_paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_paned_window.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Sol Panel: Kod Editörü ve Derleme Butonu
        left_frame = ttk.Frame(main_paned_window, padding=5)
        self.code_editor = CodeEditor(left_frame, height=20, width=60)
        self.code_editor.pack(fill=tk.BOTH, expand=True, pady=(0,5))

        self.assemble_button = ttk.Button(left_frame, text="Assemble (F5)", command=self.run_assembly_process)
        self.assemble_button.pack(fill=tk.X, pady=(5,0))
        main_paned_window.add(left_frame, weight=1) # weight ile boyutlandırma önceliği

        # Sağ Panel: Çıktı Alanları (Sekmeli olabilir)
        right_frame = ttk.Frame(main_paned_window, padding=5)
        notebook = ttk.Notebook(right_frame) # Sekmeli görünüm için

        self.listing_display = OutputDisplay(notebook, height=15, width=50)
        notebook.add(self.listing_display, text="Listeleme")

        self.symbol_table_display = OutputDisplay(notebook, height=15, width=50)
        notebook.add(self.symbol_table_display, text="Sembol Tablosu")

        self.machine_code_display = OutputDisplay(notebook, height=15, width=50)
        notebook.add(self.machine_code_display, text="Makine Kodu")

        self.error_display = OutputDisplay(notebook, height=5, width=50)
        self.error_display.configure(background="lightyellow") # Hata alanı için farklı renk
        notebook.add(self.error_display, text="Hatalar/Uyarılar")

        notebook.pack(fill=tk.BOTH, expand=True)
        main_paned_window.add(right_frame, weight=2) # Sağ panel biraz daha geniş olsun

        # --- Durum Çubuğu ---
        self.status_bar = ttk.Label(self, text="Hazır", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _update_status(self, message):
        self.status_bar.config(text=message)

    def new_file(self):
        if self._ask_save_if_needed():
            self.code_editor.clear_code()
            self.listing_display.clear_text()
            self.symbol_table_display.clear_text()
            self.machine_code_display.clear_text()
            self.error_display.clear_text()
            self.current_file_path = None
            self.title("M6800 Assembler - Tkinter - Yeni Dosya")
            self._update_status("Yeni dosya oluşturuldu.")

    def _ask_save_if_needed(self):
        # TODO: Kod editöründe değişiklik olup olmadığını kontrol et
        # Şimdilik her zaman True dönüyoruz
        # if self.code_editor.edit_modified(): # Değişiklik varsa
        #    response = messagebox.askyesnocancel("Kaydet?", "Değişiklikleri kaydetmek ister misiniz?")
        #    if response is True: self.save_file()
        #    elif response is None: return False # Cancel
        return True

    def open_file(self):
        if not self._ask_save_if_needed():
            return

        file_path = filedialog.askopenfilename(
            defaultextension=".asm",
            filetypes=[("Assembly Dosyaları", "*.asm *.s"), ("Tüm Dosyalar", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.code_editor.set_code(f.read())
                self.current_file_path = file_path
                self.title(f"M6800 Assembler - Tkinter - {os.path.basename(file_path)}")
                self._update_status(f"Dosya açıldı: {file_path}")
            except Exception as e:
                messagebox.showerror("Dosya Açma Hatası", f"Dosya okunamadı:\n{e}")
                self._update_status(f"Dosya açma hatası: {e}")


    def save_file(self):
        if self.current_file_path:
            try:
                with open(self.current_file_path, 'w', encoding='utf-8') as f:
                    f.write(self.code_editor.get_code())
                self.title(f"M6800 Assembler - Tkinter - {os.path.basename(self.current_file_path)}")
                self._update_status(f"Dosya kaydedildi: {self.current_file_path}")
                # self.code_editor.edit_modified(False) # Değişiklik bayrağını sıfırla
            except Exception as e:
                messagebox.showerror("Dosya Kaydetme Hatası", f"Dosya kaydedilemedi:\n{e}")
                self._update_status(f"Dosya kaydetme hatası: {e}")
        else:
            self.save_file_as()

    def save_file_as(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".asm",
            filetypes=[("Assembly Dosyaları", "*.asm *.s"), ("Tüm Dosyalar", "*.*")]
        )
        if file_path:
            self.current_file_path = file_path
            self.save_file() # save_file şimdi current_file_path'i kullanacak

    def run_assembly_process(self):
        self._update_status("Derleniyor...")
        self.listing_display.clear_text()
        self.symbol_table_display.clear_text()
        self.machine_code_display.clear_text()
        self.error_display.clear_text()

        source_code = self.code_editor.get_code()
        if not source_code.strip():
            messagebox.showwarning("Boş Kod", "Derlenecek kod bulunmuyor.")
            self._update_status("Derleme iptal edildi: Kod boş.")
            return

        source_lines = source_code.strip().split('\n')

        # --- Derleme işlemi ---
        # TODO: Bu işlemi ayrı bir thread'de çalıştırmak GUI'nin donmasını engeller.
        # Tkinter için `threading` modülü ve `queue` ile ana thread'e bilgi gönderme
        # veya `after` metodu ile periyodik kontrol düşünülebilir.
        # Şimdilik basitlik adına doğrudan çağırıyoruz.
        try:
            sym_table, proc_lines_p1, errs_p1 = assembler.pass_one(source_lines)

            # Pass 1 Hatalarını Göster
            if errs_p1:
                self.error_display.append_text("--- PASS 1 HATALARI ---")
                for err in errs_p1:
                    self.error_display.append_text(err)

            final_listing, mc_segments, errs_p2_combined = assembler.pass_two(proc_lines_p1, sym_table)

            # Sembol Tablosunu Göster
            self.symbol_table_display.set_text(str(sym_table))

            # Listelemeyi Göster
            listing_text = []
            for entry in final_listing:
                line = f"L:{entry['line_num']:<3} Adr:{entry['address_hex']:<6} Kod:{entry['machine_code_hex']:<10} "
                line += f"{entry['label'] or '':<8} {entry['mnemonic'] or '':<6} {entry['operand_str'] or '':<15}"
                if entry['comment']:
                    line += f"; {entry['comment']}"
                listing_text.append(line)
                # Satır bazlı hataları da listelemeye ekleyebiliriz veya ayrı hata alanında
                if entry['error']:
                    is_p1_error = any(f"Satır {entry['line_num']}" in p1_err and entry['error'] in p1_err for p1_err in errs_p1)
                    if not is_p1_error:
                         listing_text.append(f"    HATA (P2): {entry['error']}")
                         self.error_display.append_text(f"Satır {entry['line_num']} (P2): {entry['error']}")

            self.listing_display.set_text("\n".join(listing_text))


            # Sadece Pass 2'de oluşan farklı hataları göster
            pass1_error_messages_set = set(errs_p1)
            errs_p2_only = []
            for p2_err in errs_p2_combined:
                is_from_pass1_or_similar = False
                for p1_err in pass1_error_messages_set:
                    # Basit bir karşılaştırma
                    if p2_err == p1_err or p2_err in p1_err or p1_err in p2_err:
                        is_from_pass1_or_similar = True; break
                if not is_from_pass1_or_similar: errs_p2_only.append(p2_err)

            if errs_p2_only:
                self.error_display.append_text("\n--- PASS 2'DE OLUŞAN FARKLI HATALAR ---")
                for err in errs_p2_only:
                    self.error_display.append_text(err)

            # Makine Kodu Segmentlerini Göster
            mc_text = []
            if mc_segments:
                for addr, byte_codes in mc_segments:
                    hex_codes = " ".join([f"{b:02X}" for b in byte_codes])
                    mc_text.append(f"Segment @ ${addr:04X}: {hex_codes}")
            else:
                mc_text.append("(Makine kodu segmenti üretilmedi veya hatalar nedeniyle boş.)")
            self.machine_code_display.set_text("\n".join(mc_text))

            if not errs_p1 and not errs_p2_only: # Sadece pass2'ye özgü yeni hata yoksa
                 self._update_status("Derleme başarıyla tamamlandı.")
                 if not errs_p1: # Hiçbir pass1 hatası da yoksa
                    messagebox.showinfo("Başarılı", "Derleme başarıyla tamamlandı.")
                 else: # Pass1 hataları vardı ama P2'de yeni hata çıkmadı
                    messagebox.showwarning("Derleme Tamamlandı (Hatalarla)", "Derleme Pass 1 hatalarıyla tamamlandı. Lütfen hataları kontrol edin.")
            else:
                self._update_status("Derleme hatalarla tamamlandı.")
                messagebox.showerror("Derleme Hatası", "Derleme sırasında hatalar oluştu. Lütfen 'Hatalar/Uyarılar' sekmesini kontrol edin.")

        except Exception as e:
            # Bu, assembler.py içindeki beklenmedik bir Python hatası olabilir
            self.error_display.append_text(f"\nBEKLENMEDİK DERLEME HATASI: {e}")
            messagebox.showerror("Kritik Derleme Hatası", f"Beklenmedik bir hata oluştu:\n{e}")
            self._update_status(f"Kritik derleme hatası: {e}")
            import traceback
            self.error_display.append_text(traceback.format_exc()) # Detaylı hata izi