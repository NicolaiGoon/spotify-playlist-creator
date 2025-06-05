# Spotify Playlist Creator

A Python script that scans a local folder of audio files, extracts metadata, searches for matching tracks on Spotify, and creates a Spotify playlist.

## Features

- Scans a specified folder for various audio file types (MP3, M4A, FLAC, WAV, etc.).
- Extracts metadata (title, artist, album) from audio files using `mutagen`. Falls back to filename if tags are missing.
- Cleans and normalizes extracted metadata for better search accuracy.
- **Greeklish Handling**: Converts Greek characters in metadata to their Latin (Greeklish) equivalents to improve matching for Greek songs.
- **Multi-Stage Spotify Search**: 
    - Employs a staged search approach (high-precision, primary alternatives, fallback with Greeklish and raw queries) to find tracks efficiently.
    - Uses early exits if a high-confidence match is found, reducing API calls.
- **Match Scoring**: Calculates a match score based on title and artist similarity between local metadata and Spotify search results.
- Creates a new Spotify playlist or updates an existing one (if functionality is added).
- Adds successfully matched tracks to the playlist.
- Provides a summary of tracks found and not found.
- **Command-Line Interface**: Supports arguments for folder path, playlist name, playlist privacy (public/private), and a dry-run mode.
- Securely loads Spotify API credentials from a `.env` file.
- Detailed console output including profiling information for API calls and processing time per song.

## Prerequisites

- Python 3.8 or higher
- Pip (Python package installer)
- A Spotify Developer account (to get API credentials)
- A Spotify account (Premium is not strictly required to create playlists or add tracks, but recommended for full playback features).

## Setup

1.  **Clone the Repository** (or download the files):
    ```bash
    git clone https://github.com/yourusername/spotify-playlist-creator.git # Replace with actual URL if available
    cd spotify-playlist-creator
    ```

2.  **Create a Virtual Environment** (recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set Up Spotify API Credentials**:
    *   Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/) and log in.
    *   Click "Create App" (or select an existing one).
    *   Note your `Client ID` and `Client Secret`.
    *   In your app settings on the dashboard, add a **Redirect URI**. For this script, `http://localhost:8888/callback` is a common choice and is often the default Spotipy uses if not overridden.

5.  **Create a `.env` File**:
    In the root directory of the project, create a file named `.env` and add your Spotify API credentials:
    ```env
    SPOTIPY_CLIENT_ID='YOUR_CLIENT_ID'
    SPOTIPY_CLIENT_SECRET='YOUR_CLIENT_SECRET'
    SPOTIPY_REDIRECT_URI='http://localhost:8888/callback' 
    # Ensure this matches one of the Redirect URIs in your Spotify Developer Dashboard app settings.
    ```
    Replace `YOUR_CLIENT_ID` and `YOUR_CLIENT_SECRET` with your actual credentials.

## Usage

The script is run from the command line.

**Basic Command**:
```bash
python spotify_playlist_creator.py "/path/to/your/music folder"
```

**Command-Line Arguments**:

*   `folder_path` (required): The absolute or relative path to the folder containing your music files.
*   `--playlist-name` (optional): The name for the Spotify playlist. If not provided, the script will use the name of the music folder.
    *   Example: `--playlist-name "My Awesome Mix"`
*   `--private` (optional flag): If set, the created playlist will be private. By default, playlists are public.
    *   Example: `--private`
*   `--dry-run` (optional flag): If set, the script will perform all steps (scanning, metadata extraction, Spotify search) but will **not** create any playlist or add any tracks on Spotify. Useful for testing.
    *   Example: `--dry-run`

**Examples**:

1.  Create a public playlist named "80s Rock Hits" from a folder:
    ```bash
    python spotify_playlist_creator.py "D:\Music\80s Rock" --playlist-name "80s Rock Hits"
    ```

2.  Create a private playlist using the folder name, from a folder with spaces in its path:
    ```bash
    python spotify_playlist_creator.py "/Users/me/Music/Chill Vibes" --private
    ```

3.  Perform a dry run to see what tracks would be found:
    ```bash
    python spotify_playlist_creator.py "./My Local Tracks" --dry-run
    ```

Upon first run, your web browser will open, asking you to log in to Spotify and authorize the application to access your account (specifically, to manage playlists).

## Project Structure

