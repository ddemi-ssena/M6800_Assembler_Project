# gui/main_window.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import traceback # Hata ayıklama için

# --- YENİ IMPORT ---
from simulator_core.m6800_cpu import M6800CPU, CCR_CARRY, CCR_OVERFLOW, CCR_ZERO, CCR_NEGATIVE, CCR_INTERRUPT, CCR_HALF_CARRY

try:
    # Eğer gui paketi içinden çalıştırılıyorsa ve assembler_core bir üst dizindeyse
    # veya PYTHONPATH'daysa:
    from assembler_core import assembler
except ImportError:
    # Eğer ana dizinden (proje kökünden) çalıştırılıyorsa (örn: python -m gui.main)
    # ve assembler_core ile aynı seviyedeyse:
    # Bu senaryo için sys.path ayarlaması genellikle doğrudan ana betikte yapılır.
    # Ancak, bu dosya doğrudan çalıştırılmıyorsa, aşağıdaki gibi bir fallback denenebilir.
    # Daha temiz bir çözüm için proje yapınıza göre importları ayarlamak en iyisidir.
    import sys
    # Proje kök dizinini sys.path'e eklemeyi deneyebiliriz
    # Bu, __file__'ın doğru bir şekilde ayarlandığını varsayar.
    # Bu dosyanın iki seviye derinde olduğunu varsayarsak (örn: proje_koku/gui/main_window.py)
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # Şimdi tekrar deneyelim
    from assembler_core import assembler

