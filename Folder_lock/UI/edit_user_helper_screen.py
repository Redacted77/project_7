from __future__ import annotations
from typing import TYPE_CHECKING
from textual.screen import Screen
from textual.widgets import Static
from textual.containers import Center, Vertical, Horizontal
from textual.widgets import Footer, Header, Input, Button
from textual import work
from ..database_manager import UserInfo, Access
from . import functions_screen
if TYPE_CHECKING:
    from main import FolderLockApp

class Content(Vertical):
    def compose(self):
        yield Input(placeholder="enter new name", id="new_name")
        yield Input(placeholder="enter new pin", password=True, id="new_pin")
        with Horizontal(id="save_buttons"):
            yield Button("save name", id="commit_name")
            yield Button("save pin", id="save_pin")
        with Horizontal(id="access_buttons"):
            yield Button("Give Full access", id="full_access")
            yield Button("limit access", id="limit_access")
        yield Button("commit changes", id="commit")
    def on_mount(self):
        self.styles.width = 47
        self.styles.height = "auto"
        self.styles.align = ("center", "middle")
        
        self.query_one("#new_name").styles.width = "100%"
        self.query_one("#new_pin").styles.width = "100%"
        self.query_one("#commit_name").styles.width = 30
        self.query_one("#save_pin").styles.width = 30
        self.query_one("#commit").styles.width = 30
        
        self.query_one("#new_pin").styles.margin = (1, 0, 2, 0)
        self.query_one("#limit_access").styles.margin = (0, 0, 0, 2)
        self.query_one("#save_pin").styles.margin = (0, 0, 0, 2)
        for btn in self.query("#access_buttons Button"):
            btn.styles.width = 20
        for btn in self.query("#save_buttons Button"):
            btn.styles.width = 20

class EditUserInfo(Screen):
    BINDINGS = [('q', "quit", "Quit"), ('b', "go_to_previous_screen", "Go Back"), ('s', "save", "Save changes")]
    def __init__(self, user_info: UserInfo, target_user_id):
        super().__init__()
        self.app: FolderLockApp
        self.user_info = user_info
        self.target_user_id = target_user_id
        self.new_access = None
        self.new_name = None
        self.new_pin = None
        self.flag = False
    
    def compose(self):
        yield Header()
        label = Static(f"ID: {self.user_info.id} | Name: {self.user_info.name} | Access level: {self.user_info.access}")
        label.styles.text_align = "center"
        yield label
        yield Static("", id="status_label")
        with Center(id="main_center"):
            yield Content()
        yield Footer()
    def on_mount(self, event):
        center = self.query_one("#main_center", Center)
        center.styles.height = "1fr"
    
    def on_button_pressed(self, event: Button.Pressed):
        button_id = event.button.id
        if button_id == "full_access":
            self.new_access = Access.level_full.value
            self.message("access updated and ready to commit")
        elif button_id == "limit_access":
            self.new_access = Access.level_limited.value
            self.message("access updated and ready to commit")
        elif button_id == "commit_name":
            name = self.query_one("#new_name", Input).value
            self.message("name updated and ready to commit")
            self.new_name = name
        elif button_id == "save_pin":
            pin = self.query_one("#new_pin", Input).value
            self.new_pin = pin
            self.message("pin updated and ready to commit")
        elif button_id == "commit":
            if not self.flag:
                self.flag = True
                self.commit_changes_worker()
    @work(exclusive=True, thread=True)
    def commit_changes_worker(self):
        try:
            self.app.db_manger.edit_user_info(name=self.new_name, access=self.new_access, pin=self.new_pin, user_id=self.target_user_id)
            self.app.call_from_thread(self.commit_done)
        except Exception as e:
            pass
    def commit_done(self):
        self.message("commit completed successfully")
        self.flag = False
        self.app.log_manger.log_admin_action(status=True,event="Edited user info",user=self.user_info.id,target=self.target_user_id)
    
    def commit_error(self, error):
        self.message(error)
        self.flag = False
        self.app.log_manger.log_admin_action(status=False,event="Edited user info",user=self.user_info.id,target=self.target_user_id
                                             ,error=error)

    def message(self, mess):
        self.query_one("#status_label", Static).update(mess)
    def action_go_to_previous_screen(self):
        self.app.push_screen(functions_screen.FunctionsScreen(self.user_info.id))
    def action_save(self):
        try:
            self.app.security.save(fn_key=self.app.fn_key, db_conn=self.app.db_conn)
            self.message("Data saved")
        except Exception as e:
            self.message(f"Error: {e}")
    def action_quit(self):
        self.app.db_manger.close()
        self.app.exit()

