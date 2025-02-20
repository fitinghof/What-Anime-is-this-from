from pydantic import BaseModel, Field
from typing import Optional, List, Dict

class Device(BaseModel):
    id: Optional[str]
    is_active: Optional[bool]
    is_private_session: Optional[bool]
    is_restricted: Optional[bool]
    name: Optional[str]
    type: Optional[str]
    volume_percent: Optional[int]
    supports_volume: Optional[bool]

class Context(BaseModel):
    type: Optional[str]
    href: Optional[str]
    external_urls: Optional[Dict[str, str]]
    uri: Optional[str]

class SimplifiedArtist(BaseModel):
    external_urls: Optional[Dict[str, str]]
    href: Optional[str]
    id: Optional[str]
    name: Optional[str]
    type: Optional[str]
    uri: Optional[str]

class Image(BaseModel):
    url: str
    height: int
    width: int

class Album(BaseModel):
    album_type: Optional[str]
    total_tracks: Optional[int]
    available_markets: Optional[list[str]]
    external_urls: Optional[Dict[str, str]]
    href: Optional[str]
    id: Optional[str]
    images: list[Image]
    name: str
    release_date: str  # '1981-12'
    release_date_precision: str  # "year", "month", "day"
    # restrictions: Optional[dict[str, str]]
    type: str
    uri: str
    artists: list[SimplifiedArtist]

class TrackObject(BaseModel):
    album: Album
    artists: list[SimplifiedArtist]
    available_markets: list[str]
    disc_number: int
    duration_ms: int
    explicit: bool
    external_ids: Dict[str, str]
    external_urls: Dict[str, str]
    href: str
    id: str
    is_playable: Optional[bool] = None
    linked_from: Optional[Dict[str, str]] = None
    restrictions: Optional[Dict[str, str]] = None
    name: str
    popularity: int
    preview_url: Optional[str]
    track_number: int
    type: str
    uri: str
    is_local: bool

class Actions(BaseModel):
    interrupting_playback: Optional[bool] = None
    pausing: Optional[bool] = None
    resuming: Optional[bool] = None
    seeking: Optional[bool] = None
    skipping_next: Optional[bool] = None
    skipping_prev: Optional[bool] = None
    toggling_repeat_context: Optional[bool] = None
    toggling_shuffle: Optional[bool] = None
    toggling_repeat_track: Optional[bool] = None
    transfering_playback: Optional[bool] = None

class CurrentlyPlayingResponse(BaseModel):
    device: Optional[Device] = None
    repeat_state: Optional[str] = None
    shuffle_state: Optional[bool] = None
    context: Optional[Context] = None
    timestamp: Optional[int] = None
    progress_ms: Optional[int] = None
    is_playing: bool = None
    item: Optional[TrackObject] = None
    currently_playing_type: Optional[str] = None
    actions: Optional[Actions] = None
