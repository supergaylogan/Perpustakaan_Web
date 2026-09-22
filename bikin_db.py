import sqlite3

# 1. Membuat dan menyambung ke file database (otomatis terbuat jika belum ada)
koneksi = sqlite3.connect('perpustakaan.db')
cursor = koneksi.cursor()

# 2. Perintah SQL untuk mengeksekusi pembuatan tabel Mahasiswa
cursor.execute('''
CREATE TABLE IF NOT EXISTS mahasiswa (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nim VARCHAR(15) UNIQUE,
    nama VARCHAR(100),
    email VARCHAR(100)
)
''')

# Perintah SQL untuk tabel Buku
cursor.execute('''
CREATE TABLE IF NOT EXISTS buku (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    judul VARCHAR(150),
    penulis VARCHAR(100),
    stok_total INTEGER,
    stok_tersedia INTEGER
)
''')

# Perintah SQL untuk tabel Peminjaman
cursor.execute('''
CREATE TABLE IF NOT EXISTS peminjaman (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mahasiswa_id INTEGER,
    buku_id INTEGER,
    tanggal_pinjam DATE,
    tanggal_tenggat DATE,
    tanggal_kembali DATE,
    status VARCHAR(20),
    denda INTEGER DEFAULT 0,
    FOREIGN KEY(mahasiswa_id) REFERENCES mahasiswa(id),
    FOREIGN KEY(buku_id) REFERENCES buku(id)
)
''')

# 3. Menyimpan perubahan secara permanen dan menutup koneksi
koneksi.commit()
koneksi.close()

print("Database dan 3 tabel berhasil dibuat tanpa XAMPP!")