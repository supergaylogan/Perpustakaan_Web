from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('perpustakaan.db')
    conn.row_factory = sqlite3.Row
    return conn

def inisialisasi_buku():
    conn = sqlite3.connect('perpustakaan.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM buku')
    if cursor.fetchone()[0] == 0:
        buku_sampel = [
            ('Pemrograman Python Dasar', 'Guido van Rossum', 5, 5),
            ('Sistem Terdistribusi & Middleware', 'Andrew S. Tanenbaum', 3, 3),
            ('Algoritma dan Struktur Data', 'Donald Knuth', 4, 4),
            ('Internet of Things (IoT) dengan ESP32', 'Ahmad Rizal', 2, 2),
            ('Pengantar Basis Data & SQL', 'Eko Kurniawan', 6, 6)
        ]
        cursor.executemany('''
            INSERT INTO buku (judul, penulis, stok_total, stok_tersedia)
            VALUES (?, ?, ?, ?)
        ''', buku_sampel)
        conn.commit()
    conn.close()

inisialisasi_buku()

@app.route('/')
def beranda():
    conn = get_db_connection()
    buku_dari_db = conn.execute('SELECT * FROM buku').fetchall()
    conn.close()
    return render_template('index.html', daftar_buku=buku_dari_db)

# --- FUNGSI UNTUK MENANGKAP AKSI PINJAM ---
@app.route('/pinjam/<int:buku_id>', methods=['POST'])
def pinjam_buku(buku_id):
    conn = get_db_connection()
    buku = conn.execute('SELECT stok_tersedia FROM buku WHERE id = ?', (buku_id,)).fetchone()
    
    # Kurangi stok 1 jika stoknya masih ada
    if buku and buku['stok_tersedia'] > 0:
        conn.execute('UPDATE buku SET stok_tersedia = stok_tersedia - 1 WHERE id = ?', (buku_id,))
        conn.commit()
        
    conn.close()
    return redirect(url_for('beranda'))

# --- FUNGSI BARU UNTUK MENANGKAP AKSI KEMBALIKAN ---
@app.route('/kembalikan/<int:buku_id>', methods=['POST'])
def kembalikan_buku(buku_id):
    conn = get_db_connection()
    buku = conn.execute('SELECT stok_tersedia, stok_total FROM buku WHERE id = ?', (buku_id,)).fetchone()
    
    # Tambah stok 1 selama stok tersedia belum melebihi total awal
    if buku and buku['stok_tersedia'] < buku['stok_total']:
        conn.execute('UPDATE buku SET stok_tersedia = stok_tersedia + 1 WHERE id = ?', (buku_id,))
        conn.commit()
        
    conn.close()
    return redirect(url_for('beranda'))

if __name__ == '__main__':
    app.run(debug=True)