# Kliqify - URL Shortener & Link Monetization Platform

**Kliqify** adalah platform *URL Shortener* dan monetisasi tautan yang memungkinkan pengguna menghasilkan pendapatan dari setiap klik tautan. Platform ini dirancang dengan arsitektur *serverless* tanpa biaya server bulanan, memanfaatkan **Frontend Statis / Template Blogger**, **Google Apps Script (GAS)** sebagai backend API, dan **Google Sheets** sebagai database.

---

## ⚡ Panduan Cepat (Quick Start)

Hanya perlu 3 langkah mudah untuk mulai menjalankan atau mengembangkan proyek ini:

### 1. Salin Konfigurasi
Salin file konfigurasi contoh `config.example.json` menjadi `config.json`:
```powershell
cp config.example.json config.json
```
Sesuaikan `app_url` (domain website Anda) dan `gas_app_url` (URL Google Apps Script Anda) di dalam file `config.json`.

### 2. Kompilasi Template (Satu Perintah)
Jalankan master build script untuk mengompilasi semua halaman HTML ke template Blogger XML secara otomatis:
```powershell
python build_all.py
```

### 3. Jalankan Server Lokal
Uji coba langsung di localhost:
```powershell
python -m http.server 8000
```
Buka browser di [http://localhost:8000/landingpage.html](http://localhost:8000/landingpage.html) atau [http://localhost:8000/dashboard.html](http://localhost:8000/dashboard.html).

---

## 🚀 Fitur Utama

- **URL Shortener Cerdas:** Pembuatan tautan pendek dengan kode 6 karakter unik, validasi URL ketat, serta proteksi anti-spam (*cooldown* 1 menit & batas harian).
- **Monetized Interstitial Page (`continue.html`):** Halaman perantara iklan berbayar dengan *countdown timer*, slot iklan responsif, tombol verifikasi, dan pengalihan otomatis (*redirect*) ke URL tujuan.
- **Dashboard Single Page Application (SPA):**
  - **Role User:** Ringkasan saldo, grafik analitik klik harian (*Chart.js*), manajemen link pendek, sistem referral, dan formulir penarikan dana (*Withdraw*).
  - **Role Admin:** Manajemen seluruh pengguna, persetujuan (*approval*) penarikan saldo, kontrol pengumuman (*Announcement*), dan konfigurasi sistem.
- **Sistem Otentikasi:** Login, registrasi akun, dan validasi sesi berbasis token/localStorage.
- **Pipeline Kompilasi Blogger XML:** Script otomatis untuk mengubah file HTML mentah menjadi template XML Blogger dengan proteksi JavaScript obfuscation dan pembersihan entitas XML.

---

## 📁 Struktur Proyek

```text
kliqify/
├── config.example.json      # Template konfigurasi publik
├── config.json              # File konfigurasi aktif lokal
├── build_all.py             # Master build script (satu pintu compile semua template)
│
├── landingpage.html         # Halaman utama (Landing Page publik)
├── landingpage.xml          # Template XML Landing Page untuk Blogger
├── dashboard.html           # Antarmuka Dashboard SPA (User & Admin)
├── dashboard.xml            # Template XML Dashboard untuk Blogger
├── login-register.html      # Halaman Login & Pendaftaran Akun
├── continue.html            # Halaman perantara iklan & pengalihan link
├── continue.xml             # Template XML Continue untuk Blogger
│
├── build_landing.py         # Sub-compiler landingpage.html -> landingpage.xml
├── build_dashboard_spa.py   # Sub-compiler dashboard.html -> dashboard.xml
├── build_continue.py        # Sub-compiler continue.html -> continue.xml
│
├── code.gs.txt              # Script Backend utama Google Apps Script (GAS API)
├── setup.gs.txt             # Konfigurasi database Sheets & pemetaan kolom
├── spa_script.js            # Logika script pendukung SPA Dashboard
│
├── tools/                   # Kumpulan skrip utilitas & validator pengembang
│   ├── check_tags.py
│   ├── validate_xml.py
│   ├── test_syntax.js
│   ├── refactor_admin4.js
│   └── ...
└── README.md                # Dokumentasi proyek
```

---

## 🛠️ Prasyarat

- **Python 3.x** (untuk menjalankan server lokal dan script build)
- **Browser Modern** (Google Chrome, Microsoft Edge, Firefox, dll.)
- **Koneksi Internet** (diperlukan untuk memuat CDN Font, Icon, Chart.js, dan API Google Apps Script)
- **Akun Google** (jika ingin men-deploy backend Google Apps Script & Sheets sendiri)

---

## 💻 Pengujian di Localhost

| Halaman | URL Localhost | Keterangan |
| :--- | :--- | :--- |
| **Landing Page** | [http://localhost:8000/landingpage.html](http://localhost:8000/landingpage.html) | Halaman beranda utama |
| **Dashboard** | [http://localhost:8000/dashboard.html](http://localhost:8000/dashboard.html) | Dashboard User & Admin SPA |
| **Login / Register** | [http://localhost:8000/login-register.html](http://localhost:8000/login-register.html) | Autentikasi akun |
| **Continue (Ad Page)** | [http://localhost:8000/continue.html](http://localhost:8000/continue.html) | Pengujian halaman redirect & iklan |

> **Alternatif Node.js:** Anda juga bisa menggunakan `npx serve .` atau ekstensi **Live Server** di VS Code.

---

## ☁️ Setup Backend (Google Apps Script & Sheets)

Jika ingin menghubungkan proyek ke database Google Spreadsheet milik Anda sendiri:

1. Buat **Google Spreadsheet** baru di Google Drive.
2. Buka menu **Extensions > Apps Script** pada Spreadsheet tersebut.
3. Buat file baru di editor Apps Script:
   - Buat `setup.gs` dan salin isi dari [`setup.gs.txt`](setup.gs.txt).
   - Buat `code.gs` dan salin isi dari [`code.gs.txt`](code.gs.txt).
4. Ubah nilai `CONFIG.SPREADSHEET_ID` pada `setup.gs` dengan ID Spreadsheet Anda.
5. Klik **Deploy > New deployment**:
   - Pilih jenis: **Web app**
   - Execute as: **Me**
   - Who has access: **Anyone**
6. Salin URL Web App yang dihasilkan (`https://script.google.com/macros/s/.../exec`).
7. Masukkan URL tersebut ke variabel `gas_app_url` di file [`config.json`](config.json), lalu jalankan `python build_all.py`.

---

## 🔒 Keamanan & Anti-Spam

- **Cooldown Proteksi:** User dibatasi jeda minimal 1 menit antar pembuatan shortlink untuk mencegah spam/bot.
- **Daily Limit:** Maksimal 20 link per hari untuk setiap akun pengguna terdaftar.
- **JS Obfuscation:** Script frontend di-encode dengan Base64 + URL-encode pada saat build XML untuk melindungi logika kode.

---

## 📄 Lisensi

Proyek ini dikembangkan oleh **Cokro Aksata Nusantara**.
