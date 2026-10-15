from datetime import date, datetime
import json
from database import get_db


class UserModel:

  @staticmethod
  def authenticate(username, password):
    with get_db() as conn:
      with conn.cursor() as cur:
        cur.execute(
            "SELECT * FROM users WHERE LOWER(username) = %s AND password = %s;",
            (username.strip().lower(), password),
        )
        row = cur.fetchone()
    return dict(row) if row else None

  @staticmethod
  def get_all_guru():
    with get_db() as conn:
      with conn.cursor() as cur:
        cur.execute("""
                    SELECT u.username, u.nama, u.password, COALESCE(t.tarif_per_jam, 0) as tarif_per_jam
                    FROM users u
                    LEFT JOIN tarif_guru t ON u.nama = t.nama
                    WHERE u.role = 'guru'
                    ORDER BY u.nama;
                """)
        rows = cur.fetchall()
    return [dict(r) for r in rows]

  @staticmethod
  def add_or_update_guru(username, password, nama, tarif=0):
    with get_db() as conn:
      with conn.cursor() as cur:
        cur.execute(
            """
                    INSERT INTO users (username, password, nama, role) 
                    VALUES (%s, %s, %s, 'guru')
                    ON CONFLICT(username) DO UPDATE SET password=EXCLUDED.password, nama=EXCLUDED.nama;
                """,
            (username.strip().lower(), password, nama),
        )

        cur.execute(
            """
                    INSERT INTO tarif_guru (nama, tarif_per_jam)
                    VALUES (%s, %s)
                    ON CONFLICT(nama) DO UPDATE SET tarif_per_jam=EXCLUDED.tarif_per_jam;
                """,
            (nama, tarif),
        )
      conn.commit()

  @staticmethod
  def delete_guru(username, nama):
    with get_db() as conn:
      with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM users WHERE username = %s;", (username,)
        )
        cur.execute("DELETE FROM tarif_guru WHERE nama = %s;", (nama,))
      conn.commit()


class JadwalModel:

  @staticmethod
  def get_all():
    with get_db() as conn:
      with conn.cursor() as cur:
        cur.execute(
            "SELECT * FROM jadwal ORDER BY tanggal DESC, jam_mulai ASC;"
        )
        rows = cur.fetchall()

    hasil = []
    for row in rows:
      d = dict(row)
      d["murid"] = (
          json.loads(d["murid"])
          if isinstance(d["murid"], str)
          else d["murid"]
      )
      d["check_in_dt"] = (
          datetime.fromisoformat(d["check_in"]) if d["check_in"] else None
      )
      d["check_out_dt"] = (
          datetime.fromisoformat(d["check_out"]) if d["check_out"] else None
      )
      hasil.append(d)
    return hasil

  @staticmethod
  def get_by_id(jadwal_id):
    with get_db() as conn:
      with conn.cursor() as cur:
        cur.execute("SELECT * FROM jadwal WHERE id = %s;", (jadwal_id,))
        row = cur.fetchone()
    if row:
      d = dict(row)
      d["murid"] = (
          json.loads(d["murid"])
          if isinstance(d["murid"], str)
          else d["murid"]
      )
      return d
    return None

  @staticmethod
  def add_jadwal(tanggal, jam_mulai, jam_selesai, guru, murid_list):
    with get_db() as conn:
      with conn.cursor() as cur:
        cur.execute(
            """
                    INSERT INTO jadwal (tanggal, jam_mulai, jam_selesai, guru, murid, status)
                    VALUES (%s, %s, %s, %s, %s, 'Terjadwal');
                """,
            (tanggal, jam_mulai, jam_selesai, guru, json.dumps(murid_list)),
        )
      conn.commit()

  @staticmethod
  def koreksi_presensi_manual(
      jadwal_id,
      tanggal,
      status,
      check_in,
      check_out,
      durasi_menit,
      pengajar_aktual,
      alasan_koreksi,
  ):
    with get_db() as conn:
      with conn.cursor() as cur:
        cur.execute(
            """
                    UPDATE jadwal
                    SET tanggal = %s, status = %s, check_in = %s, check_out = %s,
                        durasi_menit = %s, pengajar_aktual = %s, alasan_koreksi = %s
                    WHERE id = %s;
                """,
            (
                tanggal,
                status,
                check_in,
                check_out,
                durasi_menit,
                pengajar_aktual,
                alasan_koreksi,
                jadwal_id,
            ),
        )
      conn.commit()

  @staticmethod
  def set_honor_disetujui(jadwal_id, status_honor):
    with get_db() as conn:
      with conn.cursor() as cur:
        cur.execute(
            "UPDATE jadwal SET honor_disetujui = %s WHERE id = %s;",
            (status_honor, jadwal_id),
        )
      conn.commit()

  @staticmethod
  def delete_jadwal(jadwal_id):
    with get_db() as conn:
      with conn.cursor() as cur:
        cur.execute("DELETE FROM jadwal WHERE id = %s;", (jadwal_id,))
      conn.commit()

  @staticmethod
  def save(jadwal):
    with get_db() as conn:
      with conn.cursor() as cur:
        cur.execute(
            """
                    UPDATE jadwal
                    SET status = %s, check_in = %s, check_out = %s, durasi_menit = %s,
                        keterangan = %s, pengganti = %s, pengajar_aktual = %s,
                        honor_disetujui = %s, alasan_koreksi = %s
                    WHERE id = %s;
                """,
            (
                jadwal["status"],
                jadwal["check_in"],
                jadwal["check_out"],
                jadwal["durasi_menit"],
                jadwal["keterangan"],
                jadwal["pengganti"],
                jadwal["pengajar_aktual"],
                jadwal["honor_disetujui"],
                jadwal["alasan_koreksi"],
                jadwal["id"],
            ),
        )
      conn.commit()

  @staticmethod
  def save_ketidakhadiran(data):
    with get_db() as conn:
      with conn.cursor() as cur:
        cur.execute(
            """
                    INSERT INTO ketidakhadiran (jadwal_id, guru, alasan, waktu, status)
                    VALUES (%s, %s, %s, %s, %s);
                """,
            (
                data["jadwal_id"],
                data["guru"],
                data["alasan"],
                data["waktu"],
                data["status"],
            ),
        )
      conn.commit()

  @staticmethod
  def guru_aktif(jadwal):
    return jadwal["pengganti"] if jadwal["pengganti"] else jadwal["guru"]

  @staticmethod
  def hitung_durasi_aktual(jadwal, check_in_dt, waktu_selesai):
    if not check_in_dt:
      return 0
    akhir_jadwal = datetime.combine(
        check_in_dt.date(),
        datetime.strptime(jadwal["jam_selesai"], "%H:%M").time(),
    )
    akhir_efektif = min(waktu_selesai, akhir_jadwal)
    menit = (akhir_efektif - check_in_dt).total_seconds() / 60
    return max(0, round(menit))

  @staticmethod
  def format_durasi(menit):
    jam, sisa = divmod(menit, 60)
    return f"{jam} jam {sisa} menit" if jam > 0 else f"{sisa} menit"