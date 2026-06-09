# Pengumpul Data — Soft Power & Ketahanan Ekspor Pasar Berkembang

Alat (app Streamlit) untuk **menarik dan merakit** panel data sekunder 23 pasar
berkembang (2011–2024) yang digunakan dalam studi soft power & ketahanan ekspor.
Disusun oleh **Emaridial Ulza**.

Alat ini hanya mengumpulkan dan merakit data dari penyedia resmi. Seluruh
pemodelan, analisis, dan interpretasi dilakukan terpisah oleh penulis.

---

## 1. Prasyarat

- **Python 3.10+** terpasang.
- **FRED API key** (gratis, instan): daftar di
  <https://fredaccount.stlouisfed.org/apikey>. Hanya ini yang butuh key —
  World Bank tidak butuh key.

## 2. Pasang

```bash
pip install -r requirements.txt
```

## 3. Jalankan

```bash
streamlit run app.py
```

Peramban akan terbuka otomatis (biasanya di `http://localhost:8501`).

## 4. Pakai

1. Di panel kiri, tempel **FRED API key** Anda (tersimpan di mesin Anda, tidak
   dikirim ke mana pun selain FRED).
2. Pilih **negara** dan **rentang tahun**.
3. (Opsional) Unggah sumber non-API sebagai CSV — lihat bagian Sumber di bawah.
4. Klik **Rakit panel**.
5. Periksa tabel, lalu klik **Unduh panel (CSV)** → menghasilkan `em_analysis.csv`.

---

## Sumber data

| Variabel | Sumber | Cara diperoleh |
|---|---|---|
| Ekspor (% PDB), PDB/kapita, ekspor/impor bahan bakar, enam estimasi WGI | World Bank | **Otomatis** (tanpa key) |
| Harga minyak Brent | FRED `DCOILBRENTEU` | **Otomatis** (dengan API key Anda) |
| Soft presence | Elcano Global Presence Index | Unggah CSV `iso3,year,value` |
| Risiko geopolitik negara (GPRC) & global (GPR) | Caldara–Iacoviello | Unggah CSV |
| Tekanan rantai pasok (GSCPI) | NY Fed | Unggah CSV `year,value` |
| Volatilitas pasar saham | mis. Yahoo Finance | Unggah CSV `iso3,year,value` |

**Format CSV unggahan:** kolom `iso3,year,value` untuk variabel per-negara, atau
`year,value` untuk seri global (GPR global, GSCPI, Brent). Nama kolom tidak
peka huruf besar/kecil.

> Sumber non-API diunggah karena penyedianya memublikasikan berkas (xls/csv),
> bukan API publik yang bisa ditarik otomatis lintas-situs. Unduh sekali dari
> situs resmi masing-masing, simpan sebagai CSV dengan format di atas, lalu unggah.

## Apa yang dirakit alat ini

- Menggabungkan seluruh sumber menjadi panel negara–tahun.
- Menurunkan: `fuel_net` (ekspor − impor bahan bakar), `log_gdp_pc`,
  `gov_index` (rata-rata enam estimasi WGI).
- **Soft power (residual):** residual OLS dari `log(soft presence)` terhadap
  `log_gdp_pc + gov_index + efek tetap tahun`.
- **Standardisasi** (z-score) variabel kunci.
- **Interaksi:** jalur eksposur energi `exp_* = z_fuelnet × z_shock` dan
  bantalan soft power `cush_* = z_nbrand × z_shock` untuk GPR/Brent/GSCPI.
- Tombol unduh menghasilkan `em_analysis.csv` siap-estimasi.

## Catatan

- Bila FRED key kosong atau sebuah sumber tidak diunggah, alat tetap berjalan
  dan merakit variabel yang tersedia (sisanya dilewati dengan peringatan).
- Kode indikator World Bank dan tautan sumber dapat disesuaikan di bagian atas
  `app.py`.
