import marshal
import hashlib
import os
import secrets
import time

from kivy.app import App
from kivy.uix.gridlayout import GridLayout  # Main layout to be used in the project
from kivy.uix.screenmanager import ScreenManager, Screen  # Allow to easily switch between screens
from kivy.core.window import Window

# Widgets
from kivy.uix.label import Label  # Label for either text showing or blank bar
from kivy.uix.button import Button  # Button for you guessed it button things.
from kivy.uix.textinput import TextInput  # Text input Widget
from kivy.uix.filechooser import FileChooserListView


# Encryption
from NotesEncrpytion import encryption

# Time
import datetime as dt


HASH_FUNC = hashlib.sha512


class SavableNote:
    def __init__(self, name=None, key=None, text=None, date=None, password=None, author=None, decrypt=False, iv=None, work_factor=20_000):
        self.name = name
        self.key = key
        self.author = author
        self.date = date
        if self.key is not None and not decrypt:
            self.Cipher = encryption.AESCipher(self.key)
            self.iv = self.Cipher.iv
            self.text = self.Cipher.encrypt(text)
            self.work_factor = work_factor
            self.salt = secrets.token_urlsafe(128).encode('utf-8')  # 128 bit salt for security purposes
            self.hashed_password = hashlib.pbkdf2_hmac("sha256", password.encode('utf-8'), self.salt, self.work_factor).hex()
        elif self.key is not None and decrypt and iv is not None:
            self.Cipher = encryption.AESCipher(self.key)
            self.Cipher.iv = iv
            self.text = self.Cipher.decrypt(text)
        else:
            self.text = text

    def toJSON(self):
        return {'name': self.name, 'author': self.author, 'date': self.date,
                'cipher': self.Cipher.toJSON(), 'iv': self.iv, 'text': self.text,
                'hashed_password': self.hashed_password, 'work_factor': self.work_factor,
                'salt': self.salt}

    def fromJSON(self, json_data):
        self.Cipher = encryption.AESCipher()
        self.name = json_data['name']
        self.author = json_data['author']
        self.date = json_data['date']
        self.Cipher.fromJSON(json_data['cipher'])
        self.iv = json_data['iv']
        self.text = json_data['text']
        self.hashed_password = json_data['hashed_password']
        self.work_factor = json_data['work_factor']
        self.salt = json_data['salt']


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
        self.Save.bind(on_release=self.SaveBind)
        self.add_widget(self.Save)

        Window.bind(on_key_down=self.on_key_down)

    def on_key_down(self, instance, keyboard, keycode, text, modifiers):
        if keycode == 13 and RunApp.ScreenManager.current == "Save":
            self.SaveBind(instance, keyboard, keycode, text, modifiers)

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
            key = HASH_FUNC(self.Password.text.encode('utf-8')).hexdigest().encode()
            self.Note = SavableNote(name=self.Name.text, key=key, text=self.Note.text, date=self.Note.text, author=self.Author.text, password=self.Password.text)
            marshal_data = marshal.dumps(self.Note.toJSON())
            f = open(path, mode="wb")
            marshal.dump(marshal_data, f)
            RunApp.ScreenManager.current = "NoteEntry"


class LoadPage(GridLayout):
    def __init__(self, **kwargs):
        super(LoadPage, self).__init__(**kwargs)
        self.cols = 0
        self.rows = 2
        self.FileChooser = FileChooserListView(path='./notes/', size_hint=(1, .4), filters=['*.note'])
        self.add_widget(self.FileChooser)

        self.BottomLayout = GridLayout(cols=2, rows=3, size_hint=(1, .05))

        self.BottomLayout.add_widget(Label(text="Password\n", markup=True))
        self.Password = TextInput(multiline=False, password=True)
        self.BottomLayout.add_widget(self.Password)

        self.Cancel = Button(text="Cancel", color=(1, 1, 1, 1))
        self.Cancel.bind(on_release=self.CancelBind)
        self.BottomLayout.add_widget(self.Cancel)
        self.Load = Button(text="Load", color=(1, 1, 1, 1))
        self.Load.bind(on_release=self.LoadBind)
        self.BottomLayout.add_widget(self.Load)

        self.add_widget(self.BottomLayout)

    @staticmethod
    def CancelBind(*args):
        RunApp.ScreenManager.current = "NoteEntry"

    def LoadBind(self, *args):
        password = self.Password.text
        name = self.FileChooser.path + "/" + os.path.basename(self.FileChooser.selection[0])
        if ".note" not in name:
            name += ".note"
        f = open(f'{name}', 'rb')
        open_marshal = marshal.load(f)
        NewNote = SavableNote()
        NewNote.fromJSON(marshal.loads(open_marshal))
        hashed_password = NewNote.hashed_password
        work_factor = NewNote.work_factor
        salt = NewNote.salt
        if hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, work_factor).hex() == hashed_password:
            key = HASH_FUNC(self.Password.text.encode('utf-8')).hexdigest().encode()
            PlainTextNote = SavableNote(name=name.split('.')[0], key=key, decrypt=True, iv=NewNote.iv, text=NewNote.text)
            RunApp.NoteEntry.TextArea.text = PlainTextNote.text
            RunApp.NoteEntry.TextIArea.text = PlainTextNote.text
            if not RunApp.NoteEntry.Editing:
                RunApp.NoteEntry.Editing = True
                RunApp.NoteEntry.ShowOrHideText()
            RunApp.ScreenManager.current = "NoteEntry"
        else:
            RunApp.InfoPage.update_info("Error Password is wrong.")
            RunApp.InfoPage.Next = "NoteEntry"
            RunApp.ScreenManager.current = "Info"
            # RunApp.ScreenManager.current = "NoteEntry"


class InfoPage(GridLayout):
    Next = ""
    def __init__(self, **kwargs):
        super(InfoPage, self).__init__(**kwargs)
        if self.Next == "" and RunApp.ScreenManager.current == "Info":
            raise Exception(f"Invalid Info Page.")

        # Add just one column
        self.cols = 1
        self.rows = 2

        # Add one label for a message
        self.MessageLabel = Label(halign="center", valign="middle", font_size=30)
        self.Continue = Button(text="Continue", color=(1, 1, 1, 1), size_hint=(1, .1))
        self.Continue.bind(on_release=self.continue_bind)
    

        # By default every widget returns it's side as [100, 100], it gets finally resized,
        # but we have to listen for size change to get a new one
        # more: https://github.com/kivy/kivy/issues/1044
        self.MessageLabel.bind(width=self.update_text_width)

        # Add Label to layout
        self.add_widget(self.MessageLabel)
        self.add_widget(self.Continue)
    
    def continue_bind(self, *args):
        RunApp.ScreenManager.current = self.Next
        self.Next = ""

    def update_info(self, message):
        self.MessageLabel.text = message

    def update_text_width(self, *_):
        self.MessageLabel.text_size = (self.MessageLabel.width * 0.9, None)


class NotePage(GridLayout):
    def __init__(self, **kwargs):
        super(NotePage, self).__init__(**kwargs)
        self.Editing = True
        self.rows = 3
        self.cols = 1
        self.TopRow = GridLayout(cols=1, rows=1)

        self.MiddleRow = GridLayout(cols=4, rows=1, size_hint=(1, .1))
        self.Minimise = Button(text="-", color=(1, 1, 1, 1), size_hint=(.1, 1), font_size=75, on_press=self.ShowOrHideText)
        self.SaveButton = Button(text="Save", color=(1, 1, 1, 1), size_hint=(.1, 1), on_press=self.SaveNote)
        self.LoadButton = Button(text="Load", color=(1, 1, 1, 1), size_hint=(.1, 1), on_press=self.LoadNote)

        self.TextIArea = TextInput(multiline=True, text="Test", size_hint=(1, 1))

        self.TextArea = Label(text=self.TextIArea.text, markup=True)

        # Top Row stuff
        self.TopRow.add_widget(self.TextArea)
        # self.add_widget(self.TopRow)

        # Middle Row stuff
        self.MiddleRow.add_widget(self.Minimise)
        self.MiddleRow.add_widget(self.SaveButton)
        self.MiddleRow.add_widget(self.LoadButton)
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
        RunApp.SavePage.setNote(Note)
        RunApp.ScreenManager.current = "Save"

    @staticmethod
    def LoadNote(*args):
        RunApp.ScreenManager.current = "Load"


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

        self.LoadPage = LoadPage()
        screen = Screen(name="Load")
        screen.add_widget(self.LoadPage)
        self.ScreenManager.add_widget(screen)

        self.InfoPage = InfoPage()
        screen = Screen(name="Info")
        screen.add_widget(self.InfoPage)
        self.ScreenManager.add_widget(screen)

        try:
            os.mkdir('./notes/')
        except FileExistsError:
            pass

        return self.ScreenManager


if __name__ == '__main__':
    RunApp = NoteForYourThoughts()
    RunApp.run()
