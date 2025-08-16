from __future__ import annotations
from typing import TYPE_CHECKING
from textual.screen import Screen
from textual.widgets import Input, Button, Static
from textual.containers import Center, Vertical
from textual.widgets import Footer, Header
from textual import work
from UI import functions_screen
if TYPE_CHECKING:
    from main import FolderLockApp

class _login(Vertical):

    def compose(self):
        yield Button("Face Scan", id="face-scan")
        yield Input(placeholder="enter pin", password=True, id="pin")
        yield Button("Login", id="submit")
    def on_mount(self):
        for widget in self.children:
            self.styles.width = 30 

        self.styles.align = ("center", "middle")
        self.styles.gap = 2
        self.query_one("#face-scan").styles.width=30
        self.query_one("#submit").styles.width=30
        self.query_one("#submit").styles.margin = (2, 0, 0, 0) 
        
class LoginScreen(Screen):
    BINDINGS = [('q', "quit", "Quit")]
    def __init__(self):
        super().__init__()
        self.app: FolderLockApp
        self.is_scanning = False
        self.face_enc = None
    
    def compose(self):
        yield Header()
        yield Static("", id="status_label") 
        with Center():
            yield _login()
        yield Footer()
    
    def on_button_pressed(self, event: Button.Pressed):
        button_id = event.button.id
        if button_id == "face-scan":
            if not self.is_scanning:
                self.is_scanning = True
                self.face_scan_action()
        elif button_id == "submit":
            pin_value = self.query_one("#pin", Input).value
            self.login(pin_value)
    
    @work(exclusive=True, thread=True)
    def face_scan_action(self):
        self.app.call_from_thread(self.message, "Scanning face, please wait...")
        frs = self.app.facial_recognition_system
        
        try:
            face_enc = frs.face_id_and_recog()
            self.app.call_from_thread(self.scan_result, face_enc)
        except Exception as e:
            self.app.call_from_thread(self.scan_error, e)      
    
    def scan_result(self, encoding):
        self.face_enc = encoding
        self.message("face-scan was Completed")
        self.is_scanning = False
    
    def scan_error(self, error):
        self.app.log_manger.generic_error(error)
        self.message(f"face-scan error: {error}")
        self.is_scanning = False
    
    def login(self, entered_pin):
        frs = self.app.facial_recognition_system
        if self.is_scanning:
            self.message("face-scan was not done")
            return
        
        if self.face_enc and entered_pin:
            try:
                face_check_id =  frs.compar_faces_with_db(self.face_enc)
            except Exception as e:
                self.app.log_manger.generic_error(e)
                self.message(f"{e}")
                
            try:
                if self.app.db_manger.check_pin(id=face_check_id, pin=entered_pin) and face_check_id:
                    self.app.log_manger.announce_login(user=face_check_id)
                    self.message("login successful")
                    self.app.push_screen(functions_screen.FunctionsScreen(user_id=face_check_id))
                else:
                    self.message("Error: Wrong pin or face id")
            except Exception as e:
                self.app.log_manger.generic_error(e)
                self.message("Error try again")
        else:
            self.message("Error: Messing pin or face id")
    
    def message(self, mess):
        self.query_one("#status_label", Static).update(mess)
    
    def action_quit(self):
        self.app.exit()