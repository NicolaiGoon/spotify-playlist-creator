import os
import argparse
from dotenv import load_dotenv
from src.spotify_client import SpotifyClient
from src.playlist_creator import PlaylistCreator

def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description='Create a Spotify playlist from a folder of audio files.')
    parser.add_argument('folder_path', type=str, help='The path to the folder containing audio files.')
    parser.add_argument('--name', type=str, help='The name of the playlist. Defaults to the folder name.')
    parser.add_argument('--private', action='store_true', help='Make the playlist private.')
    parser.add_argument('--dry-run', action='store_true', help='Scan files and search for tracks without creating a playlist.')
    
    args = parser.parse_args()

    folder_path = args.folder_path
    playlist_name = args.name
    public = not args.private
    dry_run = args.dry_run

    if not os.path.isdir(folder_path):
        print(f"Error: Directory not found at '{folder_path}'")
        return

    try:
        # Initialize the Spotify client
        spotify_client = SpotifyClient()
        
        # Initialize the playlist creator
        playlist_creator = PlaylistCreator(spotify_client)
        
        # Create the playlist from the folder
        playlist_creator.create_playlist_from_folder(
            folder_path=folder_path,
            playlist_name=playlist_name,
            public=public,
            dry_run=dry_run
        )
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    main()
