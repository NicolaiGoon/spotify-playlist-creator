import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Add the src directory to the Python path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / 'src'))

from metadata_utils import (
    get_audio_files, 
    _normalize_tag_value,
    _get_tag_value,
    _extract_fields_from_tags,
    get_song_info,
    AUDIO_EXTENSIONS
)

class TestMetadataUtils(unittest.TestCase):

    def test_normalize_tag_value(self):
        self.assertEqual(_normalize_tag_value(['Test Value']), 'Test Value')
        self.assertEqual(_normalize_tag_value('Direct Value'), 'Direct Value')
        self.assertIsNone(_normalize_tag_value([]))
        self.assertEqual(_normalize_tag_value([123]), '123')

    def test_get_tag_value(self):
        mock_tags_simple = {'title': ['Song Title']}
        self.assertEqual(_get_tag_value(mock_tags_simple, ['title', 'TIT2']), 'Song Title')

        mock_tags_alt = {'TIT2': ['Another Title']}
        self.assertEqual(_get_tag_value(mock_tags_alt, ['title', 'TIT2']), 'Another Title')

        mock_tags_empty_list = {'title': []}
        self.assertIsNone(_get_tag_value(mock_tags_empty_list, ['title']))

        mock_tags_whitespace = {'artist': ['  Artist Name  ']}
        self.assertEqual(_get_tag_value(mock_tags_whitespace, ['artist']), 'Artist Name')

        mock_tags_missing = {'album': ['Album']}
        self.assertIsNone(_get_tag_value(mock_tags_missing, ['title']))

    def test_extract_fields_from_tags(self):
        mock_tags = {
            'title': ['Awesome Song'],
            'TPE1': ['Great Artist'],
            '\xa9alb': ['Cool Album']
        }
        expected_data = {
            'title': 'Awesome Song',
            'artist': 'Great Artist',
            'album': 'Cool Album'
        }
        self.assertEqual(_extract_fields_from_tags(mock_tags), expected_data)

        mock_tags_partial = {'TIT2': ['Partial Title']}
        expected_partial = {'title': 'Partial Title'}
        self.assertEqual(_extract_fields_from_tags(mock_tags_partial), expected_partial)

        self.assertEqual(_extract_fields_from_tags({}), {})

    @patch('metadata_utils.MutagenFile')
    def test_get_song_info_success_standard_tags(self, mock_mutagen_file):
        mock_audio = MagicMock()
        mock_audio.tags = {
            'title': ['My Song'],
            'artist': ['My Artist'],
            'album': ['My Album']
        }
        mock_mutagen_file.return_value = mock_audio

        file_path = Path('dummy/path/song.mp3')
        expected_info = {
            'title': 'My Song',
            'artist': 'My Artist',
            'album': 'My Album',
            'file_path': str(file_path)
        }
        self.assertEqual(get_song_info(file_path), expected_info)

    @patch('metadata_utils.MutagenFile')
    def test_get_song_info_success_alternative_tags(self, mock_mutagen_file):
        mock_audio = MagicMock()
        mock_audio.tags = {
            'TIT2': ['Alt Song Title'], # Title
            'TPE1': ['Alt Artist'],   # Artist
            'TALB': ['Alt Album']     # Album
        }
        mock_mutagen_file.return_value = mock_audio
        file_path = Path('dummy/path/song_alt.flac')
        expected_info = {
            'title': 'Alt Song Title',
            'artist': 'Alt Artist',
            'album': 'Alt Album',
            'file_path': str(file_path)
        }
        self.assertEqual(get_song_info(file_path), expected_info)

    @patch('metadata_utils.MutagenFile')
    def test_get_song_info_no_tags(self, mock_mutagen_file):
        mock_audio = MagicMock()
        mock_audio.tags = {}
        mock_mutagen_file.return_value = mock_audio
        file_path = Path('dummy/path/no_tags_song.wav')
        expected_info = {
            'title': 'no_tags_song', # Should use filename stem
            'artist': '',
            'album': '',
            'file_path': str(file_path)
        }
        self.assertEqual(get_song_info(file_path), expected_info)

    @patch('metadata_utils.MutagenFile')
    def test_get_song_info_mutagen_exception(self, mock_mutagen_file):
        mock_mutagen_file.side_effect = Exception('Mutagen failed to load')
        file_path = Path('dummy/path/corrupted_file.mp3')
        # Expect default values, including filename stem as title
        expected_info = {
            'title': 'corrupted_file',
            'artist': '',
            'album': '',
            'file_path': str(file_path)
        }
        # We also expect an error to be printed, but we won't capture stdout here for simplicity
        self.assertEqual(get_song_info(file_path), expected_info)

    @patch('metadata_utils.MutagenFile')
    def test_get_song_info_empty_tag_values(self, mock_mutagen_file):
        mock_audio = MagicMock()
        mock_audio.tags = {
            'title': ['   '], # Whitespace only
            'artist': [],    # Empty list
            'album': ['Actual Album']
        }
        mock_mutagen_file.return_value = mock_audio
        file_path = Path('dummy/path/empty_tags.m4a')
        expected_info = {
            'title': 'empty_tags', # Fallback to filename stem
            'artist': '',
            'album': 'Actual Album',
            'file_path': str(file_path)
        }
        self.assertEqual(get_song_info(file_path), expected_info)

    # Test for get_audio_files requires actual file system interaction or more complex mocking
    # For now, we'll skip direct testing of get_audio_files in this unit test suite
    # to keep it focused on metadata extraction logic and avoid file system dependencies.

if __name__ == '__main__':
    unittest.main()
