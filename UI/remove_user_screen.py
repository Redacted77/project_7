from __future__ import annotations
from typing import TYPE_CHECKING
from textual.screen import Screen
from textual.widgets import Static
from textual.widgets import Footer, Header, DataTable
from textual import work
from database_manager import UserInfo
from UI import pop_up
if TYPE_CHECKING:
    from main import FolderLockApp


class RemoveUserScreen(Screen):
    BINDINGS = [('q', "quit", "Quit"), ('b', "go_to_previous_screen", "Go Back"), ('s', "save", "Save changes")]
    def __init__(self, user_info: UserInfo):
        super().__init__()
        self.app: FolderLockApp
        self.user_info = user_info
        self.remove_user_flag = False
    
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
        table.add_column("ID", width=5, key="id")
        table.add_column("Name", width=30)
        table.add_column("Access")
        self.message("Fetching users info...")
        self.fill_table()
        table.cursor_type = "row"
        table.show_cursor = True
        table.focus()
        table.mouse_enabled = True
    
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
        self.message("Select a user to delete")
    
    def on_data_table_row_selected(self, event: DataTable.RowSelected):
        if self.remove_user_flag:
            self.message("already removing a folder... please wait...")
            return
        row_key = event.row_key
        user_id = event.control.get_cell(row_key=row_key, column_key="id")
        self.confirom_worker(user_id, row_key)
    
    @work(exclusive=True, thread=True)    
    def confirom_worker(self, user_id, row_key):
        ask = self.app.call_from_thread(self.confirm)
        if ask:
            self.remove_user(user_id=user_id, row_key=row_key)
        else:
            self.message("delete aborted")
    def confirm(self):
        ask = self.app.push_screen_wait(pop_up.ConfirmPopUp("Warning: Selected user will be DELETED."))
        return ask
    @work(exclusive=True, thread=True)
    def remove_user(self, user_id, row_key):
        try:
            self.app.db_manger.remove_user(user_id=user_id)
            self.app.call_from_thread(self.removed_user, user_id, row_key)
        except Exception as e:
            self.app.call_from_thread(self.remove_error, e)

    def removed_user(self, user_id, row_key):
        self.message(f"removed {user_id} successfully")
        self.remove_user_flag = False
        self.app.log_manger.log_admin_action(status=True,event="Remove user",user=self.user_info.id,target=user_id)
        table = self.query_one(DataTable)
        table.remove_row(row_key)
    def remove_error(self, error):
        self.message(error)
        self.remove_user_flag = False
        self.app.log_manger.log_admin_action(status=True,event="Remove user",user=self.user_info.id,error=error)

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