import marshal
import hashlib
import os
import tempfile

from kivy.app import App
from kivy.uix.gridlayout import GridLayout  # Main layout to be used in the project
from kivy.uix.screenmanager import ScreenManager, Screen  # Allow to easily switch between screens

# Widgets
from kivy.uix.label import Label  # Label for either text showing or blank bar
from kivy.uix.button import Button  # Button for you guessed it button things.
from kivy.uix.textinput import TextInput  # Text input Widget


# Encryption
from NotesEncrpytion import encryption

# Time
import datetime as dt


class SavableNote:
    def __init__(self, name=None, key=None, text=None, date=None, password=None, author=None):
        self.name = name
        self.key = key
        self.author = author
        self.date = date
        if self.key is not None:
            self.Cipher = encryption.AESCipher(self.key)
            self.iv = self.Cipher.iv
            self.text = self.Cipher.encrypt(text)
            self.password = self.Cipher.encrypt(password)

    def toJSON(self):
        return {'name': self.name, 'key': self.key, 'author': self.author, 'date': self.date,
                'cipher': self.Cipher.toJSON(), 'iv': self.iv, 'text': self.text,
                'password': self.password}

    def fromJSON(self, json_data):
        self.Cipher = encryption.AESCipher()
        self.key = json_data['key']
        self.name = json_data['name']
        self.author = json_data['author']
        self.date = json_data['date']
        self.Cipher.fromJSON(json_data['cipher'])
        self.iv = json_data['iv']
        self.text = json_data['text']
        self.password = json_data['password']


class SavePage(GridLayout):
    def __init__(self, **kwargs):
        super(SavePage, self).__init__(**kwargs)
        self.cols = 2
        self.rows = 4
        self.Note = None

        self.add_widget(Label(text="Note Name"))
        self.Name = TextInput(multiline=False)
        self.add_widget(self.Name)

        self.add_widget(Label(text="Author"))
        self.Author = TextInput(multiline=False)
        self.add_widget(self.Author)

        self.add_widget(Label(text="Password\n[b]NO RECOVERY IF LOST[/b]", markup=True))
        self.Password = TextInput(multiline=False, password=True)
        self.add_widget(self.Password)

        self.Cancel = Button(text="Cancel", color=(1, 1, 1, 1), size_hint=(1, .1))
        self.Cancel.bind(on_release=self.CancelBind)
        self.add_widget(self.Cancel)
        self.Save = Button(text="Save", color=(1, 1, 1, 1), size_hint=(1, .1))
        self.add_widget(self.Save)

    def setNote(self, note):
        self.Note = note

    @staticmethod
    def CancelBind(*args):
        RunApp.ScreenManager.current = "NoteEntry"

    def SaveBind(self, *args):
        if self.Note is not None:
            path = f"./notes/{self.Name.text}.note"
            if os.path.exists(path):
                i = 1
                path = f"./notes/{self.Name.text}({i}).note"
                while os.path.exists(path):
                    i += 1
                    path = f"./notes/{self.Name.text}({i}).note"
            key = hashlib.md5(self.Password.text.encode('utf-8')).hexdigest().encode()
            self.Note = SavableNote(name=self.Name.text, key=key, text=self.Note.text, date=self.Note.text, author=self.Author.text)
            marshal_data = marshal.dumps(self.Note.toJSON())
            f = open(path, mode="wb")
            marshal.dump(marshal_data, f)
            RunApp.ScreenManager.current = "NoteEntry"  # TODO Change this to a "Information" screen.


class NotePage(GridLayout):
    def __init__(self, **kwargs):
        super(NotePage, self).__init__(**kwargs)
        self.Editing = True
        self.rows = 3
        self.cols = 1
        self.TopRow = GridLayout(cols=1, rows=1)

        self.MiddleRow = GridLayout(cols=3, rows=1, size_hint=(1, .1))
        self.Minimise = Button(text="-", color=(1, 1, 1, 1), size_hint=(.1, 1), font_size=75, on_press=self.ShowOrHideText)
        self.SaveButton = Button(text="Save", color=(1, 1, 1, 1), size_hint=(.1, 1), on_press=self.SaveNote)

        self.TextIArea = TextInput(multiline=True, text="Test", size_hint=(1, 1))

        self.TextArea = Label(text=self.TextIArea.text, markup=True)

        # Top Row stuff
        self.TopRow.add_widget(self.TextArea)
        # self.add_widget(self.TopRow)

        # Middle Row stuff
        self.MiddleRow.add_widget(self.Minimise)
        self.MiddleRow.add_widget(self.SaveButton)
        self.MiddleRow.add_widget(Label())

        self.add_widget(self.MiddleRow)

        # Bottom row?
        self.add_widget(self.TextIArea)

    def ShowOrHideText(self, *args):
        if self.Editing:
            self.Minimise.text = "+"
            # self.TextIArea.size_hint = (0, 0)
            self.remove_widget(self.TextIArea)
            # self.TopRow.size_hint = (1, 1)
            self.add_widget(self.TopRow)
            # self.TextArea.size_hint = (1, 1)
            self.TextArea.text = self.TextIArea.text
            self.Editing = False
        else:
            self.Minimise.text = "-"
            # self.TextIArea.size_hint = (1, 1)
            self.add_widget(self.TextIArea)
            # self.TopRow.size_hint = (0, 0)
            self.remove_widget(self.TopRow)
            # self.TextArea.size_hint = (0, 0)
            self.Editing = True

    def SaveNote(self, *args):
        Note = SavableNote(name=None, key=None, text=self.TextArea.text, date=dt.datetime.now().strftime("%d-%m-%Y"), password=None, author=None)
        RunApp.SavePage.setData(Note)
        RunApp.ScreenManager.current = "Save"


# noinspection PyAttributeOutsideInit
class NoteForYourThoughts(App):

    ScreenManager = None

    def build(self):
        self.ScreenManager = ScreenManager()

        self.NoteEntry = NotePage()
        screen = Screen(name="NoteEntry")
        screen.add_widget(self.NoteEntry)
        self.ScreenManager.add_widget(screen)

        self.SavePage = SavePage()
        screen = Screen(name="Save")
        screen.add_widget(self.SavePage)
        self.ScreenManager.add_widget(screen)

        return self.ScreenManager


if __name__ == '__main__':
    RunApp = NoteForYourThoughts()
    RunApp.run()
