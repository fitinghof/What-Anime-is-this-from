import sqlite3
from typing import List

hardSongs = [
]

hardArtists = [
]

class database:
    def artistsIsEmpty(self):
        self.spotify_artistID_db_cursor.execute("SELECT 1 FROM your_table LIMIT 1")
        return self.spotify_artistID_db_cursor.fetchone() is None

    def songsIsEmpty(self):
        self.spotify_songID_db_cursor.execute("SELECT 1 FROM your_table LIMIT 1")
        return self.spotify_songID_db_cursor.fetchone() is None

    def addHardSongs(self):
        for song in hardSongs:
            self.insertSong(song[0], song[1], song[2])

    def addHardArtists(self):
        for artist in hardArtists:
            self.insertArtist(artist[0], artist[1])

    def __init__(self):
        self.spotify_songID_db = sqlite3.connect('databases/spotify_songID.db')
        self.spotify_artistID_db = sqlite3.connect('databases/spotify_artistID.db')
        self.spotify_artistID_db_cursor = self.spotify_artistID_db.cursor()
        self.spotify_songID_db_cursor = self.spotify_songID_db.cursor()
        self.spotify_songID_db_cursor.execute('''
            CREATE TABLE IF NOT EXISTS songs (
                spotify_id TEXT PRIMARY KEY,
                song_name TEXT,
                artistIDs TEXT
            )
            ''')
        self.spotify_artistID_db_cursor.execute('''
            CREATE TABLE IF NOT EXISTS artists (
                spotify_id TEXT PRIMARY KEY,
                anisong_id INTEGER
            )
            ''')
        self.addHardSongs()
        self.addHardArtists()
    def getSong(self, spotifyID):
        self.spotify_songID_db_cursor.execute('SELECT song_name, artistIDs FROM songs WHERE spotify_id = ?', (spotifyID,))
        result = self.spotify_songID_db_cursor.fetchone()
        if result:
            songName = result[0]
            other_ids = list(map(int, result[1].split(','))) if result[1] else []
            return songName, other_ids
        else:
            return None, []

    def getArtist(self, spotifyID):
        self.spotify_artistID_db_cursor.execute('SELECT anisong_id FROM artists WHERE spotify_id = ?', (spotifyID,))
        result = self.spotify_artistID_db_cursor.fetchone()
        if result:
            return result[0]
        else:
            return None


    def insertSong(self, spotifyID, songName, artistIDs: List):
        self.spotify_songID_db_cursor.execute('''
            INSERT INTO songs (spotify_id, song_name, artistIDs)
            VALUES (?, ?, ?)
        ''', (spotifyID, songName, ",".join(str(a) for a in artistIDs)))
        self.spotify_songID_db.commit()

    def insertArtist(self, spotifyID, anisongID):
        self.spotify_artistID_db_cursor.execute('''
            INSERT INTO artists (spotify_id, anisong_id)
            VALUES (?, ?)
        ''', (spotifyID, anisongID))
        self.spotify_artistID_db.commit()

