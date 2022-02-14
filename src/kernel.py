import src.tts_gui as gui
import edge_tts as tts
import sys
import os
import asyncio
from edge_tts import Communicate, SubMaker, list_voices
import re
import json
import threading
import subprocess as sp
from tkinter import filedialog as fd

class Ffplay():
    def __init__(self,target):
        self.target=target
        self.start();

    def start(self):
        cmd = ['/usr/bin/ffplay','-i','-','-f','mp3','-showmode','0','-infbuf','-vn','-nodisp','-ac','1','-ar','24000']
        self.pipe = sp.Popen(cmd, bufsize=0, stdin=sp.PIPE)
        self.play()

    def play(self):
        #This is Gen a empty sound file to boot ffplay,for the else it will wait for enough data when you put a quit little sound data.
        p=sp.Popen(['/usr/bin/ffmpeg','-f','lavfi','-t','1','-i','anullsrc','-ar','24000','-ac','1','-f','mp3','/tmp/tts-init.mp3','-y'])
        p.wait()
        if os.path.exists('/tmp/tts-init.mp3'):
            print("FileExit")
            with open('/tmp/tts-init.mp3','rb') as f:
                self.write(f.read())

    def write(self,data):
        self.pipe.stdin.write(data)
        self.pipe.stdin.flush()

    def close(self):
        self.pipe.stdin.close()
        self.pipe.terminate()

class Tts():
    WaitStopPlay=False
    def __init__(self,target):
        self.target=target

    async def list_voices(self):
        self.target.voicelists=[]
        self.target.voicemap={}
        for idx, voice in enumerate(await list_voices()):
            VoiceBindName=voice["Name"]
            VoiceLocale=voice["Locale"]
            VoiceFName=voice["FriendlyName"]
            match = re.match( r'Microsoft (.*) Online \(Natural\) - (.*)(.*)\((.*)\)', VoiceFName, re.M|re.I)
            VoiceName=match.group(1).strip()
            VoiceLang=match.group(2).strip()
            VoiceCountry=match.group(4).strip()
            VoiceTName="%s (%s,%s)" % (VoiceName, VoiceLang, VoiceCountry)
            if self.target.val_tts_voice.get()=="" and VoiceLang=="Chinese" and VoiceCountry=="Mainland":
                self.target.val_tts_voice.set(VoiceTName)
            self.target.voicelists.append(VoiceTName)
            self.target.voicemap[VoiceTName]=VoiceBindName

    def initArg(self):
        self.arg_esb=False
        self.arg_ewb=False
        self.arg_codec="audio-24khz-48kbitrate-mono-mp3"
        self.arg_voice=self.target.voicemap[self.target.val_tts_voice.get()]
        self.arg_pitch="%sHz" % self.target.ui_tts_pit.get()
        if int(self.target.ui_tts_pit.get())>=0:
            self.arg_pitch="+"+self.arg_pitch
        self.arg_rate=self.target.ui_tts_speed.get()+"%"
        if int(self.target.ui_tts_speed.get())>=0:
            self.arg_rate="+"+self.arg_rate
        #self.target.speedmap[self.target.ui_tts_speed.get()]
        self.arg_volume="+0%"
        self.arg_custom_ssml=False

    def _synthTTS(self, text):
        asyncio.run(self._doSynthTTS(text))

    def synthTTS(self, text):
        t1 = threading.Thread(target=self._synthTTS, args=(text,))
        t1.setDaemon(True)
        t1.start()

    async def _doSynthTTS(self, text):
        engine = Communicate()
        async for i in engine.run(
                text,
                self.arg_esb,
                self.arg_ewb,
                self.arg_codec,
                self.arg_voice,
                self.arg_pitch,
                self.arg_rate,
                self.arg_volume,
                customspeak=self.arg_custom_ssml,
        ):
            if not self.WaitStopPlay :
                self.target.ffplay.write(i[2])
        self.WaitStopPlay=False

    def _synthTTStoFile(self, text, filepath):
        asyncio.run(self._doSynthTTSToFile(text,filepath))

    def synthTTStoFile(self, text,filepath):
        t1 = threading.Thread(target=self._synthTTStoFile, args=(text,filepath,))
        t1.setDaemon(True)
        t1.start()

    async def _doSynthTTSToFile(self, text,filepath):
        engine = Communicate()
        with open(filepath,'wb') as f:
            async for i in engine.run(
                text,
                self.arg_esb,
                self.arg_ewb,
                self.arg_codec,
                self.arg_voice,
                self.arg_pitch,
                self.arg_rate,
                self.arg_volume,
                customspeak=self.arg_custom_ssml,
            ):
                f.write(i[2])

    def stopTTS(self):
        self.WaitStopPlay=True
        self.target.ffplay.close()
        self.target.ffplay.start()

class App(gui.TtsguiApp):
    async def run(self):
        self.tts=Tts(self)
        self.ffplay=Ffplay(self)
        await self.tts.list_voices()
        self.ui_tts_voice.configure(values=self.voicelists)
        #self.speedmap={}
        #self.speedmap["-2"]="x-slow"
        #self.speedmap["-1"]="slow"
        #self.speedmap["0"]="medium"
        #self.speedmap["1"]="fast"
        #self.speedmap["2"]="x-fast"
        self.val_tts_speed.set(0)#rate
        self.val_tts_pit.set(0)#pitch
        self.toplevel2.protocol("WM_DELETE_WINDOW", self.event_on_closing)
        self.mainwindow.mainloop()

    def event_on_closing(self):
        self.toplevel2.destroy()
        self.ffplay.close()

    def event_tts_btn_play(self):
        self.tts.stopTTS()
        self.tts=Tts(self)
        self.tts.initArg()
        text=self.ui_tts_text.get("1.0","end")
        self.tts.synthTTS(text)

    def event_tts_btn_pause(self):
        pass

    def event_tts_btn_stop(self):
        self.tts.stopTTS()
        pass

    def event_tts_btn_download(self):
        self.tts.initArg()
        text=self.ui_tts_text.get("1.0","end")
        filef = fd.asksaveasfile(title=u'保存文件',filetypes=[("MP3 file", ".mp3")])
        if filef is None:
            pass
        else:
            fpath=filef.name
            filef.close()
            self.tts.synthTTStoFile(text,fpath)
        pass


