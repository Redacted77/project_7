from __future__ import annotations
from typing import TYPE_CHECKING
from textual.screen import Screen
from textual.widgets import Static
from textual.widgets import Footer, Header, DataTable
from textual import work
from database_manager import FolderInfo, UserInfo
from UI import pop_up
if TYPE_CHECKING:
    from main import FolderLockApp

class RemoveFolderScreen(Screen):
    BINDINGS = [('q', "quit", "Quit"), ('b', "go_to_previous_screen", "Go Back"), ('s', "save", "Save changes")]
    def __init__(self, user_info: UserInfo):
        super().__init__()
        self.app: FolderLockApp
        self.user_info = user_info
        self.remove_folder_flag = False
    
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
        table.add_column("Folder Path", key="folder_path")
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
        self.message("Select a folder to remove")
    
    def on_data_table_row_selected(self, event: DataTable.RowSelected):
        if self.remove_folder_flag:
            self.message("already removing a folder... please wait...")
            return
        row_key = event.row_key
        folder_data = event.control.get_row(row_key)
        self.conform_worker(folder_data, row_key)
    
    @work(exclusive=True, thread=True)
    def conform_worker(self, folder_data, row_key):
        ask = self.app.call_from_thread(self.confirm)
        if ask:
            self.message(f"Removing folder: {folder_data[0]}... Please wait...")
            self.remove_folder(folder_data[2], folder_data[0], row_key)
        else:
            self.message("delete aborted")
    def confirm(self):
        ask = self.app.push_screen_wait(pop_up.ConfirmPopUp("Warning: Selected folder will be DELETED and CAN'T be decrypted."))
        return ask
    @work(exclusive=True, thread=True)
    def remove_folder(self, folder_path, folder_id, row_key):
        try:
            self.app.db_manger.remove_encrypted_folder(folder_path=folder_path)
            self.app.call_from_thread(self.removed_folder, folder_id, row_key)
        except Exception as e:
            self.app.call_from_thread(self.remove_error, e)
    
    def removed_folder(self, folder_id, row_key):
        self.message(f"Removed folder_id:{folder_id} successfully")
        self.app.log_manger.log_admin_action(status=False,event="Remove encrypted folder",user=self.user_info.id,target=folder_id)
        self.remove_folder_flag = False
        table = self.query_one(DataTable)
        table.remove_row(row_key)
    def remove_error(self, error):
        self.message(error)
        self.app.log_manger.log_admin_action(status=False,event="Remove encrypted folder",user=self.user_info.id,error=error)
        self.remove_folder_flag = False

    def message(self, mess):
        self.query_one("#status_label", Static).update(mess)
    def action_go_to_previous_screen(self):
        self.app.pop_screen()
    def action_save(self):
        try:
            self.app.security.save(fn_key=self.app.fn_key, db_conn=self.app.db_conn)
            self.message("Data saved")
        except Exception as e:
            self.message(f"Error: {e}")
    def action_quit(self):
        self.app.db_manger.close()
        self.app.exit()