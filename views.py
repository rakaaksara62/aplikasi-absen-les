from datetime import date, datetime
import flet as ft
from models import JadwalModel, UserModel


class Views:

  @staticmethod
  def login_view(app_controller):
    username = ft.TextField(label="Username", width=320)
    password = ft.TextField(label="Password", password=True, width=320)
    error = ft.Text("", color=ft.Colors.RED)

    def handle_login(e):
      user = UserModel.authenticate(username.value, password.value)
      if user:
        app_controller.set_user(user)
      else:
        error.value = "Username atau password salah."
        app_controller.page.update()

    return [
        ft.Column(
            [
                ft.Text(
                    "Sistem Absensi Pusat Les", size=28, weight=ft.FontWeight.BOLD
                ),
                ft.Text("Login App", size=20),
                username,
                password,
                ft.Button(content=ft.Text("Login"), on_click=handle_login),
                error,
                ft.Text("Guru: raka / 123", size=12, color=ft.Colors.GREY),
                ft.Text("Admin: admin / admin", size=12, color=ft.Colors.GREY),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    ]

  @staticmethod
  def teacher_dashboard_view(app_controller, user):
    today_str = date.today().isoformat()
    jadwal_list = JadwalModel.get_all()

    jadwal_hari_ini = [
        j
        for j in jadwal_list
        if JadwalModel.guru_aktif(j) == user["nama"]
        and j["tanggal"] == today_str
        and j["status"] != "Selesai"
    ]

    histori_jadwal = [
        j
        for j in jadwal_list
        if j["pengajar_aktual"] == user["nama"]
        and (j["tanggal"] < today_str or j["status"] == "Selesai")
    ]

    total_menit = sum(j["durasi_menit"] for j in histori_jadwal)

    controls = [
        ft.Text(f"Halo, {user['nama']}", size=28, weight=ft.FontWeight.BOLD),
        ft.Text(
            f"Total Durasi Mengajar Selesai:"
            f" {JadwalModel.format_durasi(total_menit)}"
        ),
        ft.Divider(),
        ft.Text(
            "📅 Jadwal Mengajar Hari Ini", size=20, weight=ft.FontWeight.BOLD
        ),
    ]

    if not jadwal_hari_ini:
      controls.append(ft.Text("Tidak ada jadwal aktif untuk hari ini."))

    for j in jadwal_hari_ini:
      controls.append(Views._buat_kartu_guru(app_controller, j, user))

    controls.extend([
        ft.Divider(),
        ft.Text(
            "📜 Histori & Riwayat Mengajar", size=20, weight=ft.FontWeight.BOLD
        ),
    ])

    if not histori_jadwal:
      controls.append(ft.Text("Belum ada histori mengajar."))

    for j in histori_jadwal:
      controls.append(
          ft.Card(
              content=ft.Container(
                  content=ft.Column([
                      ft.Text(
                          f"Tanggal: {j['tanggal']} | {j['jam_mulai']} -"
                          f" {j['jam_selesai']}",
                          weight=ft.FontWeight.BOLD,
                      ),
                      ft.Text(f"Murid: {', '.join(j['murid'])}"),
                      ft.Text(
                          f"Status: {j['status']} | Durasi:"
                          f" {JadwalModel.format_durasi(j['durasi_menit'])}"
                      ),
                  ]),
                  padding=12,
              )
          )
      )

    controls.extend([
        ft.Divider(),
        ft.Button(
            content=ft.Text("Laporkan Tidak Bisa Mengajar"),
            on_click=lambda e: app_controller.navigate("absence_form"),
        ),
        ft.Button(
            content=ft.Text("Logout"),
            on_click=lambda e: app_controller.logout(),
        ),
    ])
    return controls

  @staticmethod
  def _buat_kartu_guru(app_controller, j, user):
    is_sub = j["pengganti"] == user["nama"]
    sub_info = f" (Menggantikan {j['guru']})" if is_sub else ""

    card_content = [
        ft.Text(
            f"{j['jam_mulai']} - {j['jam_selesai']}{sub_info}",
            size=18,
            weight=ft.FontWeight.BOLD,
        ),
        ft.Text(f"Murid: {', '.join(j['murid'])}"),
        ft.Text(f"Status: {j['status']}"),
    ]

    if j["status"] == "Terjadwal":

      def aksi_mulai(e):
        sekarang = datetime.now()
        j.update({
            "check_in_dt": sekarang,
            "check_in": sekarang.strftime("%Y-%m-%d %H:%M:%S"),
            "pengajar_aktual": user["nama"],
            "status": "Sedang Mengajar",
        })
        JadwalModel.save(j)
        app_controller.refresh_current_view()

      card_content.append(
          ft.Button(content=ft.Text("Mulai Mengajar"), on_click=aksi_mulai)
      )

    elif j["status"] == "Sedang Mengajar":

      def aksi_selesai(e):
        sekarang = datetime.now()
        j["check_out_dt"] = sekarang
        j["check_out"] = sekarang.strftime("%Y-%m-%d %H:%M:%S")
        j["durasi_menit"] = JadwalModel.hitung_durasi_aktual(
            j, j["check_in_dt"], sekarang
        )
        j["status"] = "Selesai"
        JadwalModel.save(j)
        app_controller.refresh_current_view()

      card_content.append(ft.Text(f"Mulai: {j['check_in']}"))
      card_content.append(
          ft.Button(content=ft.Text("Selesai Mengajar"), on_click=aksi_selesai)
      )

    return ft.Card(
        content=ft.Container(content=ft.Column(card_content), padding=15)
    )

  @staticmethod
  def admin_dashboard_view(app_controller):
    jadwal_list = JadwalModel.get_all()
    total_menit = sum(j["durasi_menit"] for j in jadwal_list)

    controls = [
        ft.Text("Dashboard Admin", size=28, weight=ft.FontWeight.BOLD),
        ft.Text(
            "Total Durasi Mengajar Realisasi:"
            f" {JadwalModel.format_durasi(total_menit)}"
        ),
        ft.Divider(),
        ft.Text(
            "📋 Daftar Presensi & Jadwal Aktif",
            size=20,
            weight=ft.FontWeight.BOLD,
        ),
    ]

    for j in jadwal_list:

      def edit_koreksi_click(e, j_id=j["id"]):
        app_controller.selected_jadwal_id = j_id
        app_controller.navigate("koreksi_presensi")

      card_items = [
          ft.Row([
              ft.Text(
                  f"Tgl: {j['tanggal']} | {j['jam_mulai']} - {j['jam_selesai']}",
                  weight=ft.FontWeight.BOLD,
                  expand=True,
              ),
              ft.Button(
                  content=ft.Text("Edit / Koreksi"),
                  on_click=edit_koreksi_click,
              ),
          ]),
          ft.Text(
              f"Guru Asli: {j['guru']} | Pengajar Aktual:"
              f" {j['pengajar_aktual'] or '-'}"
          ),
          ft.Text(
              f"Status: {j['status']} | Durasi:"
              f" {JadwalModel.format_durasi(j['durasi_menit'])}"
          ),
      ]
      if j["alasan_koreksi"]:
        card_items.append(
            ft.Text(
                f"Catatan Koreksi: {j['alasan_koreksi']}",
                color=ft.Colors.AMBER_800,
            )
        )

      controls.append(
          ft.Card(
              content=ft.Container(
                  content=ft.Column(card_items), padding=12
              )
          )
      )

    controls.extend([
        ft.Divider(),
        ft.Button(
            content=ft.Text("💰 Rekap & Payroll Honor Guru"),
            on_click=lambda e: app_controller.navigate("payroll"),
        ),
        ft.Button(
            content=ft.Text("👤 Kelola Akun & Password Guru"),
            on_click=lambda e: app_controller.navigate("manage_guru"),
        ),
        ft.Button(
            content=ft.Text("📅 Kelola Jadwal Les"),
            on_click=lambda e: app_controller.navigate("manage_jadwal"),
        ),
        ft.Button(
            content=ft.Text("Logout"),
            on_click=lambda e: app_controller.logout(),
        ),
    ])
    return controls

  @staticmethod
  def koreksi_presensi_view(app_controller, jadwal_id):
    j = JadwalModel.get_by_id(jadwal_id)
    guru_all = [g["nama"] for g in UserModel.get_all_guru()]

    if not j:
      return [
          ft.Text("Jadwal tidak ditemukan."),
          ft.Button(
              content=ft.Text("Kembali"),
              on_click=lambda e: app_controller.navigate("admin_dashboard"),
          ),
      ]

    tgl_tf = ft.TextField(
        label="Tanggal (YYYY-MM-DD)", value=j["tanggal"], width=200
    )
    status_dd = ft.Dropdown(
        label="Status Presensi",
        value=j["status"],
        options=[
            ft.dropdown.Option("Terjadwal"),
            ft.dropdown.Option("Sedang Mengajar"),
            ft.dropdown.Option("Selesai"),
            ft.dropdown.Option("Tidak Hadir"),
        ],
        width=200,
    )

    check_in_tf = ft.TextField(
        label="Check-in (YYYY-MM-DD HH:MM:SS)",
        value=j["check_in"] or "",
        width=250,
    )
    check_out_tf = ft.TextField(
        label="Check-out (YYYY-MM-DD HH:MM:SS)",
        value=j["check_out"] or "",
        width=250,
    )
    durasi_tf = ft.TextField(
        label="Durasi (Menit)", value=str(j["durasi_menit"]), width=150
    )

    pengajar_dd = ft.Dropdown(
        label="Pengajar Aktual",
        value=j["pengajar_aktual"] or j["guru"],
        options=[ft.dropdown.Option(g) for g in guru_all],
        width=200,
    )
    alasan_tf = ft.TextField(
        label="Alasan / Catatan Koreksi Manual",
        value=j["alasan_koreksi"] or "",
        multiline=True,
    )

    def simpan_koreksi_click(e):
      try:
        durasi = int(durasi_tf.value.strip())
      except ValueError:
        app_controller.show_message("Durasi harus angka menit.")
        return

      JadwalModel.koreksi_presensi_manual(
          jadwal_id=j["id"],
          tanggal=tgl_tf.value.strip(),
          status=status_dd.value,
          check_in=check_in_tf.value.strip() or None,
          check_out=check_out_tf.value.strip() or None,
          durasi_menit=durasi,
          pengajar_aktual=pengajar_dd.value,
          alasan_koreksi=alasan_tf.value.strip(),
      )
      app_controller.show_message("Presensi berhasil dikoreksi secara manual.")
      app_controller.navigate("admin_dashboard")

    return [
        ft.Text(
            f"Koreksi Presensi Manual (Jadwal #{j['id']})",
            size=24,
            weight=ft.FontWeight.BOLD,
        ),
        ft.Row([tgl_tf, status_dd, pengajar_dd]),
        ft.Row([check_in_tf, check_out_tf, durasi_tf]),
        alasan_tf,
        ft.Button(
            content=ft.Text("Simpan Koreksi"), on_click=simpan_koreksi_click
        ),
        ft.Button(
            content=ft.Text("Batal / Kembali"),
            on_click=lambda e: app_controller.navigate("admin_dashboard"),
        ),
    ]

  @staticmethod
  def payroll_view(app_controller):
    guru_list = UserModel.get_all_guru()
    jadwal_list = JadwalModel.get_all()

    controls = [
        ft.Text("💰 Rekap & Payroll Honor Guru", size=24, weight=ft.FontWeight.BOLD),
        ft.Text("Kalkulasi Otomatis: (Total Menit / 60) × Tarif per Jam"),
        ft.Divider(),
    ]

    for g in guru_list:
      nama_guru = g["nama"]
      tarif = g["tarif_per_jam"]

      jadwal_guru = [
          j
          for j in jadwal_list
          if j["pengajar_aktual"] == nama_guru and j["status"] == "Selesai"
      ]
      total_menit = sum(j["durasi_menit"] for j in jadwal_guru)
      total_jam = total_menit / 60.0
      total_honor = round(total_jam * tarif)

      items_guru = [
          ft.Text(
              f"Guru: {nama_guru} | Tarif: Rp {tarif:,}/jam",
              size=18,
              weight=ft.FontWeight.BOLD,
          ),
          ft.Text(
              f"Total Durasi Mengajar: {JadwalModel.format_durasi(total_menit)}"
              f" ({total_jam:.2f} jam)"
          ),
          ft.Text(
              f"Total Estimasi Honor: Rp {total_honor:,}",
              size=16,
              color=ft.Colors.GREEN_700,
              weight=ft.FontWeight.BOLD,
          ),
      ]

      for j in jadwal_guru:

        def toggle_honor(e, j_id=j["id"], status_curr=j["honor_disetujui"]):
          JadwalModel.set_honor_disetujui(
              j_id, 0 if status_curr == 1 else 1
          )
          app_controller.refresh_current_view()

        is_paid = j["honor_disetujui"] == 1
        items_guru.append(
            ft.Row([
                ft.Text(
                    f"• {j['tanggal']} ({j['jam_mulai']}-{j['jam_selesai']}) -"
                    f" {JadwalModel.format_durasi(j['durasi_menit'])}",
                    expand=True,
                ),
                ft.Button(
                    content=ft.Text(
                        "Sudah Dibayar" if is_paid else "Belum Dibayar"
                    ),
                    on_click=toggle_honor,
                ),
            ])
        )

      controls.append(
          ft.Card(
              content=ft.Container(
                  content=ft.Column(items_guru), padding=12
              )
          )
      )

    controls.append(
        ft.Button(
            content=ft.Text("Kembali ke Dashboard"),
            on_click=lambda e: app_controller.navigate("admin_dashboard"),
        )
    )
    return controls

  @staticmethod
  def manage_guru_view(app_controller):
    daftar_guru = UserModel.get_all_guru()

    username_tf = ft.TextField(label="Username", width=150)
    password_tf = ft.TextField(label="Password", width=150)
    nama_tf = ft.TextField(label="Nama Lengkap", width=180)
    tarif_tf = ft.TextField(label="Tarif/Jam (Rp)", width=130, value="35000")

    def simpan_guru_click(e):
      if (
          not username_tf.value.strip()
          or not password_tf.value.strip()
          or not nama_tf.value.strip()
      ):
        app_controller.show_message("Semua field wajib diisi.")
        return
      try:
        tarif = int(tarif_tf.value.strip())
      except ValueError:
        app_controller.show_message("Tarif harus angka.")
        return

      UserModel.add_or_update_guru(
          username_tf.value, password_tf.value, nama_tf.value, tarif
      )
      app_controller.show_message("Akun & password guru disimpan.")
      app_controller.refresh_current_view()

    controls = [
        ft.Text(
            "Kelola Akun & Password Guru", size=24, weight=ft.FontWeight.BOLD
        ),
        ft.Column([
            ft.Row([username_tf, password_tf, nama_tf, tarif_tf]),
            ft.Button(
                content=ft.Text("Tambah / Reset Password Guru"),
                on_click=simpan_guru_click,
            ),
        ]),
        ft.Divider(),
    ]

    for g in daftar_guru:

      def hapus_click(e, u=g["username"], n=g["nama"]):
        UserModel.delete_guru(u, n)
        app_controller.refresh_current_view()

      controls.append(
          ft.Card(
              content=ft.Container(
                  content=ft.Row([
                      ft.Column(
                          [
                              ft.Text(
                                  f"Nama: {g['nama']} (Username:"
                                  f" {g['username']})",
                                  weight=ft.FontWeight.BOLD,
                              ),
                              ft.Text(
                                  f"Password: {g['password']} | Tarif/Jam: Rp"
                                  f" {g['tarif_per_jam']:,}"
                              ),
                          ],
                          expand=True,
                      ),
                      ft.Button(
                          content=ft.Text("Hapus"), on_click=hapus_click
                      ),
                  ]),
                  padding=10,
              )
          )
      )

    controls.append(
        ft.Button(
            content=ft.Text("Kembali ke Dashboard"),
            on_click=lambda e: app_controller.navigate("admin_dashboard"),
        )
    )
    return controls

  @staticmethod
  def manage_jadwal_view(app_controller):
    jadwal_list = JadwalModel.get_all()
    guru_list = [g["nama"] for g in UserModel.get_all_guru()]

    tgl_tf = ft.TextField(
        label="Tanggal (YYYY-MM-DD)", width=150, value=date.today().isoformat()
    )
    jam_mulai_tf = ft.TextField(
        label="Mulai (HH:MM)", width=110, value="15:00"
    )
    jam_selesai_tf = ft.TextField(
        label="Selesai (HH:MM)", width=110, value="17:00"
    )
    guru_dd = ft.Dropdown(
        label="Guru",
        options=[ft.dropdown.Option(g) for g in guru_list],
        width=160,
    )
    murid_tf = ft.TextField(label="Nama Murid (koma)", width=250)

    def simpan_jadwal_click(e):
      if not guru_dd.value or not murid_tf.value.strip():
        app_controller.show_message("Pilih guru dan nama murid.")
        return

      murid_arr = [m.strip() for m in murid_tf.value.split(",") if m.strip()]
      JadwalModel.add_jadwal(
          tgl_tf.value,
          jam_mulai_tf.value,
          jam_selesai_tf.value,
          guru_dd.value,
          murid_arr,
      )
      app_controller.show_message("Jadwal ditambahkan.")
      app_controller.refresh_current_view()

    controls = [
        ft.Text("Kelola Jadwal Les", size=24, weight=ft.FontWeight.BOLD),
        ft.Column([
            ft.Row([tgl_tf, jam_mulai_tf, jam_selesai_tf, guru_dd]),
            murid_tf,
            ft.Button(
                content=ft.Text("Buat Jadwal Baru"),
                on_click=simpan_jadwal_click,
            ),
        ]),
        ft.Divider(),
    ]

    for j in jadwal_list:

      def hapus_j_click(e, j_id=j["id"]):
        JadwalModel.delete_jadwal(j_id)
        app_controller.refresh_current_view()

      controls.append(
          ft.Card(
              content=ft.Container(
                  content=ft.Row([
                      ft.Column(
                          [
                              ft.Text(
                                  f"Tgl: {j['tanggal']} ({j['jam_mulai']} -"
                                  f" {j['jam_selesai']})",
                                  weight=ft.FontWeight.BOLD,
                              ),
                              ft.Text(
                                  f"Guru: {j['guru']} | Murid:"
                                  f" {', '.join(j['murid'])}"
                              ),
                              ft.Text(f"Status: {j['status']}"),
                          ],
                          expand=True,
                      ),
                      ft.Button(
                          content=ft.Text("Hapus"), on_click=hapus_j_click
                      ),
                  ]),
                  padding=10,
              )
          )
      )

    controls.append(
        ft.Button(
            content=ft.Text("Kembali ke Dashboard"),
            on_click=lambda e: app_controller.navigate("admin_dashboard"),
        )
    )
    return controls

  @staticmethod
  def absence_form_view(app_controller, user):
    jadwal_list = JadwalModel.get_all()
    today_str = date.today().isoformat()
    jadwal_user = [
        j
        for j in jadwal_list
        if j["guru"] == user["nama"]
        and not j["pengganti"]
        and j["status"] == "Terjadwal"
        and j["tanggal"] == today_str
    ]

    selected_jadwal = {"val": None}
    alasan_tf = ft.TextField(label="Alasan tidak hadir", multiline=True)
    lbl_pilihan = ft.Text("Belum memilih jadwal.")

    def submit_absen(e):
      j = selected_jadwal["val"]
      if not j or not alasan_tf.value.strip():
        app_controller.show_message("Pilih jadwal dan isi alasan.")
        return

      j["status"] = "Menunggu Pengganti"
      j["keterangan"] = alasan_tf.value.strip()

      JadwalModel.save(j)
      JadwalModel.save_ketidakhadiran({
          "jadwal_id": j["id"],
          "guru": user["nama"],
          "alasan": j["keterangan"],
          "waktu": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          "status": "Menunggu Pengganti",
      })
      app_controller.navigate("teacher_dashboard")

    btn_list = []
    for j in jadwal_user:

      def _select(e, item=j):
        selected_jadwal["val"] = item
        lbl_pilihan.value = (
            f"Terpilih: {item['jam_mulai']} - {item['jam_selesai']}"
        )
        app_controller.page.update()

      btn_list.append(
          ft.Button(
              content=ft.Text(f"{j['jam_mulai']} - {j['jam_selesai']}"),
              on_click=_select,
          )
      )

    return [
        ft.Text("Laporkan Ketidakhadiran", size=24, weight=ft.FontWeight.BOLD),
        *btn_list,
        lbl_pilihan,
        alasan_tf,
        ft.Button(content=ft.Text("Kirim Laporan"), on_click=submit_absen),
        ft.Button(
            content=ft.Text("Kembali"),
            on_click=lambda e: app_controller.navigate("teacher_dashboard"),
        ),
    ]