import json
import csv
import math

def load_rules(filename='rules.json'):
    with open(filename, 'r') as f:
        return json.load(f)

def load_katalog(filename='katalog_harga.csv'):
    katalog = {}
    with open(filename, mode='r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            jenis = row['Jenis'].strip().lower()
            ukuran = int(row['Ukuran_Kg'])
            harga = float(row['Harga_Rp'])
            
            if jenis not in katalog:
                katalog[jenis] = []
                
            harga_per_kg = harga / ukuran
            
            katalog[jenis].append({
                'id': row['ID_Barang'],
                'ukuran': ukuran,
                'harga': harga,
                'harga_per_kg': harga_per_kg
            })
            
    for jenis in katalog:
        katalog[jenis].sort(key=lambda x: (x['harga_per_kg'], -x['ukuran']))
        
    return katalog

def pencarian_heuristik(target_kg, daftar_karung):
    sisa_target = target_kg
    kombinasi = []
    total_harga = 0
    
    for karung in daftar_karung:
        if sisa_target <= 0:
            break
            
        jumlah_ambil = sisa_target // karung['ukuran']
        
        if jumlah_ambil > 0:
            subtotal = jumlah_ambil * karung['harga']
            kombinasi.append({
                'id': karung['id'],
                'ukuran': karung['ukuran'],
                'jumlah': int(jumlah_ambil),
                'subtotal': subtotal
            })
            total_harga += subtotal
            
            sisa_target %= karung['ukuran']
            
    return kombinasi, total_harga

def main():
    rules = load_rules()
    katalog = load_katalog()

    print("=== SISTEM PAKAR REKOMENDASI PEMUPUKAN ===")
    
    print("\nKomoditas tersedia: ", ", ".join(rules["tanaman"].keys()))
    komoditas = input("Pilih komoditas: ").strip().lower()
    
    kabupaten_list = list(rules["tanaman"][komoditas].keys())
    kabupaten = input(f"Pilih Kabupaten/Kota ({'/'.join(kabupaten_list)}): ").strip().title()
    
    kecamatan_list = list(rules["tanaman"][komoditas][kabupaten].keys())
    kecamatan = input(f"Pilih Kecamatan di {kabupaten} ({kecamatan_list[0]}, dll): ").strip().title()
    
    luas_lahan = float(input("Masukkan luas lahan (dalam m2): "))
    
    print("Kondisi tanah tersedia: ", ", ".join(rules["modifikator_tanah"].keys()))
    kondisi = input("Pilih kondisi tanah: ").strip().lower()

    dosis_standar_ha = rules["tanaman"][komoditas][kabupaten][kecamatan]
    faktor_koreksi = rules["modifikator_tanah"][kondisi]
    rasio_lahan = luas_lahan / 10000.0  

    print("\n\n=== HASIL REKOMENDASI ===")
    print(f"Lokasi        : {kecamatan}, {kabupaten}")
    print(f"Luas Lahan    : {luas_lahan} m2")
    print(f"Kondisi Tanah : {kondisi.capitalize()} (Faktor: {faktor_koreksi})")

    total_pupuk = {}
    total_biaya_keseluruhan = 0

    print("\n[OPTIMASI KERANJANG BELANJA]")
    for jenis_pupuk, dosis_ha in dosis_standar_ha.items():
        if dosis_ha == 0:
            continue
        
        total_kg = math.ceil(dosis_ha * rasio_lahan * faktor_koreksi)
        total_pupuk[jenis_pupuk] = total_kg
        
        print(f"\nKebutuhan {jenis_pupuk.upper()}: {total_kg} Kg")
        
        if jenis_pupuk in katalog:
            kombinasi, subtotal_biaya = pencarian_heuristik(total_kg, katalog[jenis_pupuk])
            total_biaya_keseluruhan += subtotal_biaya
            
            for item in kombinasi:
                print(f"  -> Ambil {item['jumlah']} karung {item['id']} ({item['ukuran']}kg) : Rp {item['subtotal']:,.0f}")
            print(f"  Subtotal {jenis_pupuk.upper()}: Rp {subtotal_biaya:,.0f}")
        else:
            print(f"  -> Katalog harga untuk {jenis_pupuk} tidak ditemukan!")
    
    print(f"\n>> TOTAL BIAYA KESELURUHAN: Rp {total_biaya_keseluruhan:,.0f}")

    print("\n[JADWAL APLIKASI (HST)]")
    jadwal = rules["jadwal_fase"][komoditas]
    
    for hari, rasio_pupuk in jadwal.items():
        print(f"Umur {hari} HST:")
        ada_aplikasi = False
        
        for jenis_pupuk, persentase in rasio_pupuk.items():
            if jenis_pupuk in total_pupuk and persentase > 0:
                jumlah_tabur = math.ceil(total_pupuk[jenis_pupuk] * persentase)
                print(f"  -> Tabur {jenis_pupuk.upper()}: {jumlah_tabur} kg")
                ada_aplikasi = True
                
        if not ada_aplikasi:
            print("  -> (Tidak ada aplikasi pupuk utama)")

    print("==============================================\n")

if __name__ == "__main__":
    main()