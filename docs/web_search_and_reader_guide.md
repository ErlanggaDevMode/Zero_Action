# Panduan Fitur Web Search & Webpage Reader — Zero Action CLI

Dokumen ini menjelaskan cara menggunakan, menguji secara manual, serta memverifikasi fitur **Web/Browser Tooling Agent & Documentation Fetcher** pada Zero Action CLI.

---

## 1. Deskripsi Fitur

Fitur ini memungkinkan Zero Action mencari informasi terbaru secara real-time dari internet dan membaca konten halaman dokumentasi secara bersih. 

Keunggulan utama fitur ini:
- **Bypass Pemblokiran DNS (Internet Positif Bypass):** Menggunakan DNS-over-HTTPS (DoH) Google untuk mengambil IP asli DuckDuckGo secara dinamis ketika terjadi DNS Hijacking.
- **Bypass SSL Verification Issue:** Memiliki fallback otomatis ke unverified SSL context jika terjadi kesalahan verifikasi sertifikat lokal.
- **HTML Entity Unescaper:** Otomatis mengubah entitas HTML mentah (seperti `&mdash;` -> `—`, `&bull;` -> `•`) menjadi karakter plain text yang rapi dan nyaman dibaca.
- **Integrasi Memori REPL:** Hasil pencarian/bacaan otomatis diinjeksikan langsung sebagai system context ke dalam database memori chat aktif.

---

## 2. Cara Penggunaan Fitur

### A. Melalui Perintah CLI Langsung
Kamu dapat menjalankan perintah ini langsung dari terminal sistem/PowerShell:

1. **Pencarian Web (`zero search`)**
   Mencari informasi di DuckDuckGo dan menyajikan hasilnya dalam Rich Table.
   ```bash
   zero search "fastapi background tasks"
   ```

2. **Membaca Halaman Dokumentasi (`zero read`)**
   Mengambil teks mentah yang bersih dari tag HTML, skrip iklan, navbar, header, atau footer.
   ```bash
   zero read "https://fastapi.tiangolo.com/tutorial/background-tasks/"
   ```

---

### B. Melalui Slash Commands di Interactive Chat REPL
Ketika berada di dalam sesi percakapan interaktif (`zero chat`), kamu bisa memanggil fitur ini di tengah obrolan:

1. **Masuk ke Sesi Chat:**
   ```bash
   zero chat
   ```

2. **Cari Informasi di Web:**
   Ketik perintah berikut untuk mencari informasi. Hasil pencarian teratas akan **otomatis diinjeksikan** ke memori AI:
   ```text
   zero-action > /search fastapi background tasks
   ```

3. **Membaca Dokumentasi & Bertanya:**
   Ketik perintah berikut untuk membaca dokumentasi API tertentu. Konten halaman web akan **otomatis disisipkan** ke riwayat chat, sehingga kamu bisa langsung memerintahkan AI untuk memprogram berdasarkan halaman tersebut:
   ```text
   zero-action > /read https://fastapi.tiangolo.com/tutorial/background-tasks/
   zero-action > buatkan contoh kode background task fastapi berdasarkan dokumentasi di atas.
   ```

---

## 3. Cara Pengujian Manual (Manual Testing)

Gunakan skenario pengujian di bawah ini untuk memverifikasi fungsionalitas fitur secara langsung:

### Skenario 1: Verifikasi Integrasi Tampilan Tabel Pencarian
1. Jalankan perintah pencarian web:
   ```bash
   zero search "python 3.12 release notes"
   ```
2. **Kriteria Sukses:** Output menampilkan judul tabel `Web Search Results for 'python 3.12 release notes'` berisi kolom **Index**, **Title & URL**, dan **Snippet** yang terformat rapi dan sejajar.

### Skenario 2: Verifikasi Ekstraksi Teks Bersih & Unescape Halaman Web
1. Jalankan perintah baca pada halaman web yang kaya akan markup entitas dan list (seperti KBBI):
   ```bash
   zero read "https://kbbi.co.id"
   ```
2. **Kriteria Sukses:** Output berada dalam kotak panel hijau `Webpage Context`. Periksa teks di dalamnya:
   - Tidak ada kode tag HTML mentah seperti `<p>`, `<a>`, `<script>`.
   - Entitas HTML seperti `&mdash;` telah ter-unescape dengan sukses menjadi dash panjang `—`.
   - Entitas bullet point `&bull;` telah berubah menjadi simbol dot tebal `•`.

### Skenario 3: Verifikasi Bypass DNS & SSL Fallback (Internet Positif Bypass)
1. Matikan VPN atau gunakan koneksi internet lokal (seperti IndiHome atau Telkomsel) yang memblokir DuckDuckGo.
2. Jalankan pencarian web:
   ```bash
   zero search "api flask"
   ```
3. **Kriteria Sukses:** 
   - Konsol log menampilkan pemberitahuan fallback:
     `DuckDuckGo blocked or failed. Resolving via DNS-over-HTTPS fallback.`
   - Hasil pencarian tetap tampil dengan sukses dan berisi link-link asli, bukan halaman eror Internet Positif.

### Skenario 4: Verifikasi Injeksi Konteks Sesi Chat
1. Jalankan `zero chat`.
2. Masukkan perintah baca halaman web:
   ```text
   zero-action > /read https://fastapi.tiangolo.com/tutorial/background-tasks/
   ```
3. Pastikan muncul indikator:
   `[dim green](Webpage contents injected into chat memory)[/dim green]`
4. Masukkan prompt:
   ```text
   zero-action > Tuliskan kembali tutorial singkat dari halaman tersebut.
   ```
5. **Kriteria Sukses:** AI asisten mampu menjawab dengan tepat informasi spesifik dari halaman tersebut sekalipun model AI tersebut tidak dilatih dengan data real-time terbaru.

---

## 4. Cara Menjalankan Automated Test Suite

Untuk menjalankan pengujian unit otomatis menggunakan pytest:

1. **Jalankan Uji Unit Fitur Search/Read:**
   ```bash
   uv run pytest tests/unit/test_search_service.py tests/cli/test_search_commands.py
   ```

2. **Jalankan Seluruh Test Suite Project (95 Tests):**
   ```bash
   uv run pytest
   ```

3. **Jalankan Static Checks (Ruff Linter & Mypy Type Checker):**
   ```bash
   uv run ruff check zero tests
   uv run mypy zero tests --ignore-missing-imports
   ```
