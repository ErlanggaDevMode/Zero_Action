# ⚡ Zero Action - Panduan Master Fitur Lengkap

Selamat datang di **Panduan Master Fitur Lengkap** untuk **Zero Action**. Dokumen ini dirancang sebagai manual teknis komprehensif yang mengulas seluruh fitur, arsitektur, cara penggunaan, serta metode pengujian manual untuk setiap fitur di ekosistem Zero Action.

---

## 1. Arsitektur & Tech Stack

Zero Action adalah **AI Development Partner CLI** kelas produksi yang mengusung prinsip *Modular, Domain-Driven Design* dengan pemisahan tanggung jawab yang ketat (*separation of concerns*).

### A. Tech Stack Utama
- **CLI Framework:** Typer (berbasis Click) untuk routing perintah instan.
- **Terminal UI:** Rich untuk rendering Markdown, tabel berwarna, panel, ASCII logo, dan loader animasi.
- **AI Orchestrator:** LiteLLM untuk integrasi ke puluhan penyedia model (OpenAI, Anthropic, Gemini, Ollama, dll).
- **Database & RAG:** SQLite (dengan custom C-extension/SQL function untuk *cosine similarity* pencarian vektor).
- **Quality Assurance:** Pytest, Ruff (linter/formatter), dan Mypy (type checking).

### B. Struktur Direktori
- `zero/cli/`: Layer CLI tipis untuk parsing argumen dan routing perintah (banned global heavy imports untuk menjamin booting < 300ms).
- `zero/services/`: Core logic (AI wrapper, logger, config manager, search).
- `zero/memory/` & `zero/storage/`: SQLite database layer untuk persistensi chat session, embedding vector store, dan keputusan arsitektur.
- `zero/repository/`: Pemindai codebase (bahasa, framework, git dirty state).

---

## 2. Pemasangan & Konfigurasi Awal

### A. Setup Lingkungan Pengembangan
1. Sinkronisasi dependency menggunakan `uv`:
   ```bash
   uv sync
   ```
2. Jalankan setup wizard interaktif untuk memasukkan API Key dan memilih provider default:
   ```bash
   zero setup
   ```
   *(Pilih provider seperti OpenAI, OpenRouter, Anthropic, Gemini, atau Ollama)*

---

## 3. Direktori Fitur, Cara Pakai, & Uji Manual

Berikut adalah daftar lengkap seluruh fitur di Zero Action beserta instruksi cara penggunaan dan cara melakukan pengujian manual.

---

### FITUR 1: Inisialisasi & Pengenalan Context (`zero init`)
- **Deskripsi:** Memindai codebase lokal untuk mendeteksi bahasa pemrograman, file struktur, git log, serta membagi file menjadi chunk teks dan menyimpannya sebagai embedding vektor ke SQLite (`~/.zero/memory.db`).
- **Cara Penggunaan:**
  ```bash
  zero init
  ```
- **Cara Uji Manual:**
  1. Hapus database memori lama (jika ada) di `~/.zero/memory.db`.
  2. Jalankan `zero init` di root project.
  3. **Kriteria Sukses:** CLI menampilkan scanning progress file, mendeteksi bahasa (misal: Python), dan menampilkan jumlah file ter-index serta log indexing vector sukses ke database.

---

### FITUR 2: Tanya Jawab Satu Arah (`zero ask`)
- **Deskripsi:** Perintah instan Q&A satu kali eksekusi yang mengambil konteks semantik dari database vektor lokal dan menanyakan ke AI.
- **Cara Penggunaan:**
  ```bash
  zero ask "Bagaimana cara melakukan registrasi provider di zero action?"
  ```
- **Cara Uji Manual:**
  1. Jalankan perintah di atas.
  2. **Kriteria Sukses:** Spinner loader dynamic dots `⠋ Thinking (X.Xs)...` muncul menghitung waktu, lalu teks jawaban terformat Markdown dicetak dengan referensi kode yang sesuai.

---

### FITUR 3: Konsol REPL Interaktif (`zero chat`)
- **Deskripsi:** Sesi chat interaktif dengan riwayat percakapan persisten, antarmuka gaya Claude Code, loader latency real-time, dan dukungan slash commands (`/help`, `/exit`, `/test`, `/pr`, `/search`, `/read`, dll).
- **Cara Penggunaan:**
  ```bash
  zero chat
  ```
- **Cara Uji Manual:**
  1. Jalankan `zero chat`.
  2. Pastikan muncul Welcome Panel crimson-gold mewah dan ASCII logo "ZERO ACTION".
  3. Tekan sembarang tombol untuk masuk. Kirim pesan biasa.
  4. Ketik `/help` untuk melihat seluruh command terdaftar.
  5. **Kriteria Sukses:** Sesi chat merespons secara streaming dengan spinner timer yang akurat pada awal pemrosesan token pertama.

---

### FITUR 4: Pencarian Web Canggih & Anti-Blokir (`/search` / `zero search`)
- **Deskripsi:** Mencari info terkini di web menggunakan DuckDuckGo HTML dengan mekanisme bypass blokir DNS (Internet Positif Bypass via Google DoH) dan bypass sertifikat SSL gagal.
- **Cara Penggunaan:**
  - CLI: `zero search "fastapi tutorial"`
  - REPL Chat: `/search fastapi tutorial`
- **Cara Uji Manual:**
  1. Matikan VPN Anda dan gunakan koneksi seluler/IndiHome lokal (yang memblokir DuckDuckGo).
  2. Jalankan `/search fastapi tutorial` di dalam chat REPL.
  3. **Kriteria Sukses:** Log CLI menampilkan info fallback DoH: `DuckDuckGo blocked or failed. Resolving via DNS-over-HTTPS fallback.` Hasil pencarian tetap tampil sukses dalam format tabel Rich dan otomatis terinjeksi ke histori obrolan aktif.

