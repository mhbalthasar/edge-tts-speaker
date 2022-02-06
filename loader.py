#!/usr/bin/python3

import os
import sys
import asyncio

module_path=os.path.abspath(os.path.join(os.path.split(os.path.realpath(__file__))[0],"packages"))
sys.path.append(module_path)

import src.kernel as App

if __name__ == '__main__':
    app = App.App()
    asyncio.run(app.run())
