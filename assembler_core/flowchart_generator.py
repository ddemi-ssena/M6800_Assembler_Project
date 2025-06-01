import re
import argparse
import os
import subprocess # YENİ
import traceback # YENİ

# M6800 Kontrol Akış Komutları
BRANCH_INSTRUCTIONS = [
    "JMP", "BRA", "BEQ", "BNE", "BPL", "BMI", "BCC", "BCS", "BVC", "BVS",
    "BHI", "BLS", "BGT", "BLT", "BGE", "BLE", "JSR", "BSR"
]
RETURN_INSTRUCTIONS = ["RTS", "RTI"]
ALL_CONTROL_FLOW_INSTRUCTIONS = BRANCH_INSTRUCTIONS + RETURN_INSTRUCTIONS

# Direktifler (bunlar genellikle flowchart'ta özel olarak ele alınmaz veya atlanır)
ASSEMBLER_DIRECTIVES = ["ORG", "EQU", "FCB", "FCC", "FDB", "RMB", "END", "OPT"] # END ve OPT eklendi

def parse_m6800(asm_file_path):
    print(f"DEBUG: parse_m6800 fonksiyonu çağrıldı, dosya: {asm_file_path}")
    lines_data = []
    try:
        with open(asm_file_path, 'r', encoding='utf-8') as f: # encoding eklendi
            for i, line_text in enumerate(f):
                line_content = line_text.split(';')[0].strip()
                if not line_content:
                    continue
                lines_data.append({'num': i + 1, 'content': line_content, 'original_text': line_text.strip(), 'label': None, 'op': None, 'args': None})
    except Exception as e:
        print(f"HATA: Dosya okunurken hata oluştu ({asm_file_path}): {e}")
        return "" # Boş DOT kodu döndür
    print(f"DEBUG: Dosya okundu, {len(lines_data)} satır (yorum/boş hariç) bulundu.")

    parsed_instructions = []
    current_label_for_next_instruction = None

    for line_info in lines_data:
        content = line_info['content']
        label_match = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*):(.*)", content)
        instruction_part = content
        temp_label = None

        if label_match:
            temp_label = label_match.group(1)
            instruction_part = label_match.group(2).strip()
        
        if temp_label:
            line_info['label'] = temp_label
            current_label_for_next_instruction = temp_label # Etiketi bir sonraki geçerli komuta ata

        if not instruction_part and temp_label: # Sadece etiket olan satır
            # Bu etiketi bir sonraki komut için sakla, parsed_instructions'a ekleme
            # (veya ayrı bir etiket node'u olarak ekleyebiliriz, ama blok mantığı için şimdilik böyle)
            print(f"DEBUG: Sadece etiket bulundu: {temp_label} (satır {line_info['num']})")
            # parsed_instructions.append(line_info) # Eğer etiketleri ayrı node yapmak istersen
            continue

        if not instruction_part and not temp_label: # Tamamen boş (yorum sonrası)
            continue

        parts = instruction_part.split(None, 1)
        op = None
        args = None

        if parts:
            op = parts[0].upper()
            if op in ASSEMBLER_DIRECTIVES:
                print(f"DEBUG: Direktif bulundu ve atlanıyor (flowchart için): {op} (satır {line_info['num']})")
                # Direktifleri flowchart'a dahil etmiyoruz, ama bazıları (END gibi) özel işlenebilir.
                # Şimdilik atlayalım.
                if op == "END": # END direktifi için özel bir son node oluşturulabilir
                    # line_info['op'] = "END_DIRECTIVE" # Özel bir işaretleyici
                    # parsed_instructions.append(line_info)
                    pass # Şimdilik END'i de görmezden gelelim, akış sonu RTS/RTI ile belirlenir
                continue # Direktifleri parsed_instructions'a ekleme

            if len(parts) > 1:
                args = parts[1]
            line_info['op'] = op
            line_info['args'] = args
            
            if current_label_for_next_instruction:
                line_info['label'] = current_label_for_next_instruction
                current_label_for_next_instruction = None # Etiket kullanıldı
            
            parsed_instructions.append(line_info)
        elif current_label_for_next_instruction:
            # Etiket vardı ama bu satırda komut yok (örn. direktif veya boşluk)
            # Etiket bir sonraki geçerli komuta taşınmalı, bu yüzden `current_label_for_next_instruction` hala set edilmiş durumda.
            print(f"DEBUG: Etiket ({current_label_for_next_instruction}) sonrası geçerli komut bekleniyor (satır {line_info['num']})")


    print(f"DEBUG: {len(parsed_instructions)} anlamlı komut ayrıştırıldı (direktifler hariç).")
    if not parsed_instructions:
        print("UYARI: Ayrıştırılacak anlamlı komut bulunamadı.")
        # Boş bir flowchart döndürebiliriz veya hata verebiliriz
        return "digraph G { label=\"Anlamlı komut bulunamadı\"; }"


    dot_nodes = []
    dot_edges = []
    labels_map = {}

    # 1. Adım: Tüm etiketleri ve onlara karşılık gelen node isimlerini haritala
    # Blok başlangıçlarını ve etiketli komutları node olarak işaretle
    node_counter = 0
    instruction_to_node_name = {} # instr_index -> node_name
    
    # START node'u
    dot_nodes.append('node_START [shape=Mdiamond, label="Başlangıç"];')
    previous_node_name_for_flow = "node_START" # Ardışık akış için
    
    # Her komutu geçici bir node olarak düşün, sonra bloklara birleştir.
    # Bu yaklaşım, etiketlerin ve dallanmaların yönetimi için daha esnek olabilir.
    
    # Geçici: Her komut bir node, sonra blokları birleştireceğiz.
    # Daha iyisi: Blokları direkt oluştur.
    
    # Etiketleri haritala (önce tüm etiketleri bulalım)
    for i, instr_data in enumerate(parsed_instructions):
        if instr_data['label'] and instr_data['label'] not in labels_map:
            node_name = f"node_label_{instr_data['label'].replace('-', '_')}"
            labels_map[instr_data['label']] = node_name
            print(f"DEBUG: Etiket haritalandı: {instr_data['label']} -> {node_name}")

    current_block_instructions_text = []
    current_block_start_label = None # Mevcut bloğun başındaki etiket
    last_instr_was_branch_or_return = True # Başlangıçta böyle varsayalım ki ilk blok doğru bağlansın

    for i, instr_data in enumerate(parsed_instructions):
        instr_content_display = instr_data['content'].replace('"', '\\"')
        
        is_new_block = False
        current_node_name_candidate = f"node_instr_{instr_data['num']}" # Her komut için potansiyel node adı

        if instr_data['label']:
            is_new_block = True
            current_node_name_candidate = labels_map[instr_data['label']] # Etiketliyse, etiket node adını kullan
            print(f"DEBUG: Yeni blok etiketten dolayı başlıyor: {instr_data['label']} (node: {current_node_name_candidate})")
        elif last_instr_was_branch_or_return and current_block_instructions_text:
            # Dallanma sonrası yeni blok (etiketsizse)
            # Aslında bu durum olmamalı, dallanma sonrası ya etiketli bir yere gidilir
            # ya da program biter. Etiketsiz düşüşler için ayrı bir mantık gerek.
            # Şimdilik, etiketsiz yeni blokları satır numarasıyla adlandırıyoruz.
            is_new_block = True
            print(f"DEBUG: Dallanma sonrası yeni blok (etiketsiz) (node: {current_node_name_candidate})")


        if is_new_block and current_block_instructions_text:
            # Önceki bloğu bitir
            block_label_for_node = "\\n".join(current_block_instructions_text)
            block_node_id_to_draw = current_block_start_label if current_block_start_label else f"node_block_{parsed_instructions[i-len(current_block_instructions_text)]['num']}"
            
            # Eğer bu node zaten tanımlanmışsa (etiketle), tekrar tanımlama
            node_already_defined = any(block_node_id_to_draw in node_def for node_def in dot_nodes)
            if not node_already_defined:
                 dot_nodes.append(f'{block_node_id_to_draw} [label="{block_label_for_node}", shape=box];')
            
            if previous_node_name_for_flow and not last_instr_was_branch_or_return : #and previous_node_name_for_flow != block_node_id_to_draw:
                dot_edges.append(f'{previous_node_name_for_flow} -> {block_node_id_to_draw};')
            
            previous_node_name_for_flow = block_node_id_to_draw
            current_block_instructions_text = []
        
        # Mevcut komutu bloğa ekle
        current_block_instructions_text.append(instr_content_display)
        if instr_data['label'] and not current_block_start_label: # Bloğun başlangıç etiketini al
            current_block_start_label = labels_map[instr_data['label']]
        elif not current_block_start_label: # Etiketsiz bloğun başlangıç ID'si
             current_block_start_label = current_node_name_candidate


        # Eğer komut dallanma veya dönüş ise, bu bloğu bitir
        if instr_data['op'] in ALL_CONTROL_FLOW_INSTRUCTIONS:
            block_label_for_node = "\\n".join(current_block_instructions_text)
            block_node_id_to_draw = current_block_start_label if current_block_start_label else current_node_name_candidate
            
            node_already_defined = any(block_node_id_to_draw in node_def for node_def in dot_nodes)
            if not node_already_defined:
                dot_nodes.append(f'{block_node_id_to_draw} [label="{block_label_for_node}", shape=box];')

            if previous_node_name_for_flow and not last_instr_was_branch_or_return and previous_node_name_for_flow != block_node_id_to_draw :
                # Bu durum, bir önceki komutun doğal akışla bu bloğa gelmesi demek
                # Örnek: LDAA, sonra bu blok bir BEQ ile başlıyorsa.
                # Eğer previous_node_name_for_flow zaten bu bloğun başlangıcıysa (etiketliyse), tekrar ok çizme.
                dot_edges.append(f'{previous_node_name_for_flow} -> {block_node_id_to_draw};')
            
            # Dallanma hedefini işle
            if instr_data['op'] in BRANCH_INSTRUCTIONS:
                target_label_name = instr_data['args']
                if target_label_name in labels_map:
                    target_node_name = labels_map[target_label_name]
                    edge_label_text = instr_data['op']
                    edge_color = "red" # JMP, BRA, JSR, BSR için
                    if instr_data['op'].startswith("B") and instr_data['op'] not in ["BRA", "BSR"]:
                        edge_label_text = f"{instr_data['op']} (Evet)"
                        edge_color = "blue"
                        # "Hayır" kolu (doğal akış) bir sonraki blok tarafından ele alınacak
                        # (veya açıkça eklenebilir)
                    dot_edges.append(f'{block_node_id_to_draw} -> {target_node_name} [label="{edge_label_text}", color={edge_color}];')
                    print(f"DEBUG: Dallanma eklendi: {block_node_id_to_draw} -> {target_node_name} ({instr_data['op']})")
                else:
                    print(f"UYARI: Dallanma hedef etiketi '{target_label_name}' haritada bulunamadı (satır {instr_data['num']}). Komut: {instr_data['content']}")
            
            elif instr_data['op'] in RETURN_INSTRUCTIONS:
                return_node_name = f"{block_node_id_to_draw}_return_end"
                dot_nodes.append(f'{return_node_name} [label="{instr_data["op"]}\\n(Dönüş)", shape=Mdiamond];')
                dot_edges.append(f'{block_node_id_to_draw} -> {return_node_name};')
                print(f"DEBUG: Dönüş eklendi: {block_node_id_to_draw} -> {return_node_name}")

            previous_node_name_for_flow = block_node_id_to_draw # Dallanma sonrası doğal akış için (eğer varsa)
            current_block_instructions_text = []
            current_block_start_label = None
            last_instr_was_branch_or_return = True
        else:
            # Normal komut, bloğa devam et
            previous_node_name_for_flow = current_block_start_label if current_block_start_label else current_node_name_candidate
            last_instr_was_branch_or_return = False

    # Döngüden sonra kalan son bloğu işle (eğer varsa ve dallanma/dönüş ile bitmediyse)
    if current_block_instructions_text:
        block_label_for_node = "\\n".join(current_block_instructions_text)
        block_node_id_to_draw = current_block_start_label if current_block_start_label else f"node_final_block_{parsed_instructions[-1]['num']}"
        
        node_already_defined = any(block_node_id_to_draw in node_def for node_def in dot_nodes)
        if not node_already_defined:
            dot_nodes.append(f'{block_node_id_to_draw} [label="{block_label_for_node}", shape=box];')
        
        if previous_node_name_for_flow and not last_instr_was_branch_or_return and previous_node_name_for_flow != block_node_id_to_draw:
            dot_edges.append(f'{previous_node_name_for_flow} -> {block_node_id_to_draw};')
        
        # Son bloğu genel bir END node'una bağla
        dot_nodes.append('node_END [shape=Mdiamond, label="Son"];')
        dot_edges.append(f'{block_node_id_to_draw} -> node_END;')
        print(f"DEBUG: Son blok (dallanmasız) eklendi ve 'Son'a bağlandı: {block_node_id_to_draw}")
    elif not dot_edges or not any("node_END" in edge or "_return_end" in edge for edge in dot_edges):
        # Hiç komut yoksa veya son komut bir dönüş/dallanma değilse ve END'e bağlanmamışsa
        # (Bu durum, örneğin tek bir RTS içeren bir kodda olabilir, o zaman return_end olur)
        # Veya hiç dallanma/dönüş yoksa, en son işlenen node'u END'e bağla
        if previous_node_name_for_flow and previous_node_name_for_flow != "node_START":
            is_already_connected_to_an_end = any(previous_node_name_for_flow in edge and ("node_END" in edge or "_return_end" in edge) for edge in dot_edges)
            if not is_already_connected_to_an_end:
                 # Eğer 'node_END' zaten tanımlanmamışsa tanımla
                if not any("node_END [" in node_def for node_def in dot_nodes):
                    dot_nodes.append('node_END [shape=Mdiamond, label="Son"];')
                dot_edges.append(f'{previous_node_name_for_flow} -> node_END;')
                print(f"DEBUG: Önceki akış node'u ({previous_node_name_for_flow}) 'Son'a bağlandı.")
        elif previous_node_name_for_flow == "node_START" and not parsed_instructions: # Hiç komut yoksa
             if not any("node_END [" in node_def for node_def in dot_nodes):
                dot_nodes.append('node_END [shape=Mdiamond, label="Son"];')
             dot_edges.append('node_START -> node_END [label="Komut Yok"];')


    # DOT çıktısını oluştur
    dot_output = "digraph M6800_Flowchart {\n"
    dot_output += "    rankdir=TB;\n"
    dot_output += "    node [fontname=\"Arial\", shape=box];\n" # Varsayılan şekil box
    dot_output += "    edge [fontname=\"Arial\"];\n\n"

    unique_node_definitions = []
    defined_node_names = set()

    for node_str in dot_nodes:
        node_name_match = re.match(r"^\s*([a-zA-Z0-9_]+)\s*\[", node_str)
        if node_name_match:
            node_name = node_name_match.group(1)
            if node_name not in defined_node_names:
                unique_node_definitions.append(f"    {node_str}")
                defined_node_names.add(node_name)
        else: # START, END gibi basit tanımlamalar için (aslında bunlar da yukarıdaki regex'e uymalı)
             unique_node_definitions.append(f"    {node_str}")


    dot_output += "    // Nodes\n"
    dot_output += "\n".join(unique_node_definitions)
    dot_output += "\n\n"
    dot_output += "    // Edges\n"
    dot_output += "\n".join([f"    {edge}" for edge in dot_edges])
    dot_output += "\n}\n"

    print("DEBUG: DOT çıktısı oluşturuldu.")
    # print(dot_output) # Çok uzun olabilir, dikkatli kullanın
    return dot_output

