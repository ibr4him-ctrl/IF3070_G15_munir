# IF3070 G15 Munir

Tugas Besar IF3070 — Dasar Inteligensi Artifisial, Institut Teknologi Bandung, 2026.

Proyek ini mengoptimalkan penempatan kendaraan pada geladak kapal untuk memaksimalkan total *ShippingFee* dengan mempertimbangkan batas geladak, overlap, dan kapasitas berat kapal.

## Algoritma
- Stochastic Hill Climbing (HC)
- Simulated Annealing (SA)
- Genetic Algorithm (GA)

## Anggota Kelompok
- Ibrahim Ferizarizqi Permana — 18224120
- Adham Sachadeva Purwadi — 18224030
- Muhammad Reyna Athallah Agoes — 18224112

## Setup

Pastikan Python dan pip sudah terinstal.

Buat virtual environment:

```bash
python -m venv .venv
```

Aktifkan environment:

**Windows**
```powershell
.venv\Scripts\Activate.ps1
```

**Linux/macOS**
```bash
source .venv/bin/activate
```

Instal dependensi:

```bash
python -m pip install -e .
```

## Menjalankan Program

Gunakan file konfigurasi eksperimen dan problem JSON yang tersedia di repository. Hasil eksperimen dan visualisasi disimpan di direktori `output/`.

## Struktur Repository
- `configs/` — Konfigurasi eksperimen.
- `src/` — Implementasi algoritma.
- `tests/` — Pengujian otomatis.
- `output/` — Hasil eksperimen dan visualisasi.
- `docs/` — Laporan dan dokumentasi.

## Pembagian Tugas

- **Ibrahim Ferizarizqi Permana:** Implementasi Genetic Algorithm (GA) dan Stochastic Hill Climbing (HC).
- **Adham Sachadeva Purwadi:** Implementasi Simulated Annealing (SA) serta eksperimen dan evaluasi HC/SA.
- **Muhammad Reyna Athallah Agoes:** Eksperimen variasi parameter GA, visualisasi, dan analisis hasil GA.
- **Seluruh anggota:** Integrasi sistem, validasi hasil, perbandingan algoritma, dan penyusunan laporan akhir.

Repository ini dibuat untuk keperluan akademik Tugas Besar IF3070 — Dasar Inteligensi Artifisial.