"""Music catalog tools for the Chinook store."""

from langchain_core.tools import tool

from db import run_query


@tool
def get_albums_by_artist(artist: str) -> str:
    """Retrieve albums by a given artist name (partial match allowed)."""
    safe = artist.replace("'", "''")
    return run_query(
        f"""
        SELECT Album.Title, Artist.Name
        FROM Album
        JOIN Artist ON Album.ArtistId = Artist.ArtistId
        WHERE Artist.Name LIKE '%{safe}%'
        ORDER BY Album.Title
        LIMIT 20;
        """
    )


@tool
def get_tracks_by_artist(artist: str) -> str:
    """Retrieve tracks (songs) by a given artist (partial match allowed)."""
    safe = artist.replace("'", "''")
    return run_query(
        f"""
        SELECT Track.Name AS Track, Album.Title AS Album, Artist.Name AS Artist
        FROM Track
        JOIN Album ON Track.AlbumId = Album.AlbumId
        JOIN Artist ON Album.ArtistId = Artist.ArtistId
        WHERE Artist.Name LIKE '%{safe}%'
        ORDER BY Track.Name
        LIMIT 25;
        """
    )


@tool
def get_songs_by_genre(genre: str) -> str:
    """Fetch songs that match a specific genre (partial match allowed)."""
    safe = genre.replace("'", "''")
    return run_query(
        f"""
        SELECT Track.Name AS Track, Genre.Name AS Genre, Artist.Name AS Artist
        FROM Track
        JOIN Genre ON Track.GenreId = Genre.GenreId
        JOIN Album ON Track.AlbumId = Album.AlbumId
        JOIN Artist ON Album.ArtistId = Artist.ArtistId
        WHERE Genre.Name LIKE '%{safe}%'
        ORDER BY Track.Name
        LIMIT 25;
        """
    )


@tool
def check_for_songs(song_title: str) -> str:
    """Check if a song exists by its name (partial match allowed)."""
    safe = song_title.replace("'", "''")
    return run_query(
        f"""
        SELECT Track.Name AS Track, Artist.Name AS Artist, Album.Title AS Album
        FROM Track
        JOIN Album ON Track.AlbumId = Album.AlbumId
        JOIN Artist ON Album.ArtistId = Artist.ArtistId
        WHERE Track.Name LIKE '%{safe}%'
        ORDER BY Track.Name
        LIMIT 20;
        """
    )


MUSIC_TOOLS = [
    get_albums_by_artist,
    get_tracks_by_artist,
    get_songs_by_genre,
    check_for_songs,
]