---

### FITUR 5: Pembaca Konten Halaman Bersih (`/read` / `zero read`)
- **Deskripsi:** Mengambil teks utama halaman web, melucuti navbar, skrip iklan, CSS, stylesheet, serta menerjemahkan entitas HTML mentah (unescape `&mdash;`, `&bull;`, dll) menjadi teks bersih readable.
- **Cara Penggunaan:**
  - CLI: `zero read "https://fastapi.tiangolo.com/tutorial/background-tasks/"`
  - REPL Chat: `/read "https://fastapi.tiangolo.com/tutorial/background-tasks/"`
- **Cara Uji Manual:**
  1. Jalankan `/read https://kbbi.co.id` di chat.
  2. **Kriteria Sukses:** Teks bersih termuat dalam panel hijau. Entitas bullet point `&bull;` sukses terjemah menjadi `•` dan dash `&mdash;` sukses terjemah menjadi `—`.

---

### FITUR 6: Agentic Software Lifecycle (`zero plan`, `zero architect`, `zero code`)
- **Deskripsi:** Rantai kerja otomatis terstruktur dari konsepsi ide hingga pembuatan file kode implementasi.
  1. `zero plan`: Meminta AI membuat dokumen Product Requirements Document (`docs/prd.md`).
  2. `zero architect`: Membaca PRD dan merancang struktur database serta diagram sistem (`docs/architecture.md`).
  3. `zero code`: Membaca desain arsitektur dan menulis kode program riil ke file yang ditargetkan.
- **Cara Penggunaan:**
  ```bash
  zero plan --requirements "Buat sistem otentikasi JWT"
  zero architect
  zero code
  ```
- **Cara Uji Manual:**
  1. Jalankan `zero plan` dengan requirement baru.
  2. Jalankan `zero architect` lalu jalankan `zero code`.
  3. **Kriteria Sukses:** File `docs/prd.md`, `docs/architecture.md`, dan file kode (misal `auth.py`) berhasil ditulis. Kode program yang digenerasi sepenuhnya sesuai dengan spesifikasi arsitektur yang dirancang.

---

### FITUR 7: Review Kode & Auto-Fixer (`zero review`, `zero fix`)
- **Deskripsi:** Memindai file sumber untuk mencari celah keamanan/performa, menulis laporannya, dan mengaplikasikan patch perbaikan melalui visualisasi git diff interaktif.
- **Cara Penggunaan:**
  ```bash
  zero review --file zero/services/search.py
  zero fix --file zero/services/search.py --review docs/review.md
  ```
- **Cara Uji Manual:**
  1. Jalankan `zero review` pada file target.
  2. Jalankan `zero fix` menargetkan laporan review tersebut.
  3. **Kriteria Sukses:** Sistem menampilkan preview visual perbandingan baris kode (`-` merah, `+` hijau) dan menanyakan konfirmasi `Apply this fix? [Y/n]`. Jika dikonfirmasi Ya, file sukses dimodifikasi secara akurat.

---

### FITUR 8: Uji Coba Mandiri & Auto-Healing Suite (`/test` / `zero test`)
- **Deskripsi:** Menjalankan test runner (misal pytest) di latar belakang. Jika terjadi kegagalan, ia mem-parsing tumpukan error tracebacks untuk menemukan file yang rusak, meminta AI membuat diff perbaikan, menambalnya, dan menguji ulang secara berulang (iterasi) hingga semua tes lolos.
- **Cara Penggunaan:**
  - CLI: `zero test --command "pytest"`
  - REPL Chat: `/test ruff check zero tests`
- **Cara Uji Manual:**
  1. Sengaja buat satu kesalahan sintaksis di salah satu unit test (misal `assert False`).
  2. Jalankan `zero test --command "pytest"`.
  3. **Kriteria Sukses:** Program mendeteksi kegagalan tes, membaca traceback fail, meminta LLM memperbaikinya, menyajikan diff perbaikan, mengaplikasikannya, dan setelah itu pengujian ulang berjalan secara otomatis hingga tes kembali hijau (sukses).

---

### FITUR 9: Auto-Pilot Pull Request & Git Git-Flow (`/pr` / `zero pr`)
- **Deskripsi:** Menganalisis diff modifikasi git lokal, mencabangkan branch baru dengan nama deskriptif dari AI, membuat commit message berstandar Conventional Commits, melakukan push ke origin remote, dan membuat Pull Request langsung lewat GitHub CLI `gh` (atau fallback link perbandingan web).
- **Cara Penggunaan:**
  - CLI: `zero pr`
  - REPL Chat: `/pr`
- **Cara Uji Manual:**
  1. Modifikasi sedikit sebuah file di repository (buat status git menjadi dirty).
  2. Jalankan `/pr` di konsol chat.
  3. **Kriteria Sukses:** AI menyarankan nama branch baru dan commit message berstandar Conventional Commit (misal `feat(search): add ssl verify fallback...`). Jika disetujui, branch dibuat, perubahan di-commit, di-push, dan PR sukses dirancang.

---

## 4. Cara Menjalankan Automated Test Project

Seluruh fitur di atas didukung penuh oleh test suite otomatis. Jalankan perintah berikut untuk memvalidasinya:

```bash
# 1. Menjalankan seluruh 95 Unit & Integration Tests
uv run pytest

# 2. Menjalankan linter Ruff (memastikan tidak ada dead code atau unused imports)
uv run ruff check zero tests

# 3. Menjalankan static type safe validator Mypy
uv run mypy zero tests --ignore-missing-imports
```
*(Pastikan status test suite selalu 100% lulus sebelum melakukan commit perubahan).*
