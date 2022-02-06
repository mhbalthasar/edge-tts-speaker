#!/usr/bin/python3
import sys
import os
sys.path.append(os.path.abspath("../packages"))

from edge_tts import Communicate
import asyncio
import threading


class Debug:
    def __init__(self):
        pass

    def test(self):
        asyncio.run(self.test2())

    async def test2(self):
        engine=Communicate();
        async for i in engine.run(
                "I do not know where is the result.but if you want i to say anything i will do that."
                ):
            print(i[2])

def main():
    t=Debug()
    t1=threading.Thread(target=t.test)
    t1.start()

main()
