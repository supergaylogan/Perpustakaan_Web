from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = 'kunci_rahasia_perpustakaan_kampus'


# ==========================================
# KONEKSI DATABASE
# ==========================================

def get_db_connection():
    conn = sqlite3.connect('perpustakaan.db')
    conn.row_factory = sqlite3.Row
    return conn


# ==========================================
# INISIALISASI DATABASE (BUKU & ANGGOTA)
# ==========================================

def inisialisasi_database():
    conn = sqlite3.connect('perpustakaan.db')
    cursor = conn.cursor()

    # 1. Tabel Buku
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS buku (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            judul TEXT NOT NULL,
            penulis TEXT NOT NULL,
            stok_total INTEGER NOT NULL,
            stok_tersedia INTEGER NOT NULL
        )
    """)

    # 2. Tabel Mahasiswa / Anggota
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mahasiswa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nim VARCHAR(15) UNIQUE,
            username VARCHAR(50) UNIQUE,
            password TEXT,
            peran VARCHAR(20) DEFAULT 'mahasiswa'
        )
    """)

    # Pastikan kolom username, password, peran tersedia jika memakai db lama
    cursor.execute("PRAGMA table_info(mahasiswa)")
    kolom_ada = [row[1] for row in cursor.fetchall()]
    if 'username' not in kolom_ada:
        cursor.execute("ALTER TABLE mahasiswa ADD COLUMN username VARCHAR(50)")
    if 'password' not in kolom_ada:
        cursor.execute("ALTER TABLE mahasiswa ADD COLUMN password TEXT")
    if 'peran' not in kolom_ada:
        cursor.execute("ALTER TABLE mahasiswa ADD COLUMN peran VARCHAR(20) DEFAULT 'mahasiswa'")

    # Lengkapi data lama jika username masih kosong
    cursor.execute("""
        UPDATE mahasiswa
        SET username = 'rivandi',
            password = ?,
            peran = 'mahasiswa'
        WHERE nim = '2310101031' AND (username IS NULL OR username = '')
    """, (generate_password_hash('123456'),))

    # Isi data sampel buku jika kosong
    cursor.execute('SELECT COUNT(*) FROM buku')
    if cursor.fetchone()[0] == 0:
        buku_sampel = [
            ('Pemrograman Python Dasar', 'Guido van Rossum', 5, 5),
            ('Sistem Terdistribusi & Middleware', 'Andrew S. Tanenbaum', 3, 3),
            ('Algoritma dan Struktur Data', 'Donald Knuth', 4, 4),
            ('Internet of Things (IoT) dengan ESP32', 'Ahmad Rizal', 2, 2),
            ('Pengantar Basis Data & SQL', 'Eko Kurniawan', 6, 6)
        ]
        cursor.executemany("""
            INSERT INTO buku (judul, penulis, stok_total, stok_tersedia)
            VALUES (?, ?, ?, ?)
        """, buku_sampel)

    # Isi akun ADMIN default sesuai flowchart
    cursor.execute("SELECT COUNT(*) FROM mahasiswa WHERE username = 'admin'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO mahasiswa (nim, username, password, peran)
            VALUES (?, ?, ?, ?)
        """, ('ADM001', 'admin', generate_password_hash('admin123'), 'admin'))

    # Isi 1 akun MAHASISWA contoh
    cursor.execute("SELECT COUNT(*) FROM mahasiswa WHERE nim = '2310101031'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO mahasiswa (nim, username, password, peran)
            VALUES (?, ?, ?, ?)
        """, ('2310101031', 'rivandi', generate_password_hash('123456'), 'mahasiswa'))

    conn.commit()
    conn.close()


inisialisasi_database()


