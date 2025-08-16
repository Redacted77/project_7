from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Grid
from textual.containers import Center, Horizontal, Vertical
from textual.widgets import Button, Label

class _YesNo(Horizontal):
    def compose(self):
        yield Button("Yes", variant="primary", id="yes", classes="spaced-btn")
        yield Button("No", variant="error", id="no", classes="spaced-btn")
    def on_mount(self):
        for btn in self.query(".spaced-btn"):
            btn.styles.margin = (0, 2)
        self.styles.width = 'auto'
        self.styles.align = ("center", "middle")

class ConfirmPopUp(Screen[bool]):
    def __init__(self, question: str):
        super().__init__()
        self.question = question
    
    def compose(self):
        with Center():
            with Vertical(id="question_box"):
                yield Label(self.question, id="question")
                yield Label("Are you sure?", id="yesorno")
                yield _YesNo()
    def on_mount(self):
        question = self.query_one("#question_box")
        question.styles.align = ("center", "middle")
    def on_button_pressed(self, event: Button.Pressed):
        button=event.button.id
        if button == "yes":
            self.dismiss(True)
        elif button == "no":
            self.dismiss(False)
    