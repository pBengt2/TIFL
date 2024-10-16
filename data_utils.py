from datetime import date, timedelta

import file_utils

_SETTINGS_DATA = r"Data/settings.json"
_JSON_SAVED_DATA = r"Data/saved.json"  # 'book_dict' { 'filename' { 'index', 'total_chars', 'saved_chapter', 'saved_page' }: , vocab_list: [vocab], last_open_file: filename, last_date: date_string
_VOCAB_USES_DATA = r"Data/vocab_uses.json"  # 'books' : [book], 'vocab' : { filename : [index] }
_VOCAB_SENTENCES_DATA = r"Data/vocab_sentences.json"  # vocab : [sentences]
_VOCAB_QUIZ_DATA = r"Data/vocab_quiz.json"  # vocab : { 'definitions', 'verb_type' }
_VOCAB_STATS_DATA = r"Data/vocab_stats.json"  # 'vocab': { 'correct', 'incorrect', 'in_a_row' }
_VOCAB_RUSH_DATA = r"Data/vocab_rush.json"  # vocab: { 'correct', 'incorrect', 'in_a_row', 'last_date' }


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class JsonSingleton(metaclass=Singleton):
    def __init__(self):
        self.json_file = None
        self._data = None

    def get_data(self):
        if self._data is None:
            self._data = file_utils.load_json(self.json_file)
        return self._data

    def save_data(self, data):
        # TODO: saved_data is not always in sync with saved data. Subclasses should handle their cases...
        file_utils.save_json_data(self.json_file, data)


class MainSettings(JsonSingleton):
    def __init__(self):
        super().__init__()
        self.json_file = _SETTINGS_DATA

    def get_data(self):
        if self._data is None:
            self._data = file_utils.load_json(self.json_file)
            if self._data == {}:
                self._data['window_width'] = 1024
                self._data['window_height'] = 1024
                self._data['view_dual_panel_manga'] = True
        return self._data

    def get_window_width(self):
        return file_utils.read_key(self.get_data(), "window_width", 1024)

    def get_window_height(self):
        return file_utils.read_key(self.get_data(), "window_height", 1024)

    def view_dual_panel_manga(self):
        # TODO: This can be automatically handled based on window dimensions and image aspect ratio.
        return file_utils.read_key(self.get_data(), "view_dual_panel_manga", True)

    def get_reading_min_height(self):
        return min(max(320, int(self.get_window_height() * .75)), 1100)  # TODO: arbitrary

    def get_text_field_buffer_room(self):
        chars_per_row = int(self.get_reading_min_width() / 30)
        return chars_per_row + 3  # TODO: Arbitrary (before finishing second to last line...)

    def get_text_field_max_text(self):
        chars_per_row = int(self.get_reading_min_width() / 30)  # TODO: just an estimate. Should check text size...
        num_rows = int(self.get_reading_min_height() / 65)
        return chars_per_row * num_rows

    @staticmethod
    def get_manga_viewer_width():
        return 900  # TODO: arbitrary

    @staticmethod
    def get_manga_viewer_height():
        return 1333  # TODO: arbitrary

    @staticmethod
    def get_reading_input_min_height():
        return 128  # TODO: arbitrary

    @staticmethod
    def get_reading_min_width():
        return 900  # TODO: arbitrary

    @staticmethod
    def get_reading_definitions_width():
        return 512  # TODO: arbitrary


class VocabUses(JsonSingleton):
    def __init__(self):
        super().__init__()
        self.json_file = _VOCAB_USES_DATA


class VocabSentences(JsonSingleton):
    def __init__(self):
        super().__init__()
        self.json_file = _VOCAB_SENTENCES_DATA

    def get_sentences(self, vocab_word):
        # TODO: would like to be able to update sentences from here...
        return file_utils.read_key(self.get_data(), vocab_word, [])


class VocabQuizData(JsonSingleton):
    def __init__(self):
        super().__init__()
        self.json_file = _VOCAB_QUIZ_DATA


class VocabStatsData(JsonSingleton):
    def __init__(self):
        super().__init__()
        self.json_file = _VOCAB_STATS_DATA


class VocabRushData(JsonSingleton):
    def __init__(self):
        super().__init__()
        self.json_file = _VOCAB_RUSH_DATA


class SavedData(JsonSingleton):
    def __init__(self):
        super().__init__()
        self.json_file = _JSON_SAVED_DATA
        self._book_dict = None
        self.vocab_list = None

    def get_book_dict(self):
        if self._book_dict is None:
            self._book_dict = file_utils.read_key(self.get_data(), "book_dict", {})
        return self._book_dict

    def get_vocab_list(self):
        if self.vocab_list is None:
            self.vocab_list = file_utils.read_key(self.get_data(), "vocab_list", {})
        return self.vocab_list

    def get_book_index(self, book_title):
        book_info = file_utils.read_key(self.get_book_dict(), book_title, {})
        return max(file_utils.read_key(book_info, "index", 0), 0)

    def get_book_total_characters(self, book_title):
        book_info = file_utils.read_key(self.get_book_dict(), book_title, {})
        return file_utils.read_key(book_info, "total_chars", 0)

    def get_manga_chapter(self, manga_title):
        book_info = file_utils.read_key(self.get_book_dict(), manga_title, {})
        return file_utils.read_key(book_info, "saved_chapter", 0)

    def get_manga_page(self, manga_title):
        book_info = file_utils.read_key(self.get_book_dict(), manga_title, {})
        return file_utils.read_key(book_info, "saved_page", 0)

    def get_last_open_file(self):
        return file_utils.read_key(self.get_data(), "last_open_file", file_utils.DEFAULT_TXT_FILE)

    def get_saved_date(self):
        return file_utils.read_key(self.get_data(), "last_date", str(date.today() - timedelta(days=1)))

    def was_manga_open(self):
        # TODO: Manga should be it's own tab...
        return file_utils.read_key(self.get_data(), "last_file_manga", False)
