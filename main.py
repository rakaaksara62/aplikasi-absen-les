import os
import flet as ft
from database import init_db
from views import Views


class AppController:

  def __init__(self, page: ft.Page):
    self.page = page
    self.page.title = "Sistem Absensi Pusat Les"
    self.page.padding = 25
    self.current_user = None
    self.current_view = "login"
    self.selected_jadwal_id = None

  def show_message(self, msg):
    self.page.snack_bar = ft.SnackBar(content=ft.Text(msg))
    self.page.snack_bar.open = True
    self.page.update()

  def set_user(self, user):
    self.current_user = user
    if user["role"] == "guru":
      self.navigate("teacher_dashboard")
    else:
      self.navigate("admin_dashboard")

  def logout(self):
    self.current_user = None
    self.navigate("login")

  def navigate(self, view_name):
    self.current_view = view_name
    self.refresh_current_view()

  def refresh_current_view(self):
    self.page.controls.clear()

    controls = []
    if self.current_view == "login":
      controls = Views.login_view(self)
    elif self.current_view == "teacher_dashboard":
      controls = Views.teacher_dashboard_view(self, self.current_user)
    elif self.current_view == "absence_form":
      controls = Views.absence_form_view(self, self.current_user)
    elif self.current_view == "admin_dashboard":
      controls = Views.admin_dashboard_view(self)
    elif self.current_view == "koreksi_presensi":
      controls = Views.koreksi_presensi_view(self, self.selected_jadwal_id)
    elif self.current_view == "payroll":
      controls = Views.payroll_view(self)
    elif self.current_view == "manage_guru":
      controls = Views.manage_guru_view(self)
    elif self.current_view == "manage_jadwal":
      controls = Views.manage_jadwal_view(self)

    self.page.add(ft.ListView(controls=controls, expand=True, spacing=10))
    self.page.update()


def main(page: ft.Page):
  init_db()
  app = AppController(page)
  app.navigate("login")


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 8080))
  ft.run(main, port=port, view=ft.AppView.WEB_BROWSER)