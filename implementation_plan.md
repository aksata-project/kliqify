# Implementation Plan - Standardisasi & Optimalisasi Instalasi Open Source Kliqify

Dokumentasi rancangan implementasi standardisasi konfigurasi, pipeline build satu pintu, dan pembersihan direktori proyek.

---

## 1. Konfigurasi Terpusat (`config.json` & `config.example.json`)
- **Tujuan:** Menghindari hardcode domain dan URL Google Apps Script yang tersebar di banyak file Python dan HTML.
- **Implementasi:**
  - `config.example.json` sebagai blueprint publik untuk pengguna baru open-source.
  - `config.json` dibaca secara otomatis oleh seluruh modul build.

---

## 2. Master Build Script (`build_all.py`)
- **Tujuan:** Pengguna tidak perlu menjalankan `build_landing.py`, `build_dashboard_spa.py`, dan `build_continue.py` secara terpisah.
- **Implementasi:**
  - 1 perintah eksekusi: `python build_all.py`
  - Mengompilasi seluruh file `.html` menjadi template Blogger `.xml` dalam sekali jalan (0.06 detik).

---

## 3. Restrukturisasi Direktori (`tools/`)
- Memindahkan file utilitas/eksperimen pengembangan internal ke folder `tools/`:
  - `tools/check_tags.py`
  - `tools/validate_xml.py`
  - `tools/test_syntax.js`
  - `tools/refactor_admin4.js`
  - `tools/refactor_admin4.py`
  - `tools/debug_script.js`
  - `tools/script_1.js`
- Root direktori kini bersih, rapi, dan mudah dinavigasi oleh pengguna baru.

---

## 4. Panduan Cepat (Quick Start) di README.md
- Menambahkan panduan 3 langkah mudah:
  1. `cp config.example.json config.json`
  2. `python build_all.py`
  3. `python -m http.server 8000`

