from pydantic import BaseModel, Field, TypeAdapter

class Device(BaseModel):
    id: str
    is_active: bool
    is_private_session: bool
    is_restricted: bool
    name: str
    type: str
    volume_percent: int
    supports_volume: bool

class Context(BaseModel):
    type: str
    href: str
    external_urls: dict[str, str]
    uri: str

class SimplyfiedArtist(BaseModel):
    external_urls: str
    href: str
    id: str
    name: str
    type: str
    uri: str

class Album(BaseModel):
      album_type: str
      total_tracks: int
      available_markets: list[str]
      external_urls: dict[str, str]
      href: str
      id: str
      images: list
      name: str
      release_date: str # '1981-12'
      release_date_precision: str #"year", "month", "day"
      restrictions: dict[str, str]
      type: str
      uri: str
      artists: list[SimplyfiedArtist]

class TrackObject(BaseModel):
      album: Album
      artists: list[SimplyfiedArtist]
      available_markets: list[str]
      disc_number: int
      duration_ms: int
      explicit: bool
      external_ids: dict[str, str]
      external_urls: dict[str, str]
      href: str
      id: str
      is_playable: bool
      linked_from: object
      restrictions: dict[str, str]
      name: str
      popularity: int
      preview_url: str
      track_number: int
      type: str
      uri: str
      is_local: bool

class Actions(BaseModel):
    interrupting_playback: bool
    pausing: bool
    resuming: bool
    seeking: bool
    skipping_next: bool
    skipping_prev: bool
    toggling_repeat_context: bool
    toggling_shuffle: bool
    toggling_repeat_track: bool
    transfering_playback: bool

class CurrentlyPlayingResponse(BaseModel): # Might be currently playing stuff only
    device: Device
    repeat_state: str
    shuffle_state: bool
    context: Context
    timestamp: int
    progress_ms: int
    is_playing: bool
    trackObject: TrackObject
    currently_playing_type: str
    actions: Actions
