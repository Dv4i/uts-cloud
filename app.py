from flask import Flask, render_template, request, redirect, url_for
import pymysql
import boto3
import os
from werkzeug.utils import secure_filename
import uuid
from dotenv import load_dotenv

app = Flask(__name__)

load_dotenv()

# ======= KONFIGURASI DATABASE =======
DB_HOST = "data-uts.cx2auqo28uk0.ap-southeast-2.rds.amazonaws.com"
DB_USER = "admin"
DB_PASSWORD = "nara0806"
DB_NAME = "kesehatan"

# ======= KONFIGURASI AWS S3 =======
S3_BUCKET = "uts-bucket-alon"  # Ganti dengan bucket S3 kamu
S3_REGION = "ap-southeast-2"    # Region bucket
AWS_ACCESS_KEY= os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

s3_client = boto3.client(
    's3',
    region_name=S3_REGION,
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

# ======= KONEKSI MYSQL =======
def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )

# ======= HALAMAN INDEX =======
@app.route('/')
def index():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM konsultasi_pasien")
        pasien = cursor.fetchall()
    conn.close()
    return render_template('index.html', pasien=pasien)

# ======= TAMBAH DATA =======
@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        nama = request.form['nama']
        email = request.form['email']
        keluhan = request.form['keluhan']
        foto_url = None

        if 'foto' in request.files and request.files['foto'].filename != '':
            foto = request.files['foto']
            filename = secure_filename(foto.filename)
            unique_filename = str(uuid.uuid4()) + "_" + filename
            s3_client.upload_fileobj(foto, S3_BUCKET, unique_filename)
            foto_url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{unique_filename}"

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO konsultasi_pasien (nama, email, keluhan, foto_url)
                VALUES (%s, %s, %s, %s)
            """, (nama, email, keluhan, foto_url))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    return render_template('add.html')

# ======= EDIT DATA =======
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM konsultasi_pasien WHERE id=%s", (id,))
        pasien = cursor.fetchone()

    if request.method == 'POST':
        nama = request.form['nama']
        email = request.form['email']
        keluhan = request.form['keluhan']
        foto_url = pasien['foto_url']

        if 'foto' in request.files and request.files['foto'].filename != '':
            foto = request.files['foto']
            filename = secure_filename(foto.filename)
            unique_filename = str(uuid.uuid4()) + "_" + filename
            s3_client.upload_fileobj(foto, S3_BUCKET, unique_filename)
            foto_url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{unique_filename}"

        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE konsultasi_pasien
                SET nama=%s, email=%s, keluhan=%s, foto_url=%s
                WHERE id=%s
            """, (nama, email, keluhan, foto_url, id))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    conn.close()
    return render_template('edit.html', pasien=pasien)

# ======= HAPUS DATA =======
@app.route('/delete/<int:id>')
def delete(id):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM konsultasi_pasien WHERE id=%s", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
