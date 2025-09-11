from __future__ import annotations
from typing import TYPE_CHECKING
from textual.screen import Screen
from textual.widgets import Button, Static
from textual.containers import Center, Vertical
from textual.widgets import Footer, Header
from database_manager import UserInfo
from security_system import Condition
from UI import list_users_screen, add_user_screen, remove_user_screen, remove_enc_folder_screen, edit_user_screen
import new_locking_system as LS
if TYPE_CHECKING:
    from main import FolderLockApp

class MenuOptions(Vertical):
    def compose(self):
        yield Button("List Users", id="list_users")
        yield Button("Add User", id="add_user")
        yield Button("Edit User Info", id="edit_user")
        yield Button("Remove User", id="remove_user")
        yield Button("Remove Encrypted Folder", id="remove_folder")
    def on_mount(self):
        self.query_one("#list_users").styles.width = 30
        self.query_one("#add_user").styles.width = 30
        self.query_one("#edit_user").styles.width = 30
        self.query_one("#remove_user").styles.width = 30
        self.query_one("#remove_folder").styles.width = 30
        self.styles.align = ("center", "middle")
        

class AdminMenu(Screen):
    BINDINGS = [('q', "quit", "Quit"), ('b', "go_to_previous_screen", "Go Back"), ('s', "save", "Save changes")]
    def __init__(self, user_info: UserInfo):
        super().__init__()
        self.app: FolderLockApp
        self.user_info = user_info
    
    def compose(self):
        yield Header()
        label = Static(f"ID: {self.user_info.id} | Name: {self.user_info.name} | Access level: {self.user_info.access}")
        label.styles.text_align = "center"
        yield Static("", id="status_label") 
        yield label
        with Center(id="main_center"):
            yield MenuOptions()
        yield Footer()
    
    def on_mount(self):
        center = self.query_one("#main_center", Center)
        center.styles.height = "1fr"
    
    def on_button_pressed(self, event: Button.Pressed):
        button_id = event.button.id
        if button_id == "list_users":
            self.app.push_screen(list_users_screen.ListUsersScreen(self.user_info))
        elif button_id == "add_user":
            self.app.push_screen(add_user_screen.AddUserScreen(user_info=self.user_info, condition=Condition.normal.value))
        elif button_id == "edit_user":
            self.app.push_screen(edit_user_screen.EditUser(self.user_info))
        elif button_id == "remove_user":
            self.app.push_screen(remove_user_screen.RemoveUserScreen(self.user_info))
        elif button_id == "remove_folder":
            self.app.push_screen(remove_enc_folder_screen.RemoveFolderScreen(self.user_info))

    def message(self, mess):
        self.query_one("#status_label", Static).update(mess)
    def action_save(self):
        try:
            self.app.security.save(fn_key=self.app.fn_key, db_conn=self.app.db_conn)
            self.message("Data saved")
        except Exception as e:
            self.message(f"Error: {e}")
    def action_go_to_previous_screen(self):
        self.app.pop_screen()
    def action_quit(self):
        self.app.db_manger.close()
        self.app.exit()