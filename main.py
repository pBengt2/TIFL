from PySide6.QtWidgets import QApplication, QWidget, QTextEdit, QGridLayout, QPushButton, QInputDialog, QLabel, QTabWidget, QHeaderView
from PySide6.QtGui import QTextCursor, Qt, QPixmap
from datetime import date, timedelta
import sys
import random
import os

import data_utils
import file_utils
import jp_utils
import pyside_utils
import vocab_utils


# TODO: High Priority
# - Trying to restore manga page / chapter / etc from file is a complete mess.
#       - Possibly walk the directory until hitting desired file to find chapter + page
#       - Possibly store chapter + page number...
#       - Possibly standardize the Manga directory...
# - GUI should let you know that it's downloading NHK news on launch (currently doesn't launch until dl finished).

# TODO: Mid Priority
# - Should add version numbers to json data.
# - Separate Manga reader from txt reader...

# TODO: Low Priority
# - (Minor feature): Right click to copy text.
# - (feature) 'Free-type'/'playground' tab.
# - (setting) Window resolution
# - (feature/setting) Manga reader settings
# - reverse lookup (ie, english -> japanese).

# TODO: Settings
# - Window size

# TODO: Nice to have
# - Dynamic UI (ie, drag for sizes).

# Future work
# - Support for other languages (IE, generalize language functions, not adding 1 at a time).
# - automate making exe.
#       pyinstaller --paths venv\lib\site-packages main.py
#       - Manually had to copy venv/lib/site-packages/unidic/DicDir...
#       - Manually had to create 'News' and 'LN' folder...
#       - Manually had to create 'Data/saved.json'
#       - KeyError: 'LN/text_book.txt'
#
# - Stats improvements:
#   - Can store background stats on how often clicked ctrl during reading (help find words that need studying)
#   - Can store how often kanji are entered WITHOUT looking up definition (help removed from studying)
#
# - 'edit text file' / 'refresh text file' in order to fix manga text panel ordering issues
# - GUI + automated epub import.


DEFAULT_BLACK_IMG = r"black.png"  # Dummy image for consistent page layout.

MANGA_VIEWER_DUAL_PANEL_MODE = True  # TODO: Settings panel
MANGA_VIEWER_WIDTH = 900  # 540  # 900  # 1800  # TODO: Settings panel
MANGA_VIEWER_HEIGHT = 1333  # 800  # 1333  # 2000  # TODO: Settings panel

WINDOW_SIZE = 2  # TODO: Settings panel
if WINDOW_SIZE == 0:
    TEXT_FIELD_MAX_TEXT = 80
    TEXT_FIELD_BUFFER_ROOM = 20
    READING_LAYOUT_ROW_TEXT_MIN_HEIGHT = 320
    READING_LAYOUT_ROW_INPUT_MIN_HEIGHT = 128
    READING_LAYOUT_COL_ZERO_MIN_WIDTH = 900
    READING_LAYOUT_COL_ONE_MIN_WIDTH = 512
elif WINDOW_SIZE == 1:
    TEXT_FIELD_MAX_TEXT = 150
    TEXT_FIELD_BUFFER_ROOM = 30
    READING_LAYOUT_ROW_TEXT_MIN_HEIGHT = 550
    READING_LAYOUT_ROW_INPUT_MIN_HEIGHT = 128
    READING_LAYOUT_COL_ZERO_MIN_WIDTH = 1024
    READING_LAYOUT_COL_ONE_MIN_WIDTH = 512
elif WINDOW_SIZE == 2:
    TEXT_FIELD_MAX_TEXT = 276
    TEXT_FIELD_BUFFER_ROOM = 30
    READING_LAYOUT_ROW_TEXT_MIN_HEIGHT = 1100
    READING_LAYOUT_ROW_INPUT_MIN_HEIGHT = 128
    READING_LAYOUT_COL_ZERO_MIN_WIDTH = 900
    READING_LAYOUT_COL_ONE_MIN_WIDTH = 512


