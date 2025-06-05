from pathlib import Path
from mutagen import File as MutagenFile

# Common audio file extensions to look for
AUDIO_EXTENSIONS = {
    # Common formats
    '.mp3', '.m4a', '.m4b', '.m4p', '.mp4', '.flac', 
    # Less common but still widely used
    '.ogg', '.oga', '.opus', '.wav', '.wave', '.aif', 
    '.aiff', '.aifc', '.wma', '.asf', '.ape', '.mpc', 
    '.mp+', '.wv', '.tta'
}

def get_audio_files(folder_path):
    """Get list of audio files from the specified folder."""
    return [f for f in Path(folder_path).rglob('*') if f.suffix.lower() in AUDIO_EXTENSIONS]

def _normalize_tag_value(raw_value):
    """Normalize a raw tag value (list or string) to a string, or None if unusable."""
    if isinstance(raw_value, list):
        if raw_value:  # List is not empty
            return str(raw_value[0])
        else:  # Empty list
            return None  # Signal to skip this tag occurrence
    return str(raw_value) # Assume it can be converted to string

def _get_tag_value(audio_tags, tag_names_list):
    """Helper to retrieve and clean a specific tag value from audio metadata."""
    for tag in tag_names_list:
        try:
            if tag in audio_tags:
                raw_value = audio_tags[tag]
                normalized_value = _normalize_tag_value(raw_value)

                if normalized_value is None:
                    continue # Value was unusable (e.g., empty list), try next tag
                
                cleaned_value = normalized_value.strip()
                if cleaned_value:
                    return cleaned_value
        except (KeyError, IndexError, AttributeError):
            # Error accessing or processing this specific tag, try next one
            continue
    return None

def _extract_fields_from_tags(audio_tags):
    """Helper to extract title, artist, album from loaded audio tags using _get_tag_value."""
    extracted_data = {}
    # Assumes audio_tags is a valid object from Mutagen, checked by caller.
    tag_definitions = {
        'title': ['title', 'TIT2', '\xa9nam'],
        'artist': ['artist', 'TPE1', '\xa9ART'],
        'album': ['album', 'TALB', '\xa9alb']
    }
    for field, tag_names_list in tag_definitions.items():
        tag_value = _get_tag_value(audio_tags, tag_names_list)
        if tag_value:
            extracted_data[field] = tag_value
    return extracted_data

def get_song_info(file_path):
    """Extract song information from audio file metadata."""
    file_path = Path(file_path)
    file_path_str = str(file_path)
    
    # Default values
    metadata = {
        'title': file_path.stem,
        'artist': '',
        'album': '',
        'file_path': file_path_str
    }
    
    try:
        # Try to load the file with Mutagen
        audio = MutagenFile(file_path_str, easy=True)
        
        if audio is not None and hasattr(audio, 'tags') and audio.tags is not None:
            # audio.tags is confirmed to be usable here
            extracted_tag_data = _extract_fields_from_tags(audio.tags)
            metadata.update(extracted_tag_data)
        
    except Exception as e:
        print(f"Error reading metadata from {file_path}: {e}")
    
    return metadata
