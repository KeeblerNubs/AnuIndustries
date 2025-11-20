"""Utilities for downloading Apple Music content using gamdl.

This script demonstrates how to set up the gamdl downloaders and fetch
audio or video assets from Apple Music. It expects a Netscape-format
cookies.txt file that includes an authenticated Apple Music session.
"""

import asyncio
from pathlib import Path


def validate_cookies_path(cookies_path: str | Path = "cookies.txt") -> Path:
    """Ensure the Netscape cookies file exists.

    Raises a :class:`FileNotFoundError` with a helpful message when the cookies
    file cannot be found. This helper is used by the script and tests to avoid
    launching real downloads when required inputs are missing.
    """

    path = Path(cookies_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(
            f"Missing Apple Music cookies file at '{path}'. "
            "Create a Netscape-format cookies.txt export before running downloads."
        )

    return path


async def main() -> None:
    """Download content from Apple Music using the gamdl library.

    This function wires together the gamdl API clients, interfaces, and
    downloader implementations to download a single piece of content
    identified by its Apple Music URL. Update the URL passed to
    ``downloader.get_url_info`` to target a different track or video.
    """

    from gamdl.api import AppleMusicApi, ItunesApi
    from gamdl.downloader import (
        AppleMusicBaseDownloader,
        AppleMusicDownloader,
        AppleMusicMusicVideoDownloader,
        AppleMusicSongDownloader,
        AppleMusicUploadedVideoDownloader,
    )
    from gamdl.interface import (
        AppleMusicInterface,
        AppleMusicMusicVideoInterface,
        AppleMusicSongInterface,
        AppleMusicUploadedVideoInterface,
    )

    # Initialize APIs
    cookies_path = validate_cookies_path()

    apple_music_api = AppleMusicApi.from_netscape_cookies(cookies_path=str(cookies_path))
    await apple_music_api.setup()

    itunes_api = ItunesApi(
        apple_music_api.storefront,
        apple_music_api.language,
    )
    itunes_api.setup()

    # Initialize interfaces
    interface = AppleMusicInterface(apple_music_api, itunes_api)
    song_interface = AppleMusicSongInterface(interface)
    music_video_interface = AppleMusicMusicVideoInterface(interface)
    uploaded_video_interface = AppleMusicUploadedVideoInterface(interface)

    # Initialize base downloader
    base_downloader = AppleMusicBaseDownloader()
    base_downloader.setup()

    # Initialize specialized downloaders
    song_downloader = AppleMusicSongDownloader(
        base_downloader=base_downloader,
        interface=song_interface,
    )
    music_video_downloader = AppleMusicMusicVideoDownloader(
        base_downloader=base_downloader,
        interface=music_video_interface,
    )
    uploaded_video_downloader = AppleMusicUploadedVideoDownloader(
        base_downloader=base_downloader,
        interface=uploaded_video_interface,
    )

    # Create main downloader
    downloader = AppleMusicDownloader(
        interface=interface,
        base_downloader=base_downloader,
        song_downloader=song_downloader,
        music_video_downloader=music_video_downloader,
        uploaded_video_downloader=uploaded_video_downloader,
    )

    # Download a song
    url_info = downloader.get_url_info(
        "https://music.apple.com/us/album/never-gonna-give-you-up-2022-remaster/1624945511?i=1624945512"
    )

    if url_info:
        download_queue = await downloader.get_download_queue(url_info)
        if download_queue:
            for download_item in download_queue:
                await downloader.download(download_item)


if __name__ == "__main__":
    asyncio.run(main())
