# -*- coding: utf-8 -*-
import pathlib
import pygubu
import tkinter as tk
import tkinter.ttk as ttk

PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / "ttsgui.ui"

class TtsguiApp:
    def __init__(self, master=None):
        # build ui
        self.toplevel2 = tk.Tk() if master is None else tk.Toplevel(master)
        self.frame3 = ttk.Frame(self.toplevel2)
        self.labelframe5 = ttk.Labelframe(self.frame3)
        self.ui_tts_text = tk.Text(self.labelframe5)
        self.ui_tts_text.configure(height='30', width='80')
        self.ui_tts_text.pack(expand='true', fill='both', side='top')
        self.labelframe5.configure(height='500', text='文本内容', width='800')
        self.labelframe5.pack(expand='true', fill='both', padx='10', side='top')
        self.frame4 = ttk.Frame(self.frame3)
        self.labelframe10 = ttk.Labelframe(self.frame4)
        self.frame6 = ttk.Frame(self.labelframe10)
        self.label3 = ttk.Label(self.frame6)
        self.label3.configure(text='朗读音源：')
        self.label3.grid(column='0', padx='10', pady='10', row='0')
        self.ui_tts_voice = ttk.Combobox(self.frame6)
        self.val_tts_voice = tk.StringVar(value='')
        self.ui_tts_voice.values=['AAA']
        self.ui_tts_voice.configure(textvariable=self.val_tts_voice, width='30')
        self.ui_tts_voice.grid(column='1', columnspan='3', padx='10', pady='10', row='0')
        self.label2 = ttk.Label(self.frame6)
        self.label2.configure(text='语调：')
        self.label2.grid(column='0', row='1')
        self.ui_tts_pit = ttk.Spinbox(self.frame6)
        self.val_tts_pit = tk.IntVar(value='')
        self.ui_tts_pit.configure(from_='-2', textvariable=self.val_tts_pit, to='2', width='5')
        self.ui_tts_pit.grid(column='1', pady='10', row='1')
        self.label4 = ttk.Label(self.frame6)
        self.label4.configure(text='语速：')
        self.label4.grid(column='2', padx='15', row='1')
        self.ui_tts_speed = ttk.Spinbox(self.frame6)
        self.val_tts_speed = tk.IntVar(value='')
        self.ui_tts_speed.configure(from_='-2', textvariable=self.val_tts_speed, to='2', width='5')
        self.ui_tts_speed.grid(column='3', row='1')
        self.frame6.configure(height='50', width='200')
        self.frame6.grid(column='0', ipady='1', row='0')
        self.labelframe10.configure(height='70', text='声音选项', width='200')
        self.labelframe10.pack(anchor='w', expand='false', padx='10', pady='10', side='left')
        self.labelframe1 = ttk.Labelframe(self.frame4)
        self.frame1 = ttk.Frame(self.labelframe1)
        self.ui_tts_playtime = ttk.Label(self.frame1)
        self.val_tts_playtime = tk.StringVar(value='[000:00:00]')
        self.ui_tts_playtime.configure(text='[000:00:00]', textvariable=self.val_tts_playtime)
        self.ui_tts_playtime.pack(padx='10', pady='10', side='top')
        self.ui_tts_currenttext = ttk.Entry(self.frame1)
        self.val_tts_currenttext = tk.StringVar(value='')
        self.ui_tts_currenttext.configure(textvariable=self.val_tts_currenttext)
        self.ui_tts_currenttext.pack(expand='true', fill='x', padx='10', pady='10', side='right')
        self.frame1.configure(height='50', width='200')
        self.frame1.pack(expand='true', fill='x', side='top')
        self.labelframe1.configure(height='70', text='当前朗读语句', width='200')
        self.labelframe1.pack(anchor='w', expand='true', fill='x', padx='10', pady='10', side='left')
        self.labelframe11 = ttk.Labelframe(self.frame4)
        self.frame5 = ttk.Frame(self.labelframe11)
        self.ui_tts_btn_play = ttk.Button(self.frame5)
        self.val_tts_btn_play = tk.StringVar(value='朗读')
        self.ui_tts_btn_play.configure(text='朗读', textvariable=self.val_tts_btn_play)
        self.ui_tts_btn_play.grid(column='1', pady='5', row='0')
        self.ui_tts_btn_play.configure(command=self.event_tts_btn_play)
        self.ui_tts_btn_pause = ttk.Button(self.frame5)
        self.val_tts_btn_pause = tk.StringVar(value='暂停')
        self.ui_tts_btn_pause.configure(text='暂停', textvariable=self.val_tts_btn_pause)
        self.ui_tts_btn_pause.grid(column='2', row='0')
        self.ui_tts_btn_pause.configure(command=self.event_tts_btn_pause)
        self.ui_tts_btn_stop = ttk.Button(self.frame5)
        self.val_tts_btn_stop = tk.StringVar(value='停止')
        self.ui_tts_btn_stop.configure(text='停止', textvariable=self.val_tts_btn_stop)
        self.ui_tts_btn_stop.grid(column='1', pady='5', row='1')
        self.ui_tts_btn_stop.configure(command=self.event_tts_btn_stop)
        self.ui_tts_btn_download = ttk.Button(self.frame5)
        self.val_tts_btn_download = tk.StringVar(value='下载')
        self.ui_tts_btn_download.configure(text='下载', textvariable=self.val_tts_btn_download)
        self.ui_tts_btn_download.grid(column='2', row='1')
        self.ui_tts_btn_download.configure(command=self.event_tts_btn_download)
        self.frame5.configure(height='50', width='200')
        self.frame5.grid(column='0', padx='10', pady='2', row='0')
        self.labelframe11.configure(height='70', text='播放控制', width='200')
        self.labelframe11.pack(anchor='e', expand='false', padx='10', pady='10', side='right')
        self.frame4.configure(height='70', width='800')
        self.frame4.pack(expand='false', fill='x', ipady='5', side='top')
        self.frame3.configure(height='100', width='800')
        self.frame3.pack(anchor='center', expand='true', fill='both', side='top')
        self.toplevel2.resizable(True, True)
        self.toplevel2.title('Talk To Text AI')

        # Main widget
        self.mainwindow = self.toplevel2
    
    def run(self):
        self.mainwindow.mainloop()

    def event_tts_btn_play(self):
        pass

    def event_tts_btn_pause(self):
        pass

    def event_tts_btn_stop(self):
        pass

    def event_tts_btn_download(self):
        pass


if __name__ == '__main__':
    app = TtsguiApp()
    app.run()



