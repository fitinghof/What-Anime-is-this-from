import webbrowser
import requests
from typing import List, Optional
from pydantic import BaseModel, Field, TypeAdapter
from time import time
from dotenv import load_dotenv
import os
import json

load_dotenv()


class SongEntry:
    stuff: int


class ISpotify:
    timeout: float
    access_token: str

    def __init__(self):
        pass

    def getCurrentlyPlaying(self) -> Optional[SongEntry]:
        response = requests.get(
            "http://127.0.0.1:8000/currently-playing", allow_redirects=False
        )
        if response.status_code == 200:
            print(json.dumps(response.json(), indent=4))
            return response.json()
        else:
            self.perform_login(response.url)
            self.getCurrentlyPlaying()
            return None

    def perform_login(self, login_url: str):
        # Simulate the login process
        print(f"Please go to this URL and authorize the application: ")
        response = requests.get(
            "http://127.0.0.1:8000/login", allow_redirects=True
        )
        webbrowser.open(response)


        redirect_response = input("Done? ")
        print(response.text)
        redirect_response = input("Done? ")