-   `spotify_playlist_creator.py`: The main executable script. Handles command-line argument parsing, environment loading, and orchestrates the playlist creation process by calling `SpotifyPlaylistCreator`.
-   `/src`:
    -   `__init__.py`: Makes `src` a Python package.
    -   `spotify_client.py`: Contains the `SpotifyPlaylistCreator` class, which encapsulates all Spotify-related logic: authentication, metadata cleaning, Greeklish conversion, multi-stage track searching, scoring, and playlist manipulation.
    -   `metadata_utils.py`: Provides utility functions for discovering audio files (`get_audio_files`) and extracting/processing metadata from them (`get_song_info` and its helpers).
-   `/tests`:
    -   `__init__.py`: Makes `tests` a Python package.
    -   `test_metadata_utils.py`: Unit tests for the metadata utility functions.
-   `requirements.txt`: Lists project dependencies.
-   `.env`: (You create this) Stores your Spotify API credentials.
-   `README.md`: This file.

## How It Works

1.  **Initialization**: The main script parses command-line arguments and loads environment variables from the `.env` file.
2.  **Audio File Discovery**: `metadata_utils.get_audio_files()` scans the specified `folder_path` recursively for common audio file extensions.
3.  **Metadata Extraction & Processing (for each file)**:
    *   `metadata_utils.get_song_info()` uses the `mutagen` library to read embedded tags (title, artist, album).
    *   If essential tags are missing, the filename (without extension) is used as a fallback for the title.
    *   The `SpotifyPlaylistCreator` class then takes this raw metadata.
    *   `_clean_title()`: Removes common extraneous information from titles (e.g., "(live)", "[remix]").
    *   `_convert_to_greeklish()`: Converts Greek characters in title and artist to their Latin (Greeklish) phonetic equivalents.
4.  **Spotify Track Search (for each song)**:
    *   The `search_spotify_track()` method in `SpotifyPlaylistCreator` performs a multi-stage search:
        *   **Stage 1 (High-Precision)**: Searches using `cleaned_title AND artist`.
        *   **Stage 2 (Primary Alternatives)**: If no high-confidence match from Stage 1, tries `cleaned_title` alone, and `artist` alone.
        *   **Stage 3 (Fallback Searches)**: If still no good match, tries combinations involving Greeklish versions of title/artist, and also broader queries using raw (less processed) title/artist strings.
    *   **API Call Reduction**: If a match with a score above a certain threshold (e.g., 0.85 for Stage 1) is found, subsequent stages for that song are skipped.
    *   **Scoring**: `_calculate_match_score()` compares the cleaned local metadata with Spotify's track title and artist(s) using sequence matching ratios.
5.  **Playlist Creation/Update**: 
    *   If not a dry run, and tracks are found, `create_playlist()` (or a similar method) is called to either create a new public/private playlist.
    *   `add_tracks_to_playlist()` adds the URIs of the found Spotify tracks to this playlist in batches (Spotify API limits 100 tracks per add request).
6.  **Summary**: A report is printed to the console detailing how many tracks were found and which ones were not, along with profiling information.

## Troubleshooting

-   **`ModuleNotFoundError: No module named 'mutagen'` (or similar)**: Ensure you have activated your virtual environment (if using one) and have run `pip install -r requirements.txt`.
-   **Authentication Errors / `spotipy.exceptions.SpotifyOauthError`**: 
    *   Double-check that `SPOTIPY_CLIENT_ID`, `SPOTIPY_CLIENT_SECRET`, and `SPOTIPY_REDIRECT_URI` in your `.env` file are correct.
    *   Ensure the `SPOTIPY_REDIRECT_URI` in your `.env` file exactly matches one of the Redirect URIs you added in your Spotify Developer Dashboard app settings.
    *   Delete the `.cache` file (usually named `.cache-yourusername` or similar) in your project directory and try running the script again to re-authenticate.
-   **Tracks Not Found**: 
    *   Verify that your audio files have accurate embedded metadata (title, artist). The script relies heavily on this.
    *   The song might genuinely not be on Spotify, or its metadata might differ significantly.
-   **Incorrect Scopes**: If you see errors related to permissions, ensure the Spotipy client is initialized with the correct scopes (e.g., `playlist-modify-public`, `playlist-modify-private`). The script currently requests these as needed.

## License

This project is licensed under the MIT License. (If you have a `LICENSE` file, otherwise, you can state this or choose another license).
