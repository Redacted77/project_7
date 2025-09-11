from __future__ import annotations
from typing import TYPE_CHECKING
from textual.screen import Screen
from textual.widgets import Button, Static
from textual.containers import Center, Vertical
from textual.widgets import Footer, Header, Input, Button
from security_system import Checks, database_dependency
from textual import work
import security_system as SS
if TYPE_CHECKING:
    from main import FolderLockApp

class Struc(Vertical):
    def compose(self):
        yield Input(placeholder="Enter database password", password=True, id="password")
        yield Button("Unlock", id="unlock")
    def on_mount(self):
        self.query_one("#password").styles.width = 40
        self.query_one("#unlock").styles.margin = (0,0,0,11)
        self.styles.align = ("center", "middle")
class StrucNonEnc(Vertical):
    def compose(self):
        yield Input(placeholder="Enter a password for the database", password=True, id="first_password")
        yield Button("lock", id="lock")
    def on_mount(self):
        self.query_one("#first_password").styles.width = 40
        self.query_one("#lock").styles.margin = (0,0,0,11)
        self.styles.align = ("center", "middle")

class PasswordScreen(Screen[bool]):
    BINDINGS = [('q', "quit", "Quit")]
    def __init__(self):
        super().__init__()
        self.app: FolderLockApp
        self.encrypted = self.app.security.check_if_encrypted()
        self.checks: Checks
        self.checks = self.app.security.run_check()
    def compose(self):
        yield Header()
        yield Static("", id="status_label") 
        with Center():
            if self.encrypted:
                yield Struc()
            else:
                yield StrucNonEnc()
        yield Footer()
    
    def on_button_pressed(self, event: Button.Pressed):
        button_id = event.button.id
        if button_id == "unlock":
            pas = self.query_one("#password", Input).value
            try:
                if self.checks.encrypted_db_exists and self.checks.salt_exist:
                    self.unlock_worker(pas)
                else:
                    self.dismiss(False)
            except Exception as e:
                self.message("worng password")
        if button_id == "lock":
            pas = self.query_one("#first_password", Input).value
            try:
                if self.checks.public_db_exists:
                    self.lock_worker(pas)
                else:
                    self.dismiss(False)
            except Exception as e:
                self.message(f"Error: {e}")
    
    @work(exclusive=True,thread=True)
    def unlock_worker(self, pas):
        self.app.call_from_thread(self.message, "Verifying password...")
        check = self.app.security.decrypt_db_v2(password=pas)
        self.app.call_from_thread(self.decrypt_return, check)
    def decrypt_return(self, check: database_dependency):
        if check:
            self.app.db_conn = check.sql_conn
            self.app.fn_key = check.fn_key
            self.message("Unlocked database successfully")
            self.dismiss(True)
        self.message("Wrong password")
    
    @work(exclusive=True,thread=True)
    def lock_worker(self, pas):
        self.app.call_from_thread(self.message, "Locking database...")
        re = self.app.security.encrypt_db_v2(master_password=pas)
        self.app.call_from_thread(self.encrypt_return, re)
    def encrypt_return(self, re: database_dependency):
        if re:
            self.app.db_conn = re.sql_conn
            self.app.fn_key = re.fn_key
            self.message("Locking database was successful")
            self.dismiss(True)
    
    def message(self, mess):
        self.query_one("#status_label", Static).update(mess)
    def action_quit(self):
        self.app.exit()