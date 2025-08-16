from __future__ import annotations
from typing import TYPE_CHECKING
from textual.screen import Screen
from textual.widgets import Static
from textual.widgets import Footer, Header, DataTable
from textual import work
from database_manager import UserInfo, FolderInfo
from new_locking_system import Mode
from UI import pop_up
if TYPE_CHECKING:
    from main import FolderLockApp

class DecryptScreen(Screen):
    BINDINGS = [('q', "quit", "Quit"), ('b', "go_to_previous_screen", "Go Back"), ('a', "admin_menu", "Admin Menu")]
    def __init__(self, user_info: UserInfo):
        super().__init__()
        self.app: FolderLockApp
        self.user_info = user_info
        self.is_decrypting = False
    
    def compose(self):
        yield Header()
        label = Static(f"ID: {self.user_info.id} | Name: {self.user_info.name} | Access level: {self.user_info.access}")
        label.styles.text_align = "center"
        yield label
        yield Static("", id="status_label")
        yield DataTable(id="folder_table")
        yield Footer()
    def on_mount(self):
        table = self.query_one(DataTable)
        table.add_column("ID", width=5)
        table.add_column("Folder Name")
        table.add_column("Folder Path")
        self.message("Fetching encrypted folders...")
        self.fill_table()
        table.cursor_type = "row"
        table.show_cursor = True
        table.focus()
        table.mouse_enabled = True
    
    @work(exclusive=True, thread=True)
    def fill_table(self):
        try:
            folders = self.app.db_manger.list_encrypted_folders()
            self.app.call_from_thread(self.data_found, folders)
        except Exception as e:
            self.app.log_manger.generic_error(e)
            self.app.call_from_thread(self.message, f"Error: {e}")

    def data_found(self, folders_list):
        table = self.query_one(DataTable)
        folder: FolderInfo
        if not folders_list:
            self.message("No encrypted folders found.")
            return
        for folder in folders_list:
            table.add_row(f"{folder.id}", f"{folder.name}", f"{folder.path}", key=str(folder.id))
        self.message("Select a folder to decrypt")

    def on_data_table_row_selected(self, event: DataTable.RowSelected):
        if self.is_decrypting:
            self.message("Decryption is already in progress... Please wait...")
            return
        
        self.is_decrypting = True
        fodler_id = event.row_key
        row_data = event.control.get_row(fodler_id)
        self.message(f"Decrypting folder: {fodler_id}... Please wait...")
        self.decrypt(row_data[2], fodler_id)
    
    @work(exclusive=True, thread=True)
    def decrypt(self, folder_path, row_key):
        try:
            conformed_path = self.app.lock_system.confirm_target_folder(folder_path, Mode.DEC)
            if conformed_path and self.app.call_from_thread(self.confrim):
                self.app.lock_system.enc_dec_dispatcher(folder_path, Mode.DEC)
                self.app.call_from_thread(self.on_decryption, row_key)
            else:
                self.message("Folder decryption aborted")
                self.is_decrypting = False
        except Exception as e:
            self.app.call_from_thread(self.on_error, e)

    def confrim(self):
        ask = self.app.push_screen_wait(pop_up.ConfirmPopUp("Warning: This folder is about to be decrypted."))
        return ask

    def on_decryption(self, row_key):
        self.message("Decryption completed successfully")
        table = self.query_one(DataTable)
        table.remove_row(row_key)
        self.is_decrypting = False

    def on_error(self, error):
        self.app.log_manger.generic_error(error)
        self.message(f"Error: {error}")
        self.is_decrypting = False

    def message(self, mess):
        self.query_one("#status_label", Static).update(mess)
    def action_go_to_previous_screen(self):
        self.app.pop_screen()
    def action_quit(self):
        self.app.exit()