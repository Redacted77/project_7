from Folder_lock import logs_system as Log
from Folder_lock import database_manager as Dbm
from Folder_lock import facial_recognition_system as FC
from Folder_lock import security_system as SS
from Folder_lock.locking_system import LockSystem
from textual.app import App
from textual import work
from Folder_lock.UI import login_screen, add_user_screen, db_password_screen
from Folder_lock.security_system import Condition, Checks

class FolderLockApp(App):
    def on_mount(self) -> None:
        self.db_conn = None
        self.fn_key = None
        self.log_manger = Log.Logging()
        self.security = SS.SercuritySystem(logging_manger=self.log_manger)
        self.start()

    def setup(self):
        self.db_manger = Dbm.DataBaseManager(conn=self.db_conn, log=self.log_manger)
        self.facial_recognition_system = FC.facialRecognitionSystem(self.log_manger, self.db_manger)
        self.lock_system: LockSystem
    
    @work(exclusive=True, thread=True)
    def start(self):
        check: Checks
        check = self.security.run_check()
        if check.public_db_exists:
            stat = self.call_from_thread(self.decrypt_status)
        else:
            self.db_manger2 = Dbm.DataBaseManager(log=self.log_manger)
            self.db_manger2.close()
            stat = self.call_from_thread(self.decrypt_status)
        if stat:
            self.call_from_thread(self.normal_progression)
        else:
            self.exit()
    
    def decrypt_status(self):
        stat = self.push_screen_wait(db_password_screen.PasswordScreen())
        return stat
    def normal_progression(self):
        self.setup()
        try:
            if self.db_manger.not_empty_database():
                self.push_screen(login_screen.LoginScreen())
            else:
                self.push_screen(add_user_screen.AddUserScreen(condition=Condition.First_time.value))
        except AttributeError:
            self.exit()

if __name__ == "__main__":
    FolderLockApp().run()