class MainGui(pyside_utils.VampaJpMainWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Data
        self.saved_data = data_utils.SavedData()
        self.data_stale = False
        self.vocab_stats = data_utils.VocabStatsData().get_data()
        self.vocab_rush_data = vocab_utils.VocabRushData(load=False)

        # Reading / typing
        self.buffer_index = 0
        self.text_buffer = ""
        self.text_field_i1 = 0
        self.text_field_max_text = TEXT_FIELD_MAX_TEXT
        self.text_field_buffer_room = TEXT_FIELD_BUFFER_ROOM
        self.previous_selected_text = ""
        self.current_showing_word = ""
        self.selection_size = 0  # Only relevant for keyboard hotkeys
        self.selection_size_previous_buffer_index = self.buffer_index  # Used to reset selection_size
        self.show_english_definitions = False

        # File breadcrumbs
        self.previous_files_stack = []
        self.file_stack_index = 0

        # Misc / unsorted
        self.auto_word_select = False
        self.vocab_drill_window = None
        self.vocab_list_filter = None

        # Manga
        self.manga_mode = False
        self.manga_chapter = 0
        self.manga_page = 0
        self.manga_page_right_panel = 0
        self.total_manga_chapters = 0
        self.total_manga_pages = 0

        # GUI...
        self.text_field = pyside_utils.NoScrollTextEdit(self)
        self.input_line = pyside_utils.InputLineEdit(self)
        self.definition_field = QTextEdit(self)
        self.bottom_left_text = QLabel(self)
        if MANGA_VIEWER_DUAL_PANEL_MODE:
            self.reading_img_lbl_left = pyside_utils.ClickableLabel(self, self.left_img_clicked, MANGA_VIEWER_WIDTH, MANGA_VIEWER_HEIGHT)
            self.reading_img_lbl_right = pyside_utils.ClickableLabel(self, self.right_img_clicked, MANGA_VIEWER_WIDTH, MANGA_VIEWER_HEIGHT)
        else:
            self.reading_img_lbl_left = pyside_utils.ClickableLabel(self, self.left_img_clicked, MANGA_VIEWER_WIDTH * 2, MANGA_VIEWER_HEIGHT)

        self.main_layout = QGridLayout(self)
        self.tabs = QTabWidget(self)
        self.reading_tab = QWidget(self)
        self.reading_layout = QGridLayout(self.reading_tab)

        self.vocab_tab = QWidget(self)
        self.vocab_layout = QGridLayout(self.vocab_tab)
        self.btn_save_vocab = QPushButton(self)
        self.btn_set_location = QPushButton(self)
        self.button_layout = QGridLayout(self)
        self.btn_add_vocab = QPushButton(self)
        self.btn_remove_vocab = QPushButton(self)
        self.btn_vocab_drill = QPushButton(self)
        self.btn_vocab_rush = QPushButton(self)
        self.btn_conj_rush = QPushButton(self)
        self.vocab_button_layout = QGridLayout(self)
        self.vocab_model = pyside_utils.VocabTableModel([])
        self.vocab_table = pyside_utils.VocabTableView(vocab_model=self.vocab_model, parent=self)
        self.vocab_definition_field = QTextEdit(self)
        self.vocab_input_line = pyside_utils.InputLineEdit(self)

        self.news_tab = QWidget(self)
        self.news_layout = QGridLayout(self.news_tab)
        self.news_field = pyside_utils.MyListWidget(parent=self, saved_data=self.saved_data, directory_prefix=r"News/")

        self.books_tab = QWidget(self)
        self.books_layout = QGridLayout(self.books_tab)
        self.books_field = pyside_utils.MyListWidget(parent=self, saved_data=self.saved_data, directory_prefix=r"LN/")

        self.manga_tab = QWidget(self)
        self.manga_layout = QGridLayout(self.manga_tab)
        self.manga_field = pyside_utils.MyListWidget(parent=self, saved_data=self.saved_data, directory_prefix=r"Manga/", file_type="dir")

        self.log_tab = QWidget(self)
        self.log_layout = QGridLayout(self.log_tab)
        self.log_field = QTextEdit(self)

        self.settings_tab = QWidget(self)
        self.settings_layout = QGridLayout(self.settings_tab)

        # Current state...
        self.current_txt_file = None
        self.current_manga_directory = None

        self.vocab_list = []  # TODO: delete
        self.vocab_sentences = {}  # TODO: delete

        self._setup_helper()

        self.vocab_table.default_hide_columns()
        self.refresh_vocab_table()
        self.refresh_text_display()
        self.input_line.setFocus()

        self.post_load()

    """************************************** UI Setup **************************************"""
    def _setup_reading_tab(self):
        self.reading_tab.setLayout(self.reading_layout)

        self.btn_save_vocab.setText("Add Vocab")
        self.btn_save_vocab.clicked.connect(self.save_vocab_clicked)

        self.btn_set_location.setText("Set Location")
        self.btn_set_location.clicked.connect(self.set_location_clicked)
        cur_row = 0
        if MANGA_VIEWER_DUAL_PANEL_MODE:
            self.reading_layout.addWidget(self.reading_img_lbl_left, cur_row, 0)
            self.reading_layout.addWidget(self.reading_img_lbl_right, cur_row, 1)
        else:
            self.reading_layout.addWidget(self.reading_img_lbl_left, cur_row, 0, 1, 2, alignment=Qt.AlignmentFlag.AlignCenter)
        cur_row += 1
        self.button_layout.addWidget(self.btn_save_vocab, cur_row, 0)
        self.button_layout.addWidget(self.btn_set_location, cur_row, 1)
        self.reading_layout.addWidget(self.text_field, cur_row, 0)
        self.reading_layout.addWidget(self.definition_field, cur_row, 1)
        cur_row += 1
        self.reading_layout.addWidget(self.input_line, cur_row, 0)
        self.reading_layout.addLayout(self.button_layout, cur_row, 1)
        cur_row += 1
        self.reading_layout.addWidget(self.bottom_left_text, cur_row, 0)

        self.reading_layout.setRowMinimumHeight(0, 0)
        self.reading_layout.setRowMinimumHeight(1, READING_LAYOUT_ROW_TEXT_MIN_HEIGHT)
        self.reading_layout.setRowMinimumHeight(2, READING_LAYOUT_ROW_INPUT_MIN_HEIGHT)
        self.reading_layout.setColumnMinimumWidth(0, READING_LAYOUT_COL_ZERO_MIN_WIDTH)
        self.reading_layout.setColumnMinimumWidth(1, READING_LAYOUT_COL_ONE_MIN_WIDTH)
        self.reading_layout.setColumnStretch(0, 1)
        self.reading_layout.setColumnStretch(1, 0)
        self.reading_layout.setColumnStretch(2, 0)
        self.reading_layout.setRowStretch(0, 1)
        self.reading_layout.setRowStretch(1, 1)
        self.reading_layout.setRowStretch(2, 0)

        self._refresh_reading_layout()

    def _setup_vocab_tab(self):
        self.vocab_tab.setLayout(self.vocab_layout)

        self.btn_add_vocab.setText("Add Vocab")
        self.btn_add_vocab.clicked.connect(self.add_vocab_clicked)

        self.btn_remove_vocab.setText("Remove Vocab")
        self.btn_remove_vocab.clicked.connect(self.remove_vocab_clicked)

        self.btn_vocab_drill.setText("Vocab Drill")
        self.btn_vocab_drill.clicked.connect(self.vocab_drill_clicked)

        self.btn_vocab_rush.setText("Vocab Rush")
        self.btn_vocab_rush.clicked.connect(self.vocab_rush_clicked)

        self.btn_conj_rush.setText("Conj Rush")
        self.btn_conj_rush.clicked.connect(self.conj_rush_clicked)

        self.vocab_button_layout.addWidget(self.btn_add_vocab, 0, 0)
        self.vocab_button_layout.addWidget(self.btn_remove_vocab, 0, 1)
        self.vocab_button_layout.addWidget(self.btn_vocab_drill, 0, 2)
        self.vocab_button_layout.addWidget(self.btn_vocab_rush, 0, 3)
        self.vocab_button_layout.addWidget(self.btn_conj_rush, 0, 4)

        self.vocab_table.setModel(self.vocab_model)

        self.vocab_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.vocab_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.vocab_table.horizontalHeader().setSectionsClickable(False)
        self.vocab_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.vocab_table.verticalHeader().setVisible(False)
        self.vocab_table.selectionModel().selectionChanged.connect(self.vocab_selection_changed)
        self.vocab_table.doubleClicked.connect(self.vocab_table_double_clicked)

        self.vocab_layout.addWidget(self.vocab_table, 0, 0)
        self.vocab_layout.addWidget(self.vocab_definition_field, 0, 1)
        self.vocab_layout.addWidget(self.vocab_input_line, 1, 0)
        self.vocab_layout.addLayout(self.vocab_button_layout, 1, 1)

        self.vocab_layout.setRowMinimumHeight(0, 256)
        self.vocab_layout.setRowMinimumHeight(1, 128)
        self.vocab_layout.setColumnMinimumWidth(0, 1024)
        self.vocab_layout.setColumnMinimumWidth(1, 512)
        self.vocab_layout.setColumnStretch(0, 1)
        self.vocab_layout.setColumnStretch(1, 0)
        self.vocab_layout.setColumnStretch(2, 0)
        self.vocab_layout.setRowStretch(0, 1)
        self.vocab_layout.setRowStretch(1, 0)

        pyside_utils.set_font_size(self.vocab_input_line, 32)
        self.vocab_input_line.resize(512, 64)
        self.vocab_input_line.textChanged.connect(self.vocab_input_line_is_changed)
        self.vocab_input_line.selectionChanged.connect(self.vocab_input_text_selected)

        pyside_utils.set_font_size(self.vocab_table, 32)

    def _setup_news_tab(self):
        self.news_tab.setLayout(self.news_layout)
        self.news_layout.addWidget(self.news_field)
        pyside_utils.set_font_size(self.news_field, 16)

        self.news_field.refresh_list()
        self.news_field.selectionModel().selectionChanged.connect(self.news_selection_changed)

    def _setup_books_tab(self):
        self.books_tab.setLayout(self.books_layout)
        self.books_layout.addWidget(self.books_field)
        pyside_utils.set_font_size(self.books_field, 16)

        self.books_field.refresh_list()
        self.books_field.selectionModel().selectionChanged.connect(self.books_selection_changed)

    def _setup_manga_tab(self):
        self.manga_tab.setLayout(self.manga_layout)
        self.manga_layout.addWidget(self.manga_field)
        pyside_utils.set_font_size(self.manga_field, 16)

        self.manga_field.refresh_list()
        self.manga_field.selectionModel().selectionChanged.connect(self.manga_selection_changed)

    def _setup_log_tab(self):
        self.log_tab.setLayout(self.log_layout)
        self.log_layout.addWidget(self.log_field)
        self.log_field.setReadOnly(True)
        self.log_field.setHtml('')
        pyside_utils.set_font_size(self.log_field, 16)

    def _setup_settings_tab(self):
        self.settings_tab.setLayout(self.settings_layout)

    def _setup_tabs(self):
        self.tabs.currentChanged.connect(self.tab_changed)
        self.tabs.setTabPosition(QTabWidget.TabPosition.West)
        self.tabs.setMovable(True)

        self._setup_reading_tab()
        self._setup_vocab_tab()
        self._setup_news_tab()
        self._setup_books_tab()
        self._setup_manga_tab()
        self._setup_log_tab()
        self._setup_settings_tab()

        self.tabs.addTab(self.reading_tab, "read")
        self.tabs.addTab(self.vocab_tab, "vocab")
        self.tabs.addTab(self.news_tab, "news")
        self.tabs.addTab(self.books_tab, "books")
        self.tabs.addTab(self.manga_tab, "manga")
        self.tabs.addTab(self.log_tab, "log")
        self.tabs.addTab(self.settings_tab, "settings")

    def _setup_text(self):
        self.text_buffer = file_utils.read_txt_file(self.current_txt_file)

    def _setup_text_field(self):
        self.text_field.setReadOnly(True)
        self.text_field.setHtml('<font color="blue">' + self.text_buffer[self.text_field_i1:self.text_field_max_text] + '</font>')
        pyside_utils.set_font_size(self.text_field, 32)
        self.text_field.selectionChanged.connect(self.text_selected)

    def _setup_footer(self):
        self.bottom_left_text.setText("")
        pyside_utils.set_font_size(self.bottom_left_text, 8)
        self.bottom_left_text.setMaximumHeight(16)

    def _setup_input_line(self):
        pyside_utils.set_font_size(self.input_line, 32)
        self.input_line.resize(512, 64)
        self.input_line.textChanged.connect(self.input_line_is_changed)
        self.input_line.selectionChanged.connect(self.input_text_selected)

    def _setup_definition_field(self):
        self.definition_field.setReadOnly(True)
        self.definition_field.setHtml('')
        pyside_utils.set_font_size(self.definition_field, 16)
        self.definition_field.resize(256, 64)

        self.vocab_definition_field.setReadOnly(True)
        self.vocab_definition_field.setHtml('')
        pyside_utils.set_font_size(self.vocab_definition_field, 16)
        self.vocab_definition_field.resize(256, 64)

    def _setup_helper(self):
        self.load_data()

        self.setWindowTitle("vampaJP")
        # self.resize(1920, 1080)

        self.main_layout.addWidget(self.tabs)
        self.setLayout(self.main_layout)

        self._setup_tabs()
        self._setup_text()
        self._setup_text_field()
        self._setup_footer()
        self._setup_input_line()
        self._setup_definition_field()

        if self.manga_mode:
            self._manga_changed(self.current_manga_directory, True)
            self._change_manga_page(self.manga_chapter, self.manga_page)
            self._refresh_manga_viewer()
    """************************************** END UI SETUP **************************************"""

    """************************************** READING **************************************"""
    def _refresh_reading_layout(self):
        if self.manga_mode:
            self.reading_layout.setRowMinimumHeight(0, MANGA_VIEWER_HEIGHT)
            self.reading_layout.setRowMinimumHeight(1, int(READING_LAYOUT_ROW_TEXT_MIN_HEIGHT / 2))
            self.reading_layout.itemAt(0).widget().show()
            self.reading_layout.itemAt(1).widget().show()
            self.text_field_max_text = int(TEXT_FIELD_MAX_TEXT / 2)
        if not self.manga_mode:
            self.reading_layout.setRowMinimumHeight(0, 0)
            self.reading_layout.setRowMinimumHeight(1, READING_LAYOUT_ROW_TEXT_MIN_HEIGHT)
            self.reading_layout.itemAt(0).widget().hide()
            if MANGA_VIEWER_DUAL_PANEL_MODE:
                self.reading_layout.itemAt(1).widget().hide()
            self.text_field_max_text = TEXT_FIELD_MAX_TEXT

    def set_location(self, new_index):
        if new_index is None or new_index < 0:
            return
        if new_index > len(self.text_buffer):
            print("new location past end of file...")
            return

        self.text_field_i1 = max(new_index - self.text_field_buffer_room, 0)
        self.buffer_index = new_index
        self.data_stale = True
        self.refresh_text_display()

    def set_location_clicked(self):
        if self.manga_mode:
            chapter, ok = QInputDialog().getInt(self, "Set Chapter", "Chapter (0, " + str(self.total_manga_chapters) + "):", self.manga_chapter, 0, self.total_manga_chapters)
            if ok and chapter >= 0:
                page, ok = QInputDialog().getInt(self, "Set Page", "Page (0, " + str(self.total_manga_pages) + "):", self.manga_page, 0, self.total_manga_pages)
                if ok and page >= 0:
                    self._change_manga_page(chapter, page)
            return
        val, ok = QInputDialog().getInt(self, "Set Location", "Text location (0, " + str(len(self.text_buffer)) + "):", self.buffer_index, 0, len(self.text_buffer))
        # parent, title, label, value, minValue=0, maxValue=-2147483647,
        if ok and val >= 0:
            self.set_location(val)

    def get_current_book_character_count(self):
        return len(self.text_buffer)

    def find_current_sentence_index(self):
        try:
            index = self.buffer_index
            if index >= len(self.text_buffer) - 1:
                return len(self.text_buffer)
            while index > 0 and self.text_buffer[index-1] != '。':
                index -= 1
        except IndexError:
            print("error: invalid index...")
            print(len(self.text_buffer))
            print(self.buffer_index)
            self.buffer_index = len(self.text_buffer)
            index = len(self.text_buffer)
        return index

    def find_current_sentence_end_index(self):
        try:
            index = self.buffer_index
            while index < len(self.text_buffer) and self.text_buffer[index] != '。':
                index += 1
        except IndexError:
            print("error: invalid index...")
            print(len(self.text_buffer))
            print(self.buffer_index)
            self.buffer_index = len(self.text_buffer)
            index = len(self.text_buffer)
        return index

    def select_current_word(self):
        sentence = self.get_current_sentence()
        components = jp_utils.get_sentence_components(sentence)
        sentence_index = self.buffer_index - self.find_current_sentence_index()

        comp_index = 0
        i = 0
        b_found = False

        while i < sentence_index:
            j = 0
            while j < len(components[comp_index]):
                i += 1
                j += 1
                if i == sentence_index:
                    b_found = True
                    break
            if b_found:
                break
            comp_index += 1

        try:
            self.selection_size = len(components[comp_index + 1])
            self.keyboard_hotkey_selection_update()
        except IndexError:
            return

    def get_current_sentence(self):
        start_index = self.find_current_sentence_index()
        end_index = self.find_current_sentence_end_index()
        sentence = self.text_buffer[start_index:end_index]
        return sentence
    """************************************** END READING **************************************"""

    """************************************** MANGA **************************************"""
    def get_number_manga_pages(self):
        chapter_list = file_utils.get_directory_list(self.current_manga_directory)
        img_directory = os.path.join(self.current_manga_directory, chapter_list[self.manga_chapter])
        return len(file_utils.get_file_list(img_directory, ".jpg")) - 1

    def manga_chapter_changed(self):
        self.total_manga_pages = self.get_number_manga_pages()

    def left_img_clicked(self, right_half=False):
        if MANGA_VIEWER_DUAL_PANEL_MODE and self.manga_page_right_panel == self.manga_page:
            new_page = self.manga_page + 2
            self._change_manga_page(self.manga_chapter, new_page)
        else:
            if right_half:
                self.decrease_manga_page()
            else:
                self.increase_manga_page()

    def right_img_clicked(self, _right_half=False):
        if self.manga_page_right_panel == self.manga_page:
            self.decrease_manga_page()
        else:
            new_page = self.manga_page - 2
            self._change_manga_page(self.manga_chapter, new_page)

    def _change_manga_img(self, left_file, right_file=None):
        if MANGA_VIEWER_DUAL_PANEL_MODE:
            pixmap = QPixmap(left_file)
            self.reading_img_lbl_left.setPixmap(pixmap.scaled(MANGA_VIEWER_WIDTH, MANGA_VIEWER_HEIGHT, aspectMode=Qt.AspectRatioMode.KeepAspectRatio))
            pm2 = QPixmap(right_file)
            self.reading_img_lbl_right.setPixmap(pm2.scaled(MANGA_VIEWER_WIDTH, MANGA_VIEWER_HEIGHT, aspectMode=Qt.AspectRatioMode.KeepAspectRatio))
        else:
            pixmap = QPixmap(left_file)
            self.reading_img_lbl_left.setPixmap(pixmap.scaled(MANGA_VIEWER_WIDTH*2, MANGA_VIEWER_HEIGHT, aspectMode=Qt.AspectRatioMode.KeepAspectRatio))
            if right_file is not None:
                print("Sent 2 images during single panel mode...")

    def is_last_manga_page(self, page_number=None):
        if page_number is None:
            page_number = self.manga_page
        return page_number == self.total_manga_pages

    def is_last_manga_chapter(self, chapter=None):
        if chapter is None:
            chapter = self.manga_chapter
        return chapter == self.total_manga_chapters

    def _change_manga_chapter_helper(self, chapter, b_last_page=False):
        self.manga_chapter = chapter
        self.manga_chapter_changed()
        if b_last_page:
            self.manga_page = self.total_manga_pages
        else:
            self.manga_page = 0
            self.manga_page_right_panel = 0

    def _refresh_manga_viewer(self):
        chapter_list = file_utils.get_directory_list(self.current_manga_directory)
        img_directory = str(os.path.join(self.current_manga_directory, chapter_list[self.manga_chapter]))
        img_files = file_utils.get_file_list(img_directory, ".jpg")

        txt_directory = str(img_directory + r"/TXT/")
        txt_file = file_utils.get_file_list(txt_directory, ".txt")[self.manga_page]
        self.change_txt_file(os.path.join(txt_directory, txt_file))

        if MANGA_VIEWER_DUAL_PANEL_MODE:
            if self.manga_page_right_panel + 1 >= len(img_files):
                img_file_left = DEFAULT_BLACK_IMG
            else:
                img_file_left = os.path.join(img_directory, img_files[self.manga_page_right_panel + 1])
            img_file_right = os.path.join(img_directory, img_files[self.manga_page_right_panel])
            self._change_manga_img(img_file_left, img_file_right)
        else:
            img_file = os.path.join(img_directory, img_files[self.manga_page])
            self._change_manga_img(img_file)

    def _change_manga_page(self, chapter=0, page=0):
        # TODO: Working, code not pretty
        if self.manga_chapter == chapter and self.manga_page == page:
            return

        prev_chapter = self.manga_chapter
        prev_pg = self.manga_page

        if chapter > self.total_manga_chapters or chapter < 0:
            print("invalid chapter requested: {} {}".format(chapter, self.total_manga_chapters))
            return
        if self.manga_chapter != chapter:
            self._change_manga_chapter_helper(chapter)

        if page > self.total_manga_pages:
            if self.is_last_manga_page():
                if self.is_last_manga_chapter():
                    return
                else:
                    self._change_manga_chapter_helper(self.manga_chapter + 1)
                    page = 0
            else:
                page = self.total_manga_pages

        if page < 0:
            if self.manga_chapter == 0:
                return
            else:
                self._change_manga_chapter_helper(self.manga_chapter - 1, True)
                page = self.manga_page

        if page > self.total_manga_pages or page < 0:
            print("invalid page number requested {} {}".format(page, self.total_manga_pages))
            return

        self.manga_page = page

        if MANGA_VIEWER_DUAL_PANEL_MODE:
            if self.manga_page % 2 == 0:
                self.manga_page_right_panel = self.manga_page
                self.reading_img_lbl_left.setStyleSheet("border: 0px solid black;")
                self.reading_img_lbl_right.setStyleSheet("border: 5px solid red;")
            else:
                self.manga_page_right_panel = self.manga_page - 1
                self.reading_img_lbl_left.setStyleSheet("border: 5px solid red;")
                self.reading_img_lbl_right.setStyleSheet("border: 0px solid black;")

        if prev_pg != self.manga_page or prev_chapter != self.manga_chapter:
            self._refresh_manga_viewer()

    def _manga_changed(self, manga_directory, b_force_load=False):
        # TODO: Load chapter/page for specific directory
        self.total_manga_chapters = len(file_utils.get_directory_list(manga_directory)) - 1

        if not self.manga_mode:
            self.manga_mode = True
            self._refresh_reading_layout()
        if not b_force_load and manga_directory == self.current_manga_directory:
            return

        self.current_manga_directory = manga_directory
        self.total_manga_pages = self.get_number_manga_pages()
        self._change_manga_page(self.manga_chapter, self.manga_page)
        self._refresh_manga_viewer()

    def manga_selection_changed(self):
        items = self.manga_field.selectedItems()
        for item in items:
            manga_directory = "Manga/" + item.text()
            self.manga_page = 0
            self.manga_chapter = 0
            self._manga_changed(manga_directory)

    def increase_manga_page(self):
        self._change_manga_page(self.manga_chapter, self.manga_page+1)

    def decrease_manga_page(self):
        self._change_manga_page(self.manga_chapter, self.manga_page-1)
    """************************************** END MANGA **************************************"""

    """************************************** VOCAB **************************************"""
    def vocab_table_double_clicked(self):
        indices = self.vocab_table.selectedIndexes()
        self.vocab_model.sort_by_column(indices[0].column())

    def add_vocab(self, word):
        if len(word) > 0:
            if word not in self.vocab_list:
                self.vocab_list.append(word)
                self.vocab_model.add_vocab(word)
                self.save_data(True)

    def save_vocab_clicked(self):
        self.add_vocab(self.text_field.textCursor().selectedText())

    def add_vocab_clicked(self):
        self.add_vocab(self.vocab_input_line.displayText())

    def remove_vocab_clicked(self):
        selected_vocab = []
        indices = self.vocab_table.selectedIndexes()
        for i in indices:
            v = self.vocab_model.get_vocab(i)
            selected_vocab.append(v)

        for v in selected_vocab:
            if len(v) > 0:
                self.vocab_list.remove(v)
                self.save_data(True)
                self.vocab_model.remove_vocab(v)
                self.refresh_vocab_table()
                return

    def vocab_drill_clicked(self):
        number_of_vocab = 10
        prioritize = True

        self.vocab_drill_window = vocab_utils.vocab_quiz(number_of_vocab=number_of_vocab, prioritize=prioritize, save_stats=True)

    def vocab_rush_clicked(self):
        prioritize = False

        self.vocab_drill_window = vocab_utils.vocab_rush(prioritize=prioritize, save_stats=True)

    def conj_rush_clicked(self):
        prioritize = False
        max_conj = 1
        self.vocab_drill_window = vocab_utils.conj_rush(prioritize=prioritize, save_stats=False, max_conj=max_conj)

    def vocab_input_line_is_changed(self):
        self.vocab_list_filter = self.vocab_input_line.displayText()
        self.refresh_vocab_table()

    def vocab_input_text_selected(self):
        txt = self.vocab_input_line.selectedText()
        if txt != self.previous_selected_text:
            self.previous_selected_text = txt
            if len(txt) > 0:
                self.display_definitions(txt)

    def vocab_selection_changed(self):
        selected_vocab = []
        indices = self.vocab_table.selectedIndexes()

        for i in indices:
            v = self.vocab_model.get_vocab(i)
            selected_vocab.append(v)

        for v in selected_vocab:
            if len(v) == 0:
                continue
            self.display_definitions(v)

            temp_filename = "TEMP/" + v + ".txt"
            all_sentences = ""
            try:
                sentences = data_utils.VocabSentences().get_data()[v]
            except KeyError:
                vocab_utils.update_all()
                sentences = data_utils.VocabSentences().get_sentences(v)

            random.shuffle(sentences)
            for s in sentences:
                all_sentences += s
            file_utils.save_txt_file(temp_filename, all_sentences)
            self.change_txt_file(temp_filename, index_override=0)
            return
    """************************************** END VOCAB **************************************"""

    """************************************** NEWS **************************************"""
    def news_selection_changed(self):
        if self.manga_mode:
            self.manga_mode = False
            self._refresh_reading_layout()
        items = self.news_field.selectedItems()
        for item in items:
            txt_file = r"News/" + item.text()
            self.change_txt_file(txt_file)
            return
    """************************************** END NEWS **************************************"""

    """************************************** BOOKS **************************************"""
    def books_selection_changed(self):
        if self.manga_mode:
            self.manga_mode = False
            self._refresh_reading_layout()
        items = self.books_field.selectedItems()
        for item in items:
            txt_file = r"LN/" + item.text()
            self.change_txt_file(txt_file)
            return
    """************************************** END BOOKS **************************************"""

    """************************************** EVENTS **************************************"""
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.BackButton:
            self.change_to_previous_file()
        elif event.button() == Qt.MouseButton.ForwardButton:
            self.change_to_next_file()

    def ctrl_pressed(self):
        if self.auto_word_select:
            self.select_current_word()
        else:
            self.selection_size += 1
            self.keyboard_hotkey_selection_update()

    def alt_pressed(self):
        if self.selection_size > 1:
            self.selection_size -= 1
        self.keyboard_hotkey_selection_update()

    def up_pressed(self):
        self.increase_manga_page()

    def down_pressed(self):
        self.decrease_manga_page()

    def f5_pressed(self):
        if self.tabs.currentIndex() == 1:  # vocab tab
            self.vocab_stats = data_utils.VocabStatsData().get_data()
            self.vocab_rush_data = vocab_utils.VocabRushData()
            self.refresh_vocab_table()
        if self.tabs.currentIndex() == 2:  # news tab
            jp_utils.download_nhk_news()
            self.news_field.refresh_list()
            print("news done downloading...")
        if self.tabs.currentIndex() == 3:  # books tab
            self.books_field.refresh_list()
        if self.tabs.currentIndex() == 4:  # manga tab
            self.manga_field.refresh_list()

    def shift_pressed(self):
        self.show_english_definitions = True
        self.display_definitions(self.current_showing_word)

    def shift_released(self):
        self.show_english_definitions = False
        self.display_definitions(self.current_showing_word)

    def tab_pressed(self):
        if self.buffer_index < self.get_current_book_character_count():
            self.buffer_index += 1
            self.data_stale = True
        elif self.manga_mode:
            self.increase_manga_page()
        self.refresh_text_display()

    def window_unselected(self):
        self.input_line.set_gui_lost_focus()
        self.vocab_input_line.set_gui_lost_focus()
    """************************************** END EVENTS **************************************"""

    """************************************** UPDATES **************************************"""
    def change_txt_file(self, txt_file, index_override=None, update_file_stack=True):
        if txt_file == self.current_txt_file:
            return
        self.save_data()
        if update_file_stack:
            self.previous_files_stack = self.previous_files_stack[0:self.file_stack_index+1]
            self.previous_files_stack.append(self.current_txt_file)
            self.file_stack_index = len(self.previous_files_stack) - 1
        debug_text = False
        if debug_text:
            print(self.previous_files_stack)
        self.set_current_txt_file(txt_file)

        self._setup_text()

        if index_override:
            self.buffer_index = index_override
        else:
            if self.manga_mode:
                self.buffer_index = 0
            else:
                self.buffer_index = self.saved_data.get_book_index(self.current_txt_file)

        self.refresh_text_display()

    def change_to_previous_file(self):
        if self.file_stack_index == 0:
            return
        self.file_stack_index -= 1
        self.change_txt_file(self.previous_files_stack[self.file_stack_index], update_file_stack=False)

    def change_to_next_file(self):
        if len(self.previous_files_stack) <= self.file_stack_index + 1:
            return
        self.file_stack_index += 1
        self.change_txt_file(self.previous_files_stack[self.file_stack_index], update_file_stack=False)

    def refresh_vocab_table(self):
        self.vocab_model.clear_data()
        for v in self.vocab_list:
            if not self.vocab_list_filter or self.vocab_list_filter in v:
                try:
                    correct = self.vocab_stats[v]["correct"]
                    incorrect = self.vocab_stats[v]["incorrect"]
                    in_a_row = self.vocab_stats[v]["in_a_row"]
                except KeyError:
                    correct, incorrect, in_a_row = 0, 0, 0

                vr_c = self.vocab_rush_data.get_total_correct(v)
                vr_i = self.vocab_rush_data.get_total_incorrect(v)
                vr_iar = self.vocab_rush_data.get_in_a_row(v)
                vr_priority = self.vocab_rush_data.get_priority(v)
                vr_date = self.vocab_rush_data.get_last_date(v)

                self.vocab_model.add_vocab(v, correct, incorrect, in_a_row, vr_c, vr_i, vr_iar, vr_priority, vr_date)

        # Ugly but can crash if table is empty...
        if self.vocab_model.columnCount() == 0:
            self.vocab_model.add_vocab("Empty")

    def set_current_txt_file(self, file_path=""):
        self.current_txt_file = file_path.replace("\\", "/")

    def tab_changed(self):
        self.save_data()
        if self.tabs.currentIndex() == 2:
            self.news_field.refresh_list()
        elif self.tabs.currentIndex() == 3:
            self.books_field.refresh_list()

    def refresh_text_display(self):
        self._refresh_buffer()
        gray_text = '<font color="gray">' + self.text_buffer[self.text_field_i1:self.buffer_index] + '</font>'
        blue_text = '<font color="blue">' + self.text_buffer[self.buffer_index:self.text_field_max_text + self.text_field_i1] + '</font>'
        self.text_field.setHtml(gray_text + blue_text)

    def _refresh_buffer(self):
        if self.buffer_index >= self.text_field_i1 + self.text_field_max_text - self.text_field_buffer_room:
            self.text_field_i1 = self.buffer_index - self.text_field_buffer_room
        if self.text_field_i1 > self.buffer_index:
            self.text_field_i1 = self.buffer_index
        if self.manga_mode:
            self.bottom_left_text.setText(self.current_manga_directory.split("/")[-2] + " " + str(self.manga_chapter) + "/" + str(self.total_manga_chapters) + " " + str(self.manga_page) + "/" + str(self.total_manga_pages))
        else:
            self.bottom_left_text.setText(self.current_txt_file.split("/")[-1].split(".")[0][0:30] + ": " + str(self.buffer_index) + r'/' + str(len(self.text_buffer)))

    def input_line_is_changed(self):
        self.compare_text()

    def display_definitions(self, txt):
        temp_display_length = 250
        definitions = jp_utils.get_definitions(txt)

        if len(definitions) == 0:
            return

        self.current_showing_word = txt

        shortened = ""
        for d in definitions:
            if len(d) > temp_display_length:
                d_split = (d[:temp_display_length] + "...").split(':', 1)
            else:
                d_split = d.split(':', 1)
            shortened += '<font color="blue">' + d_split[0] + '</font>'
            if self.show_english_definitions:
                shortened += '<br><font color="green">' + d_split[1] + '</font>'
            shortened += "<br>"

        if self.tabs.currentIndex() == 0:
            self.definition_field.setHtml(shortened)
        elif self.tabs.currentIndex() == 1:
            self.vocab_definition_field.setHtml(shortened)

    def keyboard_hotkey_selection_update(self):
        if self.selection_size_previous_buffer_index != self.buffer_index:
            self.selection_size = 1
            self.selection_size_previous_buffer_index = self.buffer_index
        cursor = self.text_field.textCursor()
        position = self.buffer_index - self.text_field_i1
        cursor.setPosition(position)
        cursor.setPosition(position + self.selection_size, QTextCursor.MoveMode.KeepAnchor)
        self.text_field.setTextCursor(cursor)

    def text_selected(self):
        txt = self.text_field.textCursor().selectedText()
        if txt != self.previous_selected_text:
            self.previous_selected_text = txt
            if len(txt) > 0:
                self.display_definitions(txt)

    def input_text_selected(self):
        txt = self.input_line.selectedText()
        if txt != self.previous_selected_text:
            self.previous_selected_text = txt
            if len(txt) > 0:
                self.display_definitions(txt)

    def compare_text(self):
        txt2 = self.input_line.displayText()
        if len(txt2) > 0:
            txt1 = self.text_buffer[self.buffer_index:self.buffer_index+len(txt2)]
            if txt1 == txt2:
                self.buffer_index += len(txt2)
                self.data_stale = True
                self.input_line.clear()

                if self.manga_mode and self.buffer_index >= self.get_current_book_character_count():
                    self.increase_manga_page()

                self.refresh_text_display()
    """************************************** END UPDATES **************************************"""

    """************************************** DATA **************************************"""
    def _load_manga_data(self, manga_file_path):
        self._manga_changed(manga_file_path)
        chapter = self.saved_data.get_manga_chapter(self.current_manga_directory)
        page = self.saved_data.get_manga_page(self.current_manga_directory)
        self._change_manga_page(chapter, page)

    def load_data(self):
        self.vocab_list = self.saved_data.get_vocab_list()
        self.manga_mode = self.saved_data.was_manga_open()  # TODO: Manga should be it's own tab...

        last_file = self.saved_data.get_last_open_file()

        if self.manga_mode:
            self._load_manga_data(last_file)
        else:
            self.set_current_txt_file(last_file)

        self.buffer_index = self.saved_data.get_book_index(self.current_txt_file)

        if self.saved_data.get_saved_date() != str(date.today()):
            jp_utils.download_nhk_news()

        random.shuffle(self.vocab_list)
        self.refresh_vocab_table()

        self.vocab_sentences = data_utils.VocabSentences().get_data()
        self.vocab_rush_data = vocab_utils.VocabRushData()

    def save_data(self, b_force=False):
        if self.data_stale or b_force:
            # TODO: Saving should be handled by data_utils....
            updated_book_dict = self.saved_data.get_book_dict()

            if self.current_txt_file is not None:
                updated_book_dict[self.current_txt_file.replace("\\", "/")] = {
                    "index": self.find_current_sentence_index(),
                    "total_chars": self.get_current_book_character_count()
                }

            if self.current_manga_directory:
                updated_book_dict[self.current_manga_directory] = {
                    "saved_chapter": self.manga_chapter,
                    "saved_page": self.manga_page
                }

            pruned_book_dict = updated_book_dict.copy()
            key_list = [k for k in pruned_book_dict.keys()]
            for key in key_list:
                if key is not None and key.startswith("TEMP"):
                    pruned_book_dict.pop(key)

            last_file = self.current_txt_file
            if self.manga_mode:
                last_file = self.current_manga_directory

            data = {
                "book_dict": pruned_book_dict,
                "vocab_list": self.vocab_list,
                "last_open_file": last_file,
                "last_file_manga": self.manga_mode,
                "last_manga_directory": self.current_manga_directory,
                "last_date": str(date.today())
            }
            self.saved_data.save_data(data)
    """************************************** END DATA **************************************"""


def setup_gui():
    app = QApplication(sys.argv)
    window = MainGui()
    window.setGeometry(25, 25, 100, 100)
    window.show()
    app.exec()


def main():
    setup_gui()


if __name__ == '__main__':
    main()
