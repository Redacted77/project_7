from __future__ import annotations
from typing import TYPE_CHECKING
from textual.screen import Screen
from textual.widgets import Button, Static
from textual.containers import Center, Vertical
from textual.widgets import Footer, Header, Input
from textual import work
from UI import functions_screen
from database_manager import Access, UserInfo
if TYPE_CHECKING:
    from main import FolderLockApp

class Content(Vertical):
    def compose(self):
        yield Button("Face Scan", id="face-scan")
        yield Input(placeholder="Enter name", id="name")
        yield Input(placeholder="enter pin", password=True, id="pin")
        yield Button("Add", id="add")
    
    def on_mount(self):
        for widget in self.children:
            self.styles.width = 30 

        self.styles.align = ("center", "middle")
        self.styles.gap = 2
        self.query_one("#face-scan").styles.width=30
        self.query_one("#name").styles.width=30
        self.query_one("#add").styles.width=30
        self.query_one("#add").styles.margin = (2, 0, 0, 0)

class AddUserScreen(Screen):
    BINDINGS = [('q', "quit", "Quit"), ('b', "go_to_previous_screen", "Go Back"), ('s', "save", "Save changes")]
    def __init__(self, condition, user_info: UserInfo = None):
        super().__init__()
        self.app: FolderLockApp
        self.condition = condition
        self.face_encoding = None
        self.scan_face_flag = False
        self.user_info = user_info
    def compose(self):
        yield Header()
        yield Static("", id="status_label")
        with Center():
            yield Content()
        yield Footer()
    def on_button_pressed(self, event: Button.Pressed):
        button_id = event.button.id
        if button_id == "face-scan":
            self.scan_face_flag = True
            self.face_scan()
        elif button_id == "add":
            if not self.face_encoding:
                self.message("Error: A face scan must be completed first.")
                return
            if self.scan_face_flag:
                self.message("Please wait for the face scan to complete.")
                return
            name = self.query_one("#name", Input).value
            pin = self.query_one("#pin", Input).value
            if not name or not pin:
                self.message("Error: Please enter both a name and a PIN.")
                return
            self.add_worker(name, pin, self.face_encoding, self.condition)
    
    @work(exclusive=True, thread=True)
    def face_scan(self):
        self.app.call_from_thread(self.message, "Scanning face, please wait...")
        try:
            face_encoding = self.app.facial_recognition_system.face_id_and_recog()
            self.app.call_from_thread(self.done_face_scan, face_encoding)
        except Exception as e:
            self.app.call_from_thread(self.error_face_scan, e)
    
    def done_face_scan(self, face_encoding):
        self.face_encoding = face_encoding
        self.message("face-scan was Completed")
        self.scan_face_flag = False
    def error_face_scan(self, error):
        self.message(f"error: {error}")
        self.scan_face_flag = False
    
    @work(exclusive=True, thread=True)
    def add_worker(self, name, pin, face_encoding, condition):
        if condition == "first_user":
            access = Access.level_full.value
        else:
            access = Access.level_limited.value
        
        try:
            added_user_id = self.app.db_manger.add_user_info(name=name,encoding=face_encoding,pin=pin,access=access)
            self.app.call_from_thread(self.added_user, added_user_id)
        except Exception as e:
            self.app.call_from_thread(self.added_user_error, e)
    def added_user(self, added_user_id):
        if self.condition == "subsequent":
            self.app.log_manger.log_admin_action(True, "Add User", self.user_info.id, added_user_id)
        self.message("Added user successfully")
        if self.condition == "first_user":
            self.app.push_screen(functions_screen.FunctionsScreen(added_user_id))
    def added_user_error(self, error):
        if self.condition == "subsequent":
            self.app.log_manger.log_admin_action(status=False, event="Add User", user=self.user_info.id, error=error)
        self.message(f"{error}")
    
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