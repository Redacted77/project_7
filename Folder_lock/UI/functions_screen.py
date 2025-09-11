from __future__ import annotations
from typing import TYPE_CHECKING
from textual.screen import Screen
from textual.widgets import Button, Static
from textual.containers import Center, Horizontal
from textual.widgets import Footer, Header
from ..database_manager import UserInfo, Access
from . import encrypt_screen, decrypt_screen, admin_screen
from .. import locking_system as LS
if TYPE_CHECKING:
    from main import FolderLockApp

class _content(Horizontal):
    def compose(self):
        yield Button("Decrypt", id="decrypt", classes="spaced-btn")
        yield Button("Encrypt", id="encrypt", classes="spaced-btn")
    def on_mount(self):
        for btn in self.query(".spaced-btn"):
            btn.styles.margin = (0, 2)
        self.styles.width = 'auto'
        self.styles.align = ("center", "middle")
        
class FunctionsScreen(Screen):
    BINDINGS = [('q', "quit", "Quit"), ('a', "admin_menu", "Admin Menu"), ('s', "save", "Save changes")]
    def __init__(self, user_id: int):
        super().__init__()
        self.app: FolderLockApp
        self.user_id = user_id
        self.app.lock_system = LS.LockSystem(self.user_id,self.app.log_manger,self.app.db_manger)
        self.info: UserInfo
        self.user_info = self.app.db_manger.return_login_info(self.user_id)
    
    def compose(self):
        yield Header()
        label = Static(f"ID: {self.user_info.id} | Name: {self.user_info.name} | Access level: {self.user_info.access}")
        label.styles.text_align = "center"
        yield label
        yield Static("", id="status_label") 
        with Center(id="main_center"):
            yield _content()
        yield Footer()
    
    def on_mount(self, event):
        center = self.query_one("#main_center", Center)
        center.styles.height = "1fr"

    def on_button_pressed(self, event: Button.Pressed):
        button_id = event.button.id
        if button_id == "decrypt":
            self.app.push_screen(decrypt_screen.DecryptScreen(self.user_info))
        elif button_id == "encrypt":
            self.app.push_screen(encrypt_screen.EncryptScreen(self.user_info))
    
    def message(self, mess):
        self.query_one("#status_label", Static).update(mess)

    def action_admin_menu(self):
        if self.user_info.access == Access.level_full.value:
            self.message("Access granted.")
            self.app.push_screen(admin_screen.AdminMenu(self.user_info))
        else:
            self.message("Error: Admin menu is only available to users with 'Full access'.")
    def action_save(self):
        try:
            self.app.security.save(fn_key=self.app.fn_key, db_conn=self.app.db_conn)
            self.message("Data saved")
        except Exception as e:
            self.message(f"Error: {e}")
    def action_quit(self):
        self.app.db_manger.close()
        self.app.exit()