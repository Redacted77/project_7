from __future__ import annotations
from typing import TYPE_CHECKING
from textual.screen import Screen
from textual.widgets import Input, Button, Static
from textual.containers import Center, Vertical
from textual.widgets import Footer, Header
from textual import work
from database_manager import UserInfo
from new_locking_system import Mode
from UI import pop_up

if TYPE_CHECKING:
    from main import FolderLockApp

class _content(Vertical):
    def compose(self):
        yield Input(placeholder="Enter folder path", id="path")
        yield Button("Pick a Folder", id="pick_folder")
    def on_mount(self):
        self.query_one("#path").styles.width = 75
        self.styles.align = ("center", "middle")

class EncryptScreen(Screen):
    BINDINGS = [('q', "quit", "Quit"), ('b', "go_to_previous_screen", "Go Back"), ('a', "admin_menu", "Admin Menu")]
    def __init__(self, user_info: UserInfo):
        super().__init__()
        self.app: FolderLockApp
        self.user_info = user_info
        self.is_encrypting = False
    
    def compose(self):
        yield Header()
        label = Static(f"ID: {self.user_info.id} | Name: {self.user_info.name} | Access level: {self.user_info.access}")
        label.styles.text_align = "center"
        yield label
        yield Static("", id="status_label")
        with Center():
            yield _content()
        yield Footer()
    
    def on_button_pressed(self, event: Button.Pressed):
        button_id = event.button.id
        if button_id == "pick_folder":
            if not self.is_encrypting:
                self.is_encrypting = True
                folder_path = self.query_one("#path", Input).value
                self.encrypt_worker(folder_path)
            else:
                self.message("Encryption is already in progress... please wait...")
    
    @work(exclusive=True, thread=True)
    def encrypt_worker(self, path):
        self.message("Checking folder.... please wait...")
        try:
            conformed_path = self.app.lock_system.confirm_target_folder(user_path=path, mode=Mode.ENC)
            if conformed_path and self.app.call_from_thread(self.confirm):
                self.message("Folder path is VALID. Encryption in progress... please wait...")
                self.app.lock_system.enc_dec_dispatcher(target_folder_path=conformed_path, mode=Mode.ENC)
                self.app.call_from_thread(self.encrypt_valid)
            else:
                self.message("Folder encryption aborted")
                self.is_encrypting = False
        except Exception as e:
            self.app.call_from_thread(self.encrypt_error, e)
            
    def confirm(self):
        ask = self.app.push_screen_wait(pop_up.ConfirmPopUp("Warning: This folder is about to be encrypted."))
        return ask
    def encrypt_valid(self):
        self.message("Encryption completed successfully")
        self.is_encrypting = False
    def encrypt_error(self, error):
        self.message(f"Error: {error}. try again.")
        self.app.log_manger.generic_error(error)
        self.is_encrypting = False

    def message(self, mess):
        self.query_one("#status_label", Static).update(mess)
    
    def action_go_to_previous_screen(self):
        self.app.pop_screen()
    def action_quit(self):
        self.app.exit()