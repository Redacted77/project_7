import logs_system as Log
import database_manager as Dbm
import new_face_recod as FC
import security_system as SS
from new_locking_system import LockSystem
from textual.app import App
from UI import login_screen

class FolderLockApp(App):
    def on_mount(self) -> None:
        self.log_manger = Log.Logging()
        self.db_manger = Dbm.DataBaseManager()
        self.security = SS.SercuritySystem(self.log_manger)
        self.facial_recognition_system = FC.facialRecognitionSystem(self.log_manger, self.db_manger)
        self.lock_system: LockSystem
        
        if self.db_manger.not_empty_database():
            self.push_screen(login_screen.LoginScreen())
        else:
            pass # should skip to a screen to insert user info and add an enrty in the faces table
    
if __name__ == "__main__":
    FolderLockApp().run()