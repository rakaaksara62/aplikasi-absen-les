import json
import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Ambil URI Supabase dari Environment Variable / fallback string
DATABASE_URL = os.environ.get(
    "DATABASE_URL"
)


def get_db():
  conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
  return conn


def init_db():
  with get_db() as conn:
    with conn.cursor() as cur:
      # Tabel Users
      cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    username VARCHAR(100) PRIMARY KEY,
                    password VARCHAR(255) NOT NULL,
                    nama VARCHAR(255) NOT NULL,
                    role VARCHAR(50) NOT NULL
                );
            """)

      # Tabel Jadwal
      cur.execute("""
                CREATE TABLE IF NOT EXISTS jadwal (
                    id SERIAL PRIMARY KEY,
                    tanggal VARCHAR(20) NOT NULL,
                    jam_mulai VARCHAR(20) NOT NULL,
                    jam_selesai VARCHAR(20) NOT NULL,
                    guru VARCHAR(255) NOT NULL,
                    murid TEXT NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    check_in VARCHAR(100),
                    check_out VARCHAR(100),
                    durasi_menit INTEGER NOT NULL DEFAULT 0,
                    keterangan TEXT NOT NULL DEFAULT '',
                    pengganti VARCHAR(255),
                    pengajar_aktual VARCHAR(255),
                    honor_disetujui INTEGER NOT NULL DEFAULT 0,
                    alasan_koreksi TEXT NOT NULL DEFAULT ''
                );
            """)

      # Tabel Tarif Guru
      cur.execute("""
                CREATE TABLE IF NOT EXISTS tarif_guru (
                    nama VARCHAR(255) PRIMARY KEY,
                    tarif_per_jam INTEGER NOT NULL DEFAULT 0
                );
            """)

      # Tabel Ketidakhadiran
      cur.execute("""
                CREATE TABLE IF NOT EXISTS ketidakhadiran (
                    id SERIAL PRIMARY KEY,
                    jadwal_id INTEGER NOT NULL,
                    guru VARCHAR(255) NOT NULL,
                    alasan TEXT NOT NULL,
                    waktu VARCHAR(100) NOT NULL,
                    status VARCHAR(50) NOT NULL
                );
            """)

      # Seed Users Default
      cur.execute("SELECT COUNT(*) as count FROM users;")
      if cur.fetchone()["count"] == 0:
        users_default = [
            ("admin", "admin", "Administrator", "admin"),
            ("raka", "123", "Raka", "guru"),
            ("dimas", "123", "Dimas", "guru"),
            ("sinta", "123", "Sinta", "guru"),
        ]
        for u, p, n, r in users_default:
          cur.execute(
              "INSERT INTO users (username, password, nama, role) VALUES (%s,"
              " %s, %s, %s);",
              (u, p, n, r),
          )

      # Seed Tarif Guru Default
      for nama, tarif in (
          ("Raka", 35000),
          ("Dimas", 35000),
          ("Sinta", 35000),
      ):
        cur.execute(
            """
                    INSERT INTO tarif_guru (nama, tarif_per_jam) 
                    VALUES (%s, %s) 
                    ON CONFLICT (nama) DO NOTHING;
                """,
            (nama, tarif),
        )

      # Seed Sample Jadwal
      cur.execute("SELECT COUNT(*) as count FROM jadwal;")
      if cur.fetchone()["count"] == 0:
        from datetime import date

        today_str = date.today().isoformat()
        data_awal = [
            (today_str, "15:00", "17:00", "Raka", ["Andi", "Budi"]),
            (today_str, "17:00", "19:00", "Raka", ["Citra"]),
            (today_str, "16:00", "18:00", "Dimas", ["Fajar", "Gilang"]),
            (today_str, "18:00", "20:00", "Sinta", ["Hana"]),
        ]
        for tgl, mulai, selesai, guru, murid in data_awal:
          cur.execute(
              """
                        INSERT INTO jadwal (tanggal, jam_mulai, jam_selesai, guru, murid, status)
                        VALUES (%s, %s, %s, %s, %s, 'Terjadwal');
                    """,
              (tgl, mulai, selesai, guru, json.dumps(murid)),
          )

    conn.commit()