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
        self._data = data
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
                self._data['reset_mode'] = False
        return self._data

    def get_reset_mode(self):
        return file_utils.read_key(self.get_data(), "reset_mode", False)

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
        self._vocab_list = None

    def update_saved_data(self, current_txt_file=None, current_sentence_index=0, current_book_character_count=0, current_manga_directory=None, manga_chapter=0, manga_page=0, manga_mode=False):
        if current_txt_file is not None:
            self._book_dict[current_txt_file.replace("\\", "/")] = {
                "index": current_sentence_index,
                "total_chars": current_book_character_count
            }

        if current_manga_directory:
            self._book_dict[current_manga_directory] = {
                "saved_chapter": manga_chapter,
                "saved_page": manga_page
            }

        # TODO: can't remember why this code was added in the first place...
        #   Commenting out for now... remove if no issues arise.
        """
        pruned_book_dict = updated_book_dict.copy()
        key_list = [k for k in pruned_book_dict.keys()]
        for key in key_list:
            if key is not None and key.startswith("TEMP"):
                pruned_book_dict.pop(key)
        """

        last_file = current_txt_file
        if manga_mode:
            last_file = current_manga_directory

        data = {
            "book_dict": self._book_dict,
            "vocab_list": self._vocab_list,
            "last_open_file": last_file,
            "last_file_manga": manga_mode,
            "last_manga_directory": current_manga_directory,
            "last_date": str(date.today())
        }
        self.save_data(data)

    def save_data(self, data):
        self._data = data
        self._book_dict = file_utils.read_key(self.get_data(), "book_dict", {})
        self._vocab_list = file_utils.read_key(self.get_data(), "vocab_list", {})
        file_utils.save_json_data(self.json_file, data)

    def add_vocab(self, word):
        if len(word) > 0:
            if word not in self._vocab_list:
                self._vocab_list.append(word)
                self.update_saved_data()
                return True
        return False

    def remove_vocab(self, word):
        try:
            if len(word) > 0:
                self._vocab_list.remove(word)
                return True
        except ValueError:
            return False

    def get_book_dict(self):
        if self._book_dict is None:
            self._book_dict = file_utils.read_key(self.get_data(), "book_dict", {})
        return self._book_dict

    def get_vocab_list(self):
        if self._vocab_list is None:
            self._vocab_list = file_utils.read_key(self.get_data(), "vocab_list", {})
            # random.shuffle(self.vocab_list)
        return self._vocab_list

    def get_book_index(self, book_title):
        book_info = file_utils.read_key(self.get_book_dict(), book_title, {})
        return max(file_utils.read_key(book_info, "index", 0), 0)

    def get_book_total_characters(self, book_title):
        book_info = file_utils.read_key(self.get_book_dict(), book_title, {})
        return file_utils.read_key(book_info, "total_chars", 0)

    def get_book_read_status(self, filename):
        book_index = self.get_book_index(filename)
        book_total_chars = self.get_book_total_characters(filename)

        if book_index == 0:
            return 1
        elif book_index >= book_total_chars - 1:
            return 2
        else:
            return 0

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
        return file_utils.read_key(self.get_data(), "last_file_manga", False)

    def get_last_manga_directory(self):
        return file_utils.read_key(self.get_data(), "last_manga_directory", False)
