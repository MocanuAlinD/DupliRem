from kivy.app import App
from kivy.uix.screenmanager import Screen,ScreenManager
from kivy.lang import Builder
from clss.mainPage import MainPage
from kivy.core.window import Window as w
import platform
from win32api import GetSystemMetrics


class WindowManager(ScreenManager):
    pass


class DupliRemApp(App):
    def build(self):
        
        w.size = (GetSystemMetrics(0)/1.3, GetSystemMetrics(1)/1.3)
        # w.size = (GetSystemMetrics(0), GetSystemMetrics(1)-65)
        w.top = 25
        w.left = 150
        Builder.load_file('kvs/mainPage.kv')
        screen = Builder.load_file('kvs/main.kv')
        return screen

    

if __name__=='__main__':
    DupliRemApp().run()