import os
import requests
from flask import Flask, request, redirect, session, url_for, render_template
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
from databases import database as IDConvertionDB
from japaneseProcessing import (
    processSimilarity,
    processPossibleJapanese,
    normalize_text,
)

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
        "redirect_url", url_for("from_anime", _external=True)
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

    if response.status_code == 200:
        return response.json()
    else:
        return None


@app.route("/from-anime")
def from_anime():
    if notlogedin := assertLogin("from_anime"):
        return notlogedin
    response = _currently_playing()
    if response is None:
        session["previouslyPlayed"] = -1
        return render_template(
            "CurrentAnime.html", songInfo="Not Playing anything", animes=""
        )
    if session.get("previouslyPlayed") == response["item"]["id"]:
        return "No change in currently playing song", 204  # No Content status code

    session["previouslyPlayed"] = response["item"]["id"]

    mostLikelyAnime, certainty = findMostLikelyAnime(response)

    return formatAnimeList(response, mostLikelyAnime, certainty)


def findSongsByArtists(
    currentlyPlaying, accuracyCutOff
) -> List[tuple[Song_Entry, float]]:
    artists = currentlyPlaying["item"]["artists"]
    idconverter = IDConvertionDB.database()
    db = AnisongDB()
    animeSongEntries = []
    artistIds = []
    for a in artists:
        id = idconverter.getArtist(a["id"])
        if id is not None:
            artistIds.append(id)
    if len(artistIds) > 0:
        animeSongEntries = db.get_songs_artists(artistIds, True)
        if len(animeSongEntries) == 0:
            animeSongEntries = db.get_songs_artists(artistIds, False)
        if len(animeSongEntries) == 0:
            return []

    else:
        for artist in artists:
            romanjiArtist = processPossibleJapanese(artist["name"])

            search = Search_Request(
                artist_search_filter=Search_Filter(
                    search=romanjiArtist, partial_match=False
                ),
            )
            animeSongEntries.extend(db.get_songs(search))

    weighed_anime: List[tuple[Song_Entry, int]] = []
    romanjiSongTitle = processPossibleJapanese(currentlyPlaying["item"]["name"])
    for anime in animeSongEntries:
        score = processSimilarity(romanjiSongTitle, anime.songName)
        print(
            anime.animeENName, score, romanjiSongTitle.strip(), " vs ", anime.songName
        )
        if score > accuracyCutOff:
            weighed_anime.append((anime, score))
    return weighed_anime


def findSongsBySongTitle(
    currentlyPlaying, accuracyCutOff
) -> List[tuple[Song_Entry, float]]:
    romanjiSongTitle = processPossibleJapanese(currentlyPlaying["item"]["name"])
    search = Search_Request(
        song_name_search_filter=Search_Filter(
            search=romanjiSongTitle.strip(), partial_match=False
        ),
    )
    artists = currentlyPlaying["item"]["artists"]
    db = AnisongDB()
    animeNames = db.get_songs(search)

    weighed_anime: List[tuple[Song_Entry, int]] = []
    for anime in animeNames:
        score = 0
        for artist in artists:
            romanjiArtist = processPossibleJapanese(artist["name"])
            maxScore = 0
            for songArtist in anime.artists:
                tempscore = processSimilarity(romanjiArtist, songArtist.names[0])
                if tempscore > maxScore:
                    maxScore = tempscore
            if maxScore > score:
                score = maxScore
        if score > accuracyCutOff:
            weighed_anime.append((anime, score))
    return weighed_anime


def findMostLikelyAnime(response) -> tuple[List[Song_Entry], int]:
    accuracy = 40
    idconverter = IDConvertionDB.database()
    db = AnisongDB()
    song = idconverter.getSong(response["item"]["id"])
    if song[0] is not None:
        return db.get_exact_song(song[0], song[1]), 100

    romanjiTitle = processPossibleJapanese(response["item"]["name"])

    artists = response["item"]["artists"]

    weighed_anime: List[tuple[Song_Entry, int]] = findSongsByArtists(response, accuracy)

    if len(weighed_anime) == 0:
        weighed_anime = findSongsBySongTitle(response, accuracy)

    weighed_anime.sort(key=lambda a: a[1], reverse=True)

    if len(weighed_anime) > 0:
        weighed_anime = list(
            filter(lambda a: a[1] == weighed_anime[0][1], weighed_anime)
        )

    if len(weighed_anime) > 0:
        if weighed_anime[0][1] > 90:
            idconverter.insertSong(
                response["item"]["id"],
                weighed_anime[0][0].songName,
                [a.id for a in weighed_anime[0][0].artists],
            )
        if len(artists) == len(weighed_anime[0][0].artists) == 1:
            if idconverter.getArtist(artists[0]["id"]) == None:
                idconverter.insertArtist(
                    artists[0]["id"], weighed_anime[0][0].artists[0].id
                )
    else:
        print("------------Song Miss------------")
        print(
            romanjiTitle + ", Artists:",
            ", ".join(
                [
                    processPossibleJapanese(a["name"])
                    for a in response["item"]["artists"]
                ]
            ),
        )
    certainty = 0
    if len(weighed_anime):
        print(
            f"Best Match for: '{response["item"]["name"]}' by '{"', '".join([a["name"] for a in response["item"]["artists"]])}' is:\n\t'{weighed_anime[0][0].songName}' by '{"', '".join([a.names[0] for a in weighed_anime[0][0].artists])}'\n\tScore: {weighed_anime[0][1]}"
        )
        certainty = weighed_anime[0][1]

    return list(set([a[0] for a in weighed_anime])), certainty


def getAnimeNames(rawSongData: List[Song_Entry]) -> str:
    output = []
    for song in rawSongData:
        output.append(
            {
                "title": f"'{song.animeENName}', {song.animeCategory} {song.songType}",
                "url": f"https://myanimelist.net/anime/{song.linked_ids.myanimelist}"
            }
        )
    return output


def formatAnimeList(playing, rawSongData: List[Song_Entry], certainty) -> str:
    animes = getAnimeNames(rawSongData)
    if len(animes) == 0:
        render_template("CurrentAnime.html", songInfo="Couldn't find a good match for this song!", anime="")

    songInfo = f"The song '{playing["item"]["name"]}' by '{"', '".join([i["name"] for i in playing["item"]["artists"]])}' is a {certainty}% match for the following:"

    return render_template("CurrentAnime.html", songInfo=songInfo, animes=animes)
    # return output


if __name__ == "__main__":
    print("http://127.0.0.1:8000/from-anime")
    app.run(port=8000, debug=False)
