import streamlit as st
import json
import csv
import math
import os

# --- 1. FUNGSI PEMUATAN DATA ---
@st.cache_data
def load_rules(filename='rules.json'):
    with open(filename, 'r') as f:
        return json.load(f)

@st.cache_data
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

# --- 2. FUNGSI HEURISTIC SEARCH ---
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

# --- 3. UI WEB APP STREAMLIT ---
def main():
    st.set_page_config(page_title="Sistem Pakar Pemupukan", layout="wide")
    
    # Load Knowledge Base
    rules = load_rules()
    katalog = load_katalog()

    # --- BAGIAN HEADER & LOGO ---
    # Silakan simpan file 'logo_uns.png' di folder yang sama dengan app.py
    if os.path.exists("logo_uns.png"):
        st.image("logo_uns.png", width=100)
    
    st.title("Sistem Reasoning & Searching Anjuran Pemupukan")
    st.markdown("Aplikasi kecerdasan buatan untuk optimasi dosis dan biaya pupuk komoditas pertanian.")
    st.divider()

    # Layout Kolom Input
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Parameter Lahan")
        komoditas_list = list(rules["tanaman"].keys())
        komoditas = st.selectbox("Pilih Komoditas", komoditas_list, format_func=lambda x: x.replace('_', ' ').title())
        
        kabupaten_list = list(rules["tanaman"][komoditas].keys())
        kabupaten = st.selectbox("Pilih Kabupaten/Kota", kabupaten_list)
        
        kecamatan_list = list(rules["tanaman"][komoditas][kabupaten].keys())
        kecamatan = st.selectbox("Pilih Kecamatan", kecamatan_list)

    with col2:
        st.subheader("Kondisi Ekstra")
        luas_lahan = st.number_input("Luas Lahan (meter persegi)", min_value=1.0, value=5000.0, step=100.0)
        
        kondisi_list = list(rules["modifikator_tanah"].keys())
        kondisi = st.selectbox("Kondisi Tanah", kondisi_list, format_func=lambda x: x.title())

    # Tombol Eksekusi
    if st.button("Hitung Rekomendasi", type="primary", use_container_width=True):
        st.divider()
        
        # --- PROSES INFERENSI ---
        dosis_standar_ha = rules["tanaman"][komoditas][kabupaten][kecamatan]
        faktor_koreksi = rules["modifikator_tanah"][kondisi]
        rasio_lahan = luas_lahan / 10000.0  

        total_pupuk = {}
        total_biaya_keseluruhan = 0

        st.subheader(f"Hasil Analisis: {kecamatan}, {kabupaten}")
        
        col_res1, col_res2 = st.columns(2)
        
        # Kolom Kiri: Kebutuhan & Optimasi Harga
        with col_res1:
            st.info("Keranjang Belanja Optimal (Heuristic Search)")
            for jenis_pupuk, dosis_ha in dosis_standar_ha.items():
                if dosis_ha == 0:
                    continue
                
                total_kg = math.ceil(dosis_ha * rasio_lahan * faktor_koreksi)
                total_pupuk[jenis_pupuk] = total_kg
                
                with st.expander(f"Kebutuhan {jenis_pupuk.upper()}: {total_kg} Kg", expanded=True):
                    if jenis_pupuk in katalog:
                        kombinasi, subtotal_biaya = pencarian_heuristik(total_kg, katalog[jenis_pupuk])
                        total_biaya_keseluruhan += subtotal_biaya
                        
                        for item in kombinasi:
                            st.write(f"- {item['jumlah']}x {item['id']} ({item['ukuran']}kg) : Rp {item['subtotal']:,.0f}")
                        st.markdown(f"**Subtotal {jenis_pupuk.upper()}: Rp {subtotal_biaya:,.0f}**")
                    else:
                        st.error(f"Katalog harga untuk {jenis_pupuk} tidak ditemukan.")
            
            st.success(f"TOTAL ESTIMASI BIAYA: Rp {total_biaya_keseluruhan:,.0f}")

        # Kolom Kanan: Jadwal Tabur
        with col_res2:
            st.warning("Kalender Penjadwalan (Forward Chaining)")
            jadwal = rules["jadwal_fase"][komoditas]
            
            for hari, rasio_pupuk in jadwal.items():
                st.write(f"**Umur {hari} HST (Hari Setelah Tanam):**")
                ada_aplikasi = False
                for jenis_pupuk, persentase in rasio_pupuk.items():
                    if jenis_pupuk in total_pupuk and persentase > 0:
                        jumlah_tabur = math.ceil(total_pupuk[jenis_pupuk] * persentase)
                        st.write(f"- Tabur **{jenis_pupuk.upper()}**: {jumlah_tabur} kg")
                        ada_aplikasi = True
                if not ada_aplikasi:
                    st.write("*(Tidak ada aplikasi pupuk utama)*")
                st.write("---")

if __name__ == "__main__":
    main()