from .widgets import CodeEditor, OutputDisplay, MemoryViewer
from .menu_bar import AppMenuBar

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("M6800 Assembler & Simulator") # Başlığı güncelleyebiliriz
        self.geometry("1300x750") # Simülatör paneli için biraz daha genişlik ve yükseklik

        self.current_file_path = None

        # --- Simülatör ile ilgili özellikler ---
        self.cpu_simulator = M6800CPU()
        self.program_loaded_in_simulator = False
        self.last_mc_segments = None # Assemble edilmiş son makine kodu
        self.last_sym_table = None   # Assemble edilmiş son sembol tablosu
        # --- Simülatör ile ilgili özellikler SONU ---

        self._setup_ui() # Ana UI (assembler kısmı)
        self._setup_simulator_ui() # Simülatör UI'ını kur
        
        self.menu_bar = AppMenuBar(self, self) # self (MainWindow) app_logic olarak veriliyor
        self.update_simulator_display() # Başlangıçta registerları göster

    def _setup_ui(self):
        # Ana PanedWindow'ı oluşturalım, böylece simülatör panelini de ekleyebiliriz
        self.top_paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.top_paned_window.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Sol Panel: Kod Editörü ve Derleme Butonu
        left_assembler_frame = ttk.Frame(self.top_paned_window, padding=5)
        self.code_editor = CodeEditor(left_assembler_frame, height=25, width=70) # Boyutları biraz artırdım
        self.code_editor.pack(fill=tk.BOTH, expand=True, pady=(0,5))

        self.assemble_button = ttk.Button(left_assembler_frame, text="Assemble (F5)", command=self.run_assembly_process)
        self.assemble_button.pack(fill=tk.X, pady=(5,0))
        self.top_paned_window.add(left_assembler_frame, weight=2) # Assembler editörüne ağırlık

        # Orta Panel: Çıktı Alanları
        right_output_frame = ttk.Frame(self.top_paned_window, padding=5)
        notebook = ttk.Notebook(right_output_frame)

        self.listing_display = OutputDisplay(notebook, height=15, width=60) # Genişliği artırdım
        notebook.add(self.listing_display, text="Listeleme")

        self.symbol_table_display = OutputDisplay(notebook, height=15, width=60)
        notebook.add(self.symbol_table_display, text="Sembol Tablosu")

        self.machine_code_display = OutputDisplay(notebook, height=15, width=60)
        notebook.add(self.machine_code_display, text="Makine Kodu")

        self.error_display = OutputDisplay(notebook, height=7, width=60) # Yükseklik biraz artırdım
        self.error_display.configure(background="lightyellow")
        notebook.add(self.error_display, text="Hatalar/Uyarılar")

        self.memory_viewer = MemoryViewer(notebook)
        notebook.add(self.memory_viewer, text="Bellek Görüntüleyici")

        notebook.pack(fill=tk.BOTH, expand=True)
        self.top_paned_window.add(right_output_frame, weight=3) # Çıktı alanlarına daha fazla ağırlık

        # Durum Çubuğu (en altta kalacak)
        self.status_bar = ttk.Label(self, text="Hazır", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=(0,5))

    def _setup_simulator_ui(self):
        sim_outer_frame = ttk.Frame(self.top_paned_window, padding=5)
        self.top_paned_window.add(sim_outer_frame, weight=1) # Simülatöre ağırlık

        sim_frame = ttk.LabelFrame(sim_outer_frame, text="CPU Simülatörü", padding=10)
        sim_frame.pack(fill=tk.BOTH, expand=True)


        reg_frame = ttk.Frame(sim_frame)
        reg_frame.pack(pady=5, fill=tk.X, anchor="n")

        # Register Göstergeleri
        ttk.Label(reg_frame, text="PC:", width=4, anchor="e").grid(row=0, column=0, sticky="e", padx=(0,2), pady=1)
        self.pc_var = tk.StringVar(value="$0000")
        ttk.Entry(reg_frame, textvariable=self.pc_var, state="readonly", width=7, justify="center").grid(row=0, column=1, padx=(0,10), pady=1)

        ttk.Label(reg_frame, text="SP:", width=4, anchor="e").grid(row=1, column=0, sticky="e", padx=(0,2), pady=1)
        self.sp_var = tk.StringVar(value="$0000")
        ttk.Entry(reg_frame, textvariable=self.sp_var, state="readonly", width=7, justify="center").grid(row=1, column=1, padx=(0,10), pady=1)
        
        ttk.Label(reg_frame, text="A:", width=3, anchor="e").grid(row=0, column=2, sticky="e", padx=(0,2), pady=1)
        self.a_var = tk.StringVar(value="$00")
        ttk.Entry(reg_frame, textvariable=self.a_var, state="readonly", width=5, justify="center").grid(row=0, column=3, padx=(0,5), pady=1)

        ttk.Label(reg_frame, text="B:", width=3, anchor="e").grid(row=1, column=2, sticky="e", padx=(0,2), pady=1)
        self.b_var = tk.StringVar(value="$00")
        ttk.Entry(reg_frame, textvariable=self.b_var, state="readonly", width=5, justify="center").grid(row=1, column=3, padx=(0,5), pady=1)

        ttk.Label(reg_frame, text="X:", width=4, anchor="e").grid(row=2, column=0, sticky="e", padx=(0,2), pady=1)
        self.x_var = tk.StringVar(value="$0000")
        ttk.Entry(reg_frame, textvariable=self.x_var, state="readonly", width=7, justify="center").grid(row=2, column=1, padx=(0,10), pady=1)

        ttk.Label(reg_frame, text="CCR:", width=4, anchor="e").grid(row=3, column=0, sticky="e", padx=(0,2), pady=(5,1))
        self.ccr_var = tk.StringVar(value="$C0 (--I---)") 
        ttk.Entry(reg_frame, textvariable=self.ccr_var, state="readonly", width=18, justify="center").grid(row=3, column=1, columnspan=3, padx=(0,5), pady=(5,1), sticky="ew")
        
        # Kontrol Butonları
        controls_frame = ttk.Frame(sim_frame)
        controls_frame.pack(pady=15, fill=tk.X, anchor="n")
        
        ttk.Button(controls_frame, text="Reset CPU", command=self.sim_reset, width=10).pack(side=tk.LEFT, padx=3, fill=tk.X, expand=True)
        self.load_to_sim_button = ttk.Button(controls_frame, text="Load to Sim", command=self.load_program_to_simulator, state=tk.DISABLED, width=10)
        self.load_to_sim_button.pack(side=tk.LEFT, padx=3, fill=tk.X, expand=True)
        self.step_button = ttk.Button(controls_frame, text="Step (F7)", command=self.sim_step, state=tk.DISABLED, width=10)
        self.step_button.pack(side=tk.LEFT, padx=3, fill=tk.X, expand=True)
        # self.run_button = ttk.Button(controls_frame, text="Run (F8)", command=self.sim_run, state=tk.DISABLED)
        # self.run_button.pack(side=tk.LEFT, padx=2)

        # Klavye kısayolları
        self.bind_all("<F7>", lambda event: self.sim_step() if self.step_button['state'] == tk.NORMAL else None)
        self.bind_all("<F5>", lambda event: self.run_assembly_process() if self.assemble_button['state'] == tk.NORMAL else None)


    def _update_status(self, message):
        self.status_bar.config(text=message)

    def update_simulator_display(self):
        self.pc_var.set(f"${self.cpu_simulator.pc:04X}")
        self.sp_var.set(f"${self.cpu_simulator.sp:04X}")
        self.a_var.set(f"${self.cpu_simulator.acc_a:02X}")
        self.b_var.set(f"${self.cpu_simulator.acc_b:02X}")
        self.x_var.set(f"${self.cpu_simulator.ix:04X}")
        
        ccr_val = self.cpu_simulator.ccr
        h = 'H' if (ccr_val & CCR_HALF_CARRY) else '-'
        i_flag = 'I' if (ccr_val & CCR_INTERRUPT) else '-' # I bayrağı
        n = 'N' if (ccr_val & CCR_NEGATIVE) else '-'
        z = 'Z' if (ccr_val & CCR_ZERO) else '-'
        v = 'V' if (ccr_val & CCR_OVERFLOW) else '-'
        c = 'C' if (ccr_val & CCR_CARRY) else '-'
        # M6800 CCR bit sırası: (X X H I N Z V C) - X'ler her zaman 1'dir.
        # Gösterim sırası genellikle H I N Z V C şeklindedir.
        self.ccr_var.set(f"${ccr_val:02X} ({h}{i_flag}{n}{z}{v}{c})")
        # --- BELLEK GÜNCELLE ---
        self.memory_viewer.set_memory(self.cpu_simulator.memory)

    def load_program_to_simulator(self):
        if self.last_mc_segments:
            self.cpu_simulator.load_memory(self.last_mc_segments)
            
            start_address = 0xC000 # Varsayılan
            if self.last_mc_segments and self.last_mc_segments[0]: # İlk segmentin adresini al
                start_address = self.last_mc_segments[0][0]

            if self.last_sym_table:
                val = self.last_sym_table.get_symbol_value("START")
                if val is not None: # Eğer START etiketi tanımlıysa onu kullan
                    start_address = val
            
            self.cpu_simulator.reset()
            self.cpu_simulator.pc = start_address # PC'yi programın başına ayarla

            self.program_loaded_in_simulator = True
            self.step_button.config(state=tk.NORMAL)
            # self.run_button.config(state=tk.NORMAL) # Eğer run varsa
            self.update_simulator_display()
            self._update_status(f"Program simülatöre yüklendi. PC=${start_address:04X}")
            messagebox.showinfo("Simülatör", f"Program simülatör belleğine yüklendi.\nBaşlangıç PC: ${start_address:04X}")
        else:
            messagebox.showwarning("Simülatör", "Yüklenecek makine kodu bulunmuyor. Önce programı assemble edin.")

    def sim_reset(self):
        self.cpu_simulator.reset()
        if self.program_loaded_in_simulator and self.last_mc_segments:
            start_address = self.last_mc_segments[0][0]
            if self.last_sym_table:
                val = self.last_sym_table.get_symbol_value("START")
                if val is not None: start_address = val
            self.cpu_simulator.pc = start_address
        else: # Program yüklü değilse butonları pasif yap
            self.program_loaded_in_simulator = False
            self.step_button.config(state=tk.DISABLED)
            # self.run_button.config(state=tk.DISABLED)
        
        self.update_simulator_display()
        self._update_status("CPU Resetlendi.")
        self.step_button.config(state=tk.NORMAL if self.program_loaded_in_simulator else tk.DISABLED)

    def sim_step(self):
        if not self.program_loaded_in_simulator:
            messagebox.showwarning("Simülatör", "Önce programı simülatöre yükleyin.")
            return
        if self.cpu_simulator.halted:
            messagebox.showinfo("Simülatör", "CPU durdurulmuş (halted). Resetleyin veya yeni program yükleyin.")
            self.step_button.config(state=tk.DISABLED)
            # self.run_button.config(state=tk.DISABLED)
            return
        
        try:
            success = self.cpu_simulator.step()
            self.update_simulator_display()
            if not success or self.cpu_simulator.halted:
                msg = "CPU durduruldu."
                if not success and not self.cpu_simulator.halted:
                     msg = "Simülasyon adımı başarısız oldu (örn: bilinmeyen opcode)."
                elif self.cpu_simulator.halted:
                     msg = "CPU SWI veya benzeri bir komutla durduruldu."
                
                messagebox.showinfo("Simülasyon", msg)
                self.step_button.config(state=tk.DISABLED)
                # self.run_button.config(state=tk.DISABLED)
                self._update_status(msg)
            else:
                self._update_status(f"Adım atıldı. Sonraki PC=${self.cpu_simulator.pc:04X}")
        except Exception as e:
            messagebox.showerror("Simülasyon Hatası", f"Simülasyon sırasında kritik hata: {e}\n{traceback.format_exc()}")
            self.update_simulator_display() # Hata anındaki durumu göster
            self._update_status(f"Simülasyon hatası: {e}")

    def _reset_simulator_state_for_new_code(self):
        """Yeni kod yüklendiğinde veya derlendiğinde simülatör durumunu sıfırlar."""
        self.load_to_sim_button.config(state=tk.DISABLED)
        self.step_button.config(state=tk.DISABLED)
        # self.run_button.config(state=tk.DISABLED)
        self.program_loaded_in_simulator = False
        self.last_mc_segments = None
        self.last_sym_table = None
        self.cpu_simulator.reset() # CPU'yu da resetleyebiliriz
        self.update_simulator_display()

    def new_file(self):
        if self._ask_save_if_needed():
            self.code_editor.clear_code()
            self.current_file_path = None
            self.title("M6800 Assembler & Simulator - Yeni Dosya")
            self._update_status("Yeni dosya oluşturuldu.")
            self._reset_simulator_state_for_new_code() # Simülatör durumunu sıfırla
            # Çıktı alanlarını da temizleyelim
            self.listing_display.clear_text()
            self.symbol_table_display.clear_text()
            self.machine_code_display.clear_text()
            self.error_display.clear_text()


    def open_file(self):
        if self._ask_save_if_needed():
            file_path = filedialog.askopenfilename(
                defaultextension=".asm",
                filetypes=[("Assembly Files", "*.asm *.s *.txt"), ("All Files", "*.*")]
            )
            if file_path:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        self.code_editor.set_code(f.read())
                    self.current_file_path = file_path
                    self.title(f"M6800 Assembler & Simulator - {os.path.basename(file_path)}")
                    self._update_status(f"'{file_path}' açıldı.")
                    self._reset_simulator_state_for_new_code() # Simülatör durumunu sıfırla
                    # Çıktı alanlarını da temizleyelim
                    self.listing_display.clear_text()
                    self.symbol_table_display.clear_text()
                    self.machine_code_display.clear_text()
                    self.error_display.clear_text()
                except Exception as e:
                    messagebox.showerror("Dosya Açılamadı", f"Dosya okuma hatası: {e}")
                    self._update_status(f"Dosya açılamadı: {file_path}")

    def _ask_save_if_needed(self):
        # Basit bir placeholder, gerçek bir "kaydedilmemiş değişiklik var mı?" kontrolü
        # ve kullanıcıya sorma mantığı eklenebilir.
        # Şimdilik her zaman True dönüyoruz.
        # if self.code_editor.edit_modified(): # Eğer Text widget'ında değişiklik varsa
        #     response = messagebox.askyesnocancel("Kaydet?", "Kaydedilmemiş değişiklikler var. Kaydetmek ister misiniz?")
        #     if response is True: # Yes
        #         return self.save_file() # True dönerse devam et, False dönerse iptal
        #     elif response is False: # No
        #         return True # Kaydetme, devam et
        #     else: # Cancel veya pencereyi kapatma
        #         return False # İşlemi iptal et
        return True # Değişiklik yoksa veya sorma mantığı yoksa devam et

    def save_file(self):
        if self.current_file_path:
            try:
                with open(self.current_file_path, 'w', encoding='utf-8') as f:
                    f.write(self.code_editor.get_code())
                self._update_status(f"'{self.current_file_path}' kaydedildi.")
                self.code_editor.edit_modified(False) # Değişiklik bayrağını sıfırla
                return True
            except Exception as e:
                messagebox.showerror("Kaydetme Hatası", f"Dosya kaydedilemedi: {e}")
                return False
        else:
            return self.save_file_as()

    def save_file_as(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".asm",
            filetypes=[("Assembly Files", "*.asm *.s *.txt"), ("All Files", "*.*")]
        )
        if file_path:
            self.current_file_path = file_path
            self.title(f"M6800 Assembler & Simulator - {os.path.basename(file_path)}")
            return self.save_file()
        return False


    def run_assembly_process(self):
        self._update_status("Derleniyor...")
        self.listing_display.clear_text()
        self.symbol_table_display.clear_text()
        self.machine_code_display.clear_text()
        self.error_display.clear_text()

        self._reset_simulator_state_for_new_code() # Yeni derleme öncesi simülatörü sıfırla

        source_code = self.code_editor.get_code()
        if not source_code.strip():
            messagebox.showwarning("Boş Kod", "Derlenecek kod bulunmuyor.")
            self._update_status("Derleme iptal edildi: Kod boş.")
            return

        source_lines = source_code.strip().split('\n')

        try:
            sym_table, proc_lines_p1, errs_p1 = assembler.pass_one(source_lines)

            # Pass 1/Lexer hatalarını (varsa) göster
            combined_errors_p1_lexer = []
            for line_data in proc_lines_p1:
                if line_data.get("error") and line_data["error"] not in combined_errors_p1_lexer:
                    # Sadece lexer'dan veya pass1'de bu satır için eklenen ilk hatayı alalım
                    # errs_p1 zaten genel hataları (örn: duplicate label) tutuyor.
                    # proc_lines_p1'deki error'lar daha çok satır bazlı syntax hataları olabilir.
                    # Şimdilik errs_p1'i kullanalım, daha sonra bu ayrımı netleştirebiliriz.
                    pass # errs_p1 zaten genel hataları tutuyor

            if errs_p1:
                # errs_p1 hem lexer hem de pass1 genel hatalarını (duplicate label vb.) içermeli
                self.error_display.append_text("--- PASS 1 / LEXER HATALARI ---")
                for err_msg in sorted(list(set(errs_p1))): # Tekrarları önle ve sırala
                    self.error_display.append_text(err_msg)

            final_listing, mc_segments, errs_p2_pass_two_only = assembler.pass_two(proc_lines_p1, sym_table)
            
            self.symbol_table_display.set_text(str(sym_table))

            listing_text_lines = []
            any_error_in_listing = False
            for entry in final_listing:
                mc_hex_str = entry['machine_code_hex'] if entry['machine_code_hex'] else ""
                line = f"L:{entry['line_num']:<3} Adr:{entry['address_hex']:<6} Kod:{mc_hex_str:<10} "
                line += f"{entry['label'] or '':<9} {entry['mnemonic'] or '':<7} {entry['operand_str'] or '':<18}"
                if entry['comment']: line += f"; {entry['comment']}"
                listing_text_lines.append(line)
                if entry.get('error'):
                    listing_text_lines.append(f"    HATA: {entry['error']}")
                    any_error_in_listing = True # Hata varsa işaretle
            self.listing_display.set_text("\n".join(listing_text_lines))

            # Sadece Pass 2'de YENİ oluşan hataları göster
            if errs_p2_pass_two_only:
                self.error_display.append_text("\n--- PASS 2 ÖZGÜN HATALARI ---")
                for err_msg in sorted(list(set(errs_p2_pass_two_only))):
                    self.error_display.append_text(err_msg)
            
            mc_text = []
            if mc_segments:
                for addr, byte_codes in mc_segments:
                    hex_codes = " ".join([f"{b:02X}" for b in byte_codes])
                    mc_text.append(f"Segment @ ${addr:04X}: {hex_codes}")
            else:
                 mc_text.append("(Makine kodu üretilmedi)")
            self.machine_code_display.set_text("\n".join(mc_text))

            # Toplam hata sayısını belirle: errs_p1 (Pass1/Lexer) + errs_p2_pass_two_only (Pass2)
            # VEYA daha basitçe, listing'deki herhangi bir satırda hata var mı kontrolü
            # ve genel pass1 hataları.
            # `any_error_in_listing` zaten satır bazlı hataları kontrol ediyor.
            # `errs_p1` genel P1 hatalarını (örn: duplicate label) tutar.
            # `errs_p2_pass_two_only` ise P2'ye özgü (örn: range error) hataları tutar.
            
            total_unique_errors = set(errs_p1) | set(errs_p2_pass_two_only)
            # Ayrıca, final_listing'deki hataları da sayabiliriz ama bu yukarıdakilerle çakışabilir.
            # Şimdilik errs_p1 ve errs_p2_pass_two_only'yi baz alalım.
            # Eğer listing'de hata varsa ve bu P1/P2 listelerinde yoksa, o da bir hatadır.

            if not total_unique_errors and not any_error_in_listing:
                # ...existing code...
                if mc_segments:
                    self.last_mc_segments = mc_segments
                    self.last_sym_table = sym_table
                    self.load_to_sim_button.config(state=tk.NORMAL)
                    # --- BELLEK GÜNCELLE ---
                    self.cpu_simulator.load_memory(mc_segments)
                    self.memory_viewer.set_memory(self.cpu_simulator.memory)
            else:
                num_errors = len(total_unique_errors)
                if any_error_in_listing and num_errors == 0: # Sadece listing'de gösterilen ama sayılmayan hata varsa
                    num_errors = 1 # En az bir hata var de
                
                self._update_status(f"Derleme {num_errors if num_errors > 0 else 'bazı'} hata(lar) ile tamamlandı.")
                messagebox.showerror("Derleme Hatası", f"Derleme sırasında {num_errors if num_errors > 0 else 'bazı'} hata(lar) oluştu. Detaylar için 'Hatalar/Uyarılar' ve 'Listeleme' sekmelerini kontrol edin.")

        except Exception as e:
            self.error_display.append_text(f"\nBEKLENMEDİK KRİTİK DERLEME HATASI: {e}")
            self.error_display.append_text(traceback.format_exc())
            messagebox.showerror("Kritik Derleme Hatası", f"Beklenmedik bir hata oluştu:\n{e}")
            self._update_status(f"Kritik derleme hatası: {e}")

if __name__ == '__main__':
    # Bu dosyanın doğrudan çalıştırılması genellikle test amaçlıdır.
    # Gerçek uygulamada, bir ana betik (örn: main.py veya run_app.py) üzerinden
    # MainWindow örneği oluşturulup app.mainloop() çağrılır.
    
    # Eğer bu dosya doğrudan çalıştırılıyorsa ve paket yapısı varsa,
    # importlar sorun çıkarabilir. `python -m gui.main_window` gibi
    # bir komutla çalıştırmak daha iyi olabilir (eğer __main__ bloğu uygunsa).
    
    # Geçici test çalıştırması:
    try:
        app = MainWindow()
        app.mainloop()
    except Exception as e:
        print(f"Ana uygulama başlatılırken hata: {e}")
        print(traceback.format_exc())