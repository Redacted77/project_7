from __future__ import annotations
from typing import TYPE_CHECKING
from textual.screen import Screen
from textual.widgets import Static
from textual.widgets import Footer, Header, DataTable
from textual import work
from database_manager import UserInfo
if TYPE_CHECKING:
    from main import FolderLockApp

class ListUsersScreen(Screen):
    BINDINGS = [('q', "quit", "Quit"), ('b', "go_to_previous_screen", "Go Back"), ('s', "save", "Save changes")]
    def __init__(self, user_info: UserInfo):
        super().__init__()
        self.app: FolderLockApp
        self.user_info = user_info
    
    def compose(self):
        yield Header()
        label = Static(f"ID: {self.user_info.id} | Name: {self.user_info.name} | Access level: {self.user_info.access}")
        label.styles.text_align = "center"
        yield label
        yield Static("", id="status_label")
        yield DataTable(id="user_table")
        yield Footer()
    
    def on_mount(self):
        table = self.query_one(DataTable)
        table.add_column("ID", width=5)
        table.add_column("Name", width=30)
        table.add_column("Access")
        self.message("Fetching users info...")
        self.fill_table()
    
    @work(exclusive=True, thread=True)
    def fill_table(self):
        try:
            users = self.app.db_manger.list_users()
            self.app.call_from_thread(self.data_found, users)
        except Exception as e:
            self.app.call_from_thread(self.message, f"{e}")
    
    def data_found(self, users):
        table = self.query_one(DataTable)
        user: UserInfo
        if not users:
            self.message("No users found")
            return
        for user in users:
            table.add_row(f"{user.id}",f"{user.name}",f"{user.access}")
        self.message("Done")
    
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