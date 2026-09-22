import sqlite3

# Sambungkan ke database perpustakaan
conn = sqlite3.connect('perpustakaan.db')
cursor = conn.cursor()

# Data 5 buku sampel (Judul, Penulis, Stok Total, Stok Tersedia)
buku_sampel = [
    ('Pemrograman Python Dasar', 'Guido van Rossum', 5, 5),
    ('Sistem Terdistribusi & Middleware', 'Andrew S. Tanenbaum', 3, 3),
    ('Algoritma dan Struktur Data', 'Donald Knuth', 4, 4),
    ('Internet of Things (IoT) dengan ESP32', 'Ahmad Rizal', 2, 2),
    ('Pengantar Basis Data & SQL', 'Eko Kurniawan', 6, 6)
]

# Cek apakah tabel buku masih kosong
cursor.execute('SELECT COUNT(*) FROM buku')
jika_kosong = cursor.fetchone()[0] == 0

if jika_kosong:
    cursor.executemany('''
        INSERT INTO buku (judul, penulis, stok_total, stok_tersedia)
        VALUES (?, ?, ?, ?)
    ''', buku_sampel)
    conn.commit()
    print("Berhasil menambahkan 5 buku sampel ke database!")
else:
    print("Database sudah memiliki data buku.")

conn.close()