# ==========================================
# MODUL DATA ANGGOTA: REGISTER
# ==========================================

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nim = request.form.get('nim', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        # Validasi 1: Data tidak boleh kosong (sesuai flowchart)
        if not nim or not username or not password:
            flash("Data tidak boleh kosong!", "danger")
            return render_template('register.html')

        conn = get_db_connection()

        # Validasi 2: Cek NIM sudah terdaftar (fungsi cari_anggota)
        cek_nim = conn.execute("SELECT * FROM mahasiswa WHERE nim = ?", (nim,)).fetchone()
        if cek_nim:
            conn.close()
            flash("NIM sudah terdaftar!", "warning")
            return render_template('register.html')

        # Validasi 3: Cek Username sudah dipakai
        cek_user = conn.execute("SELECT * FROM mahasiswa WHERE username = ?", (username,)).fetchone()
        if cek_user:
            conn.close()
            flash("Username sudah digunakan, pilih yang lain!", "warning")
            return render_template('register.html')

        # Simpan anggota baru dengan peran default 'mahasiswa'
        password_hash = generate_password_hash(password)
        conn.execute("""
            INSERT INTO mahasiswa (nim, username, password, peran)
            VALUES (?, ?, ?, ?)
        """, (nim, username, password_hash, 'mahasiswa'))
        conn.commit()
        conn.close()

        flash("Registrasi berhasil! Silakan login.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')


# ==========================================
# MODUL DATA ANGGOTA: LOGIN & LOGOUT
# ==========================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash("Username dan password wajib diisi!", "danger")
            return render_template('login.html')

        conn = get_db_connection()
        anggota = conn.execute("SELECT * FROM mahasiswa WHERE username = ?", (username,)).fetchone()
        conn.close()

        # Validasi 1 & 2 sesuai flowchart login(username, password)
        if anggota is None or not check_password_hash(anggota['password'], password):
            flash("Login gagal! Username atau password salah.", "danger")
            return render_template('login.html')

        # Simpan data sesi pengguna yang berhasil login
        session['user_id'] = anggota['id']
        session['nim'] = anggota['nim']
        session['username'] = anggota['username']
        session['peran'] = anggota['peran']

        flash(f"Selamat datang, {anggota['username']}!", "success")
        return redirect(url_for('beranda'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash("Anda telah berhasil logout.", "info")
    return redirect(url_for('login'))


# ==========================================
# MODUL DATA ANGGOTA: TAMPILKAN ANGGOTA
# ==========================================

@app.route('/mahasiswa')
def daftar_mahasiswa():
    conn = get_db_connection()
    semua_mahasiswa = conn.execute("""
        SELECT * FROM mahasiswa
        ORDER BY id ASC
    """).fetchall()
    conn.close()

    return render_template('daftar_mahasiswa.html', daftar_mahasiswa=semua_mahasiswa)


# ==========================================
# BERANDA + PENCARIAN BUKU
# ==========================================

@app.route('/')
def beranda():
    kata_kunci = request.args.get('cari', '').strip()
    conn = get_db_connection()

    if kata_kunci:
        daftar_buku = conn.execute("""
            SELECT * FROM buku
            WHERE judul LIKE ? OR penulis LIKE ?
            ORDER BY judul ASC
        """, (f'%{kata_kunci}%', f'%{kata_kunci}%')).fetchall()
    else:
        daftar_buku = conn.execute("""
            SELECT * FROM buku
            ORDER BY judul ASC
        """).fetchall()

    conn.close()
    return render_template('index.html', daftar_buku=daftar_buku, kata_kunci=kata_kunci)


# ==========================================
# TAMBAH, EDIT, HAPUS BUKU (KHUSUS ADMIN)
# ==========================================

@app.route('/tambah', methods=['GET', 'POST'])
def tambah_buku():
    if session.get('peran') != 'admin':
        flash("Hanya admin yang dapat menambah buku.", "warning")
        return redirect(url_for('login'))

    if request.method == 'POST':
        judul = request.form['judul'].strip()
        penulis = request.form['penulis'].strip()
        stok = int(request.form['stok'])

        conn = get_db_connection()
        conn.execute("""
            INSERT INTO buku (judul, penulis, stok_total, stok_tersedia)
            VALUES (?, ?, ?, ?)
        """, (judul, penulis, stok, stok))
        conn.commit()
        conn.close()

        return redirect(url_for('beranda'))

    return render_template('tambah_buku.html')


@app.route('/edit/<int:buku_id>', methods=['GET', 'POST'])
def edit_buku(buku_id):
    if session.get('peran') != 'admin':
        flash("Hanya admin yang dapat mengedit buku.", "warning")
        return redirect(url_for('login'))

    conn = get_db_connection()

    if request.method == 'POST':
        judul = request.form['judul'].strip()
        penulis = request.form['penulis'].strip()
        stok_baru = int(request.form['stok'])

        buku = conn.execute("SELECT * FROM buku WHERE id = ?", (buku_id,)).fetchone()
        if buku:
            jumlah_dipinjam = buku['stok_total'] - buku['stok_tersedia']
            if stok_baru >= jumlah_dipinjam:
                stok_tersedia_baru = stok_baru - jumlah_dipinjam
                conn.execute("""
                    UPDATE buku
                    SET judul = ?, penulis = ?, stok_total = ?, stok_tersedia = ?
                    WHERE id = ?
                """, (judul, penulis, stok_baru, stok_tersedia_baru, buku_id))
                conn.commit()

        conn.close()
        return redirect(url_for('beranda'))

    buku = conn.execute("SELECT * FROM buku WHERE id = ?", (buku_id,)).fetchone()
    conn.close()

    if buku is None:
        return redirect(url_for('beranda'))

    return render_template('edit_buku.html', buku=buku)


@app.route('/hapus/<int:buku_id>', methods=['POST'])
def hapus_buku(buku_id):
    if session.get('peran') != 'admin':
        flash("Hanya admin yang dapat menghapus buku.", "warning")
        return redirect(url_for('login'))

    conn = get_db_connection()
    buku = conn.execute("SELECT * FROM buku WHERE id = ?", (buku_id,)).fetchone()
    if buku:
        conn.execute("DELETE FROM buku WHERE id = ?", (buku_id,))
        conn.commit()

    conn.close()
    return redirect(url_for('beranda'))


# ==========================================
# PINJAM & KEMBALIKAN BUKU (WAJIB LOGIN)
# ==========================================

@app.route('/pinjam/<int:buku_id>', methods=['POST'])
def pinjam_buku(buku_id):
    # Wajib login sebelum meminjam buku
    if 'user_id' not in session:
        flash("Silakan login terlebih dahulu sebelum meminjam buku!", "warning")
        return redirect(url_for('login'))

    conn = get_db_connection()
    buku = conn.execute("SELECT * FROM buku WHERE id = ?", (buku_id,)).fetchone()

    if buku and buku['stok_tersedia'] > 0:
        conn.execute("""
            UPDATE buku
            SET stok_tersedia = stok_tersedia - 1
            WHERE id = ?
        """, (buku_id,))
        conn.commit()
        flash(f"Buku '{buku['judul']}' berhasil dipinjam oleh {session['username']}!", "success")

    conn.close()
    return redirect(url_for('beranda'))


@app.route('/kembalikan/<int:buku_id>', methods=['POST'])
def kembalikan_buku(buku_id):
    # Wajib login sebelum mengembalikan buku
    if 'user_id' not in session:
        flash("Silakan login terlebih dahulu untuk mengembalikan buku!", "warning")
        return redirect(url_for('login'))

    conn = get_db_connection()
    buku = conn.execute("SELECT * FROM buku WHERE id = ?", (buku_id,)).fetchone()

    if buku and buku['stok_tersedia'] < buku['stok_total']:
        conn.execute("""
            UPDATE buku
            SET stok_tersedia = stok_tersedia + 1
            WHERE id = ?
        """, (buku_id,))
        conn.commit()
        flash(f"Buku '{buku['judul']}' telah dikembalikan!", "info")

    conn.close()
    return redirect(url_for('beranda'))


if __name__ == '__main__':
    app.run(debug=True)