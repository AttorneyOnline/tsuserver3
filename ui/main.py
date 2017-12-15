import pygubu
import gettext
t = gettext.translation("default", "locales")
_ = t.gettext

class TsuserverConfig:
    def __init__(self):
        self.builder = builder = pygubu.Builder(_)
        builder.add_from_file("main.ui")
        self.main_window = builder.get_object("tsuserver_config_toplevel")

    def run(self):
        self.main_window.mainloop()

    def quit(self, event=None):
        self.main_window.quit()

def main():
    application = TsuserverConfig()
    application.run()