def main():
    parser = argparse.ArgumentParser(description="M6800 Assembly için Kontrol Akış Diyagramı Oluşturucu")
    parser.add_argument("asm_file", help="Giriş M6800 assembly dosyası (.asm)")
    parser.add_argument("-o", "--output", help="Çıktı DOT dosyasının adı (varsayılan: flowchart.dot)", default="flowchart.dot")
    parser.add_argument("-g", "--graph", help="Oluşturulacak grafik dosyasının adı (örn: flowchart.png). Format uzantıdan anlaşılır.", default=None)
    args = parser.parse_args()

    print(f"DEBUG: main fonksiyonu çağrıldı, args: {args}")

    if not os.path.exists(args.asm_file):
        print(f"HATA: Giriş dosyası '{args.asm_file}' bulunamadı.")
        return

    print(f"Assembly dosyası işleniyor: {args.asm_file}")
    dot_code = parse_m6800(args.asm_file)
    print(f"DEBUG: parse_m6800'den dönen dot_code { 'boş değil' if dot_code.strip() else 'BOŞ' }")

    if not dot_code.strip():
        print("HATA: Boş DOT kodu üretildi, grafik oluşturulmayacak.")
        return

    # Çıktı DOT dosyasının dizinini kontrol et ve yoksa oluştur
    output_dot_dir = os.path.dirname(args.output)
    if output_dot_dir and not os.path.exists(output_dot_dir):
        try:
            os.makedirs(output_dot_dir)
            print(f"DEBUG: DOT çıktı dizini oluşturuldu: {output_dot_dir}")
        except OSError as e:
            print(f"HATA: DOT çıktı dizini oluşturulamadı ({output_dot_dir}): {e}")
            return
            
    try:
        with open(args.output, 'w', encoding='utf-8') as f: # encoding eklendi
            f.write(dot_code)
        print(f"DOT dosyası oluşturuldu: {args.output}")
    except Exception as e:
        print(f"HATA: DOT dosyası yazılamadı ({args.output}): {e}")
        return


    if args.graph:
        print(f"DEBUG: Grafik oluşturma bloğuna girildi: {args.graph}")
        
        # Grafik çıktı dosyasının dizinini kontrol et ve yoksa oluştur
        output_graph_dir = os.path.dirname(args.graph)
        if output_graph_dir and not os.path.exists(output_graph_dir):
            try:
                os.makedirs(output_graph_dir)
                print(f"DEBUG: Grafik çıktı dizini oluşturuldu: {output_graph_dir}")
            except OSError as e:
                print(f"HATA: Grafik çıktı dizini oluşturulamadı ({output_graph_dir}): {e}")
                return

        try:
            output_format = args.graph.split('.')[-1].lower()
            if not output_format or output_format == args.graph.lower() or len(output_format) > 4 : #geçerli bir uzantı değilse
                output_format = "png" 
                if '.' not in args.graph:
                    args.graph += ".png"
                else: # Sadece uzantıyı değiştir, örneğin dosya.abc -> dosya.png
                    base, _ = os.path.splitext(args.graph)
                    args.graph = base + ".png"


            cmd = f"dot -T{output_format} \"{args.output}\" -o \"{args.graph}\"" # Dosya yolları için tırnak eklendi
            print(f"DEBUG: Graphviz komutu çalıştırılacak: {cmd}")

            process = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=False, encoding='utf-8', errors='replace')

            if process.returncode == 0:
                print(f"Grafik dosyası başarıyla oluşturuldu: {args.graph}")
                if process.stdout and process.stdout.strip():
                    print(f"Graphviz stdout: {process.stdout.strip()}")
                if process.stderr and process.stderr.strip(): # Bazen başarılı olsa da uyarı verebilir
                    print(f"Graphviz stderr (başarılı): {process.stderr.strip()}")
            else:
                print(f"HATA: Grafik oluşturulamadı (Graphviz hatası).")
                print(f"Komut: {cmd}")
                print(f"Dönüş Kodu: {process.returncode}")
                if process.stdout and process.stdout.strip():
                    print(f"Graphviz stdout: {process.stdout.strip()}")
                if process.stderr and process.stderr.strip():
                    print(f"Graphviz stderr: {process.stderr.strip()}")

        except FileNotFoundError:
            print(f"HATA: 'dot' komutu bulunamadı. Graphviz kurulu ve PATH'de mi? (FileNotFoundError)")
        except Exception as e:
            print(f"HATA: Grafik oluşturulamadı. Beklenmedik bir Python hatası oluştu.")
            print(f"Detay: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    main()