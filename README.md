# Spotify Playlist Creator

A Python script that creates Spotify playlists from local music files by matching them with tracks on Spotify.

## Features

- Scans a folder for audio files (MP3, WAV, FLAC, M4A)
- Extracts metadata from audio files
- Matches local songs with Spotify tracks
- Creates a new Spotify playlist with the matched tracks
- Handles large music libraries with pagination
- Shows which tracks were not found on Spotify

## Prerequisites

1. Python 3.8 or higher
2. A Spotify Developer account
3. A Spotify Premium account (required to play full tracks)

## Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/spotify-playlist-creator.git
   cd spotify-playlist-creator
   ```

2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your Spotify Developer application:
   - Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
   - Log in with your Spotify account
   - Click "Create App"
   - Fill in the app details and create
   - Note down your Client ID and Client Secret
   - Click on "Edit Settings" and add `http://localhost:8888/callback` to the Redirect URIs

4. Create a `.env` file:
   - Copy the `.env.example` file to `.env`
   - Fill in your Spotify API credentials
   ```
   SPOTIFY_CLIENT_ID=your_client_id_here
   SPOTIFY_CLIENT_SECRET=your_client_secret_here
   SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
   ```

## Usage

1. Run the script:
   ```bash
   python spotify_playlist_creator.py
   ```

2. When prompted, enter the path to your music folder.

3. Enter a name for your playlist (or press Enter to use the folder name).

4. The script will:
   - Scan your music folder for audio files
   - Extract metadata from each file
   - Search for matching tracks on Spotify
   - Create a new playlist with all found tracks
   - Show you which tracks couldn't be found

5. The first time you run the script, it will open a browser window asking you to log in to Spotify and authorize the application.

## Notes

- The script reads ID3 tags from your audio files to search for tracks on Spotify. Make sure your files have proper metadata for best results.
- If a track isn't found, it might be because the metadata is missing or doesn't match Spotify's database.
- You need a Spotify Premium account to play full tracks in the created playlist.

## Troubleshooting

- If you get authentication errors, make sure your `.env` file has the correct credentials and the redirect URI is properly set in your Spotify Developer Dashboard.
- If tracks aren't being found, check that your audio files have proper metadata (title, artist, etc.).
- Make sure you've authorized the application with the correct scopes (playlist-modify-public and/or playlist-modify-private).

## License

This project is licensed under the MIT License - see the LICENSE file for details.
