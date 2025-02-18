import os
import json
import requests
from flask import Flask, request, redirect, session, url_for, jsonify
from urllib.parse import urlencode
from dotenv import load_dotenv
import time
from typing import List
from AnisongDBI import (
    AnisongDB_Interface as AnisongDB,
    Search_Request,
    Search_Filter,
    Song_Entry,
)
import pykakasi
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import sqlite3
from databases import database as IDConvertionDB

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

client_id = os.getenv("ClientID")
client_secret = os.getenv("ClientSecret")
redirect_uri = "http://127.0.0.1:8000/callback"


@app.route("/login")
def login():
    state = os.urandom(16).hex()
    scope = "user-read-private user-read-email user-read-playback-state user-read-currently-playing"
    session["state"] = state
    session["redirect_url"] = request.args.get("redirect")

    auth_params = {
        "response_type": "code",
        "client_id": client_id,
        "scope": scope,
        "redirect_uri": redirect_uri,
        "state": state,
    }
    auth_url = f"https://accounts.spotify.com/authorize?{urlencode(auth_params)}"
    return redirect(auth_url)


@app.route("/callback")
def callback():
    code = request.args.get("code")
    state = request.args.get("state")

    if state != session.get("state"):
        return "State mismatch", 400

    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret,
    }
    token_headers = {"Content-Type": "application/x-www-form-urlencoded"}

    token_response = requests.post(
        "https://accounts.spotify.com/api/token", data=token_data, headers=token_headers
    )
    token_info = token_response.json()

    session["access_token"] = token_info["access_token"]
    session["refresh_token"] = token_info["refresh_token"]
    session["expire_time"] = time.time() + token_info["expires_in"]

    redirect_url = session.pop(
        "redirect_url", url_for("currently_playing", _external=True)
    )
    return redirect(redirect_url)


def refresh_access_token():
    refresh_token = session.get("refresh_token")
    token_data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
    }
    token_headers = {"Content-Type": "application/x-www-form-urlencoded"}

    token_response = requests.post(
        "https://accounts.spotify.com/api/token", data=token_data, headers=token_headers
    )
    token_info = token_response.json()

    session["access_token"] = token_info["access_token"]
    session["expire_time"] = time.time() + token_info["expires_in"]


@app.route("/currently-playing")
def currently_playing():
    if notlogedin := assertLogin("currently_playing"):
        return notlogedin
    return _currently_playing()


def assertLogin(redir: str):
    access_token = session.get("access_token")
    if not access_token:
        return redirect(url_for("login", redirect=url_for(redir, _external=True)))

    if time.time() > session.get("expire_time"):
        refresh_access_token()


def _currently_playing():

    access_token = session.get("access_token")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    response = requests.get(
        "https://api.spotify.com/v1/me/player/currently-playing", headers=headers
    )
    return response.json()


@app.route("/from-anime")
def from_anime():
    if notlogedin := assertLogin("from_anime"):
        return notlogedin
    response = _currently_playing()

    return formatAnimeList(response, findMostLikelyAnime(response))


def findMostLikelyAnime(response, partial: bool = False) -> List[Song_Entry]:
    idconverter = IDConvertionDB.database()
    db = AnisongDB()
    song = idconverter.getSong(response["item"]["id"])
    if song[0] is not None:
        return db.get_exact_song(song[0], song[1])

    kks = pykakasi.kakasi()
    romanjiTitle = " ".join(t["kunrei"] for t in kks.convert(response["item"]["name"]))

    artists = response["item"]["artists"]

    animeNames = []
    artistIds = []
    for a in artists:
        id = idconverter.getArtist(a["id"])
        if id is not None: artistIds.append(id)
    if len(artistIds) > 0:
        print(artistIds)
        animeNames = db.get_songs_artists(artistIds, True)
        if len(animeNames) == 0:
            animeNames = db.get_songs_artists(artistIds, False)
        if len(animeNames) == 0: return []

    else:
        for artist in artists:
            romanjiArtist = " ".join([word["kunrei"]for word in kks.convert(artist["name"])])

            print(romanjiArtist)
            search = Search_Request(
                artist_search_filter=Search_Filter(
                    search=romanjiArtist, partial_match=partial
                ),
            )
            animeNames.extend(db.get_songs(search))

    weighed_anime: List[tuple[Song_Entry, int]] = []
    for anime in animeNames:
        score = fuzz.token_sort_ratio(romanjiTitle.strip(), anime.songName)
        if score > 50:
            weighed_anime.append((anime, score))

    if len(weighed_anime) == 0:
        search = Search_Request(
            song_name_search_filter=Search_Filter(
                search=romanjiTitle.strip(), partial_match=partial
            ),
        )
        animeNames = db.get_songs(search)
        for anime in animeNames:
            score = fuzz.token_sort_ratio(romanjiTitle, anime.songName)
            if score > 50:
                weighed_anime.append((anime, score))

    weighed_anime.sort(key=lambda a : a[1])

    if not partial and len(weighed_anime) > 0:
        idconverter.insertSong(
            response["item"]["id"],
            weighed_anime[0][0].songName,
            [a.id for a in weighed_anime[0][0].artists],
        )
        if len(artists) == len(weighed_anime[0][0].artists) == 1:
            print(animeNames[0].artists)
            idconverter.insertArtist(artist["id"], animeNames[0].artists[0].id)
    else:
        print("------------Song Miss------------")
        print(romanjiTitle + ", Artists:", ", ".join([a["name"] for a in artists]))
        print("Found alternatives: ", [a.animeJPName for a in animeNames])
    print(len(animeNames))
    print(romanjiTitle)
    print(romanjiArtist)

    return [a[0] for a in weighed_anime[:5]]



def getAnimeNames(rawSongData: List[Song_Entry]) -> str:
    output = ""
    for song in rawSongData:
        output += f"'{song.animeENName}', {song.animeCategory} {song.songType} <a href=https://myanimelist.net/anime/{song.linked_ids.myanimelist}>Mal Link</a>\n"
        print(song.linked_ids)
    return output


def formatAnimeList(playing, rawSongData: List[Song_Entry]) -> str:
    output = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Anime Song List</title>
        <link rel="stylesheet" href={url_for("static", filename="styles.css")}>
    </head>
    <body>
        <h1>Possible Anime '{playing["item"]["name"]}' by '{"', '".join([i["name"] for i in playing["item"]["artists"]])}' could be from</h1>
        <h3 class="preserve-whitespace">
{getAnimeNames(rawSongData)}
        </h3>
    </body>
    </html>
    """
    return output


if __name__ == "__main__":
    print("http://127.0.0.1:8000/currently-playing")
    app.run(port=8000, debug=True)
