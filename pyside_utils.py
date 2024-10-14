import os
from threading import Timer
import random

import pyautogui
import py_win_keyboard_layout as pwkl
from PySide6.QtWidgets import QGridLayout, QLabel, QLineEdit, QTextEdit, QListWidget, QWidget, QListWidgetItem, QMenu, QTableView
from PySide6.QtGui import QKeyEvent, Qt, QColor, QCursor, QAction
from PySide6.QtCore import QAbstractTableModel, QEvent

import data_utils
import jp_utils

JAPANESE_LOCALE_ID = 68224017
ENGLISH_LOCALE_ID = 67699721


def change_to_japanese():
    # TODO: There doesn't seem to be a good way to do it, but would like to check current input mode...
    pwkl.change_foreground_window_keyboard_layout(JAPANESE_LOCALE_ID)

    pyautogui.keyDown('enter')  # TODO: fix: Ugly hack to signal in-between keys are automated...
    pyautogui.keyDown("ctrl")
    pyautogui.keyDown("capslock")
    pyautogui.keyUp("ctrl")
    pyautogui.keyUp("capslock")
    pyautogui.keyUp('enter')  # Ugly hack...


def change_to_english():
    pwkl.change_foreground_window_keyboard_layout(ENGLISH_LOCALE_ID)


class VampaJpMainWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.ignore_key_lock = True

    def post_load(self):
        self.setStyleSheet(get_style_sheet())
        Timer(.25, change_to_japanese).start()

    def save_data(self, b_force=False):
        pass

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return:  # enter
            self.ignore_key_lock = True
        elif event.key() == Qt.Key.Key_Control and not self.ignore_key_lock:  # ctrl
            self.ctrl_pressed()
        elif event.key() == Qt.Key.Key_Alt:  # alt
            self.alt_pressed()
        elif event.key() == Qt.Key.Key_F5:  # f5
            self.f5_pressed()
        elif event.key() == Qt.Key.Key_Shift:  # left shift to temporarily show definitions
            self.shift_pressed()
        elif event.key() == Qt.Key.Key_Escape:  # esc, close
            self.close()
        elif event.key() == Qt.Key.Key_Up:
            self.up_pressed()
        elif event.key() == Qt.Key.Key_Down:
            self.down_pressed()
        else:
            debug_print = False
            if debug_print:
                print(event.key())

        super().keyPressEvent(event)

    def up_pressed(self):
        pass

    def down_pressed(self):
        pass

    def ctrl_pressed(self):
        pass

    def alt_pressed(self):
        pass

    def f5_pressed(self):
        pass

    def shift_pressed(self):
        pass

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key.Key_Return:  # enter
            self.ignore_key_lock = False
        elif event.key() == Qt.Key.Key_Control and not self.ignore_key_lock:  # ctrl
            self.ctrl_released()
        elif event.key() == Qt.Key.Key_Shift:  # left shift to temporarily show definitions
            self.shift_released()

        super().keyReleaseEvent(event)

    def ctrl_released(self):
        pass

    def shift_released(self):
        pass

    def event(self, cur_event):
        t = type(cur_event)

        if t == QKeyEvent:
            if cur_event.key() == Qt.Key.Key_Tab:  # tab key (skip current text)
                self.tab_pressed()
                return True
        elif cur_event.type() == QEvent.Type.WindowDeactivate:
            self.window_unselected()
        return super().event(cur_event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._move()
            return super().mousePressEvent(event)

    def tab_pressed(self):
        pass

    def window_unselected(self):
        pass

    def _move(self):
        window = self.window().windowHandle()
        window.startSystemMove()

    def closeEvent(self, event):
        self.save_data(True)
        super().closeEvent(event)


class QuizGui(VampaJpMainWidget):
    def __init__(self, parent=None, number_of_questions=-1, prioritize=False, save_stats=True):
        super().__init__(parent)

        self.number_of_questions = number_of_questions
        self.prioritize = prioritize
        self.save_stats = save_stats

        self.quiz_problems = []
        self.quiz_data = {}
        self.current_question = ""
        self.current_answers = []

        self.wrong_questions = []
        self.correct_questions = []

        self.setup_quiz()

        self.setWindowTitle("vampaJP_QuizGui")
        self.auto_resize()

        self.main_layout = QGridLayout(self)

        self.main_text = QLabel(self)
        self.main_text.setText("")
        set_font_size(self.main_text, 32)

        self.input_line = InputLineEdit(self)
        self.input_line.textChanged.connect(self.input_line_is_changed)
        set_font_size(self.input_line, 32)
        self.input_line.resize(512, 64)
        self.input_line.setFocus()

        self.bottom_text = QLabel(self)
        self.bottom_text.setText("")
        set_font_size(self.bottom_text, 8)
        self.bottom_text.setMaximumHeight(16)

        self.main_layout.addWidget(self.main_text, 0, 0)
        self.main_layout.addWidget(self.input_line, 1, 0)
        self.main_layout.addWidget(self.bottom_text, 2, 0)

        self.setLayout(self.main_layout)

        self.input_line_is_changed()

        self.resize_lock = False

        self.post_load()

    def save_data(self, b_force=False):
        pass

    def tab_pressed(self):
        pass

    def window_unselected(self):
        self.input_line.set_gui_lost_focus()

    def ctrl_pressed(self):
        set_font_size(self.main_text, 12)
        self.main_text.setText(self.get_answers())
        if self.current_question not in self.wrong_questions:
            self.wrong_questions.append(self.current_question)

    def shift_pressed(self):
        set_font_size(self.main_text, 12)
        self.main_text.setText(self.get_definitions())
        if self.current_question not in self.wrong_questions:
            self.wrong_questions.append(self.current_question)

    def auto_resize(self):
        self.resize(300, 50)

    def ctrl_released(self):
        self.main_text.setText(self.current_question)
        set_font_size(self.main_text, 32)
        self.auto_resize()

    def shift_released(self):
        self.main_text.setText(self.current_question)
        set_font_size(self.main_text, 32)
        self.auto_resize()

    def input_line_is_changed(self):
        txt = self.input_line.displayText()
        if self.current_question == txt:
            if self.current_question not in self.wrong_questions:
                self.correct_questions.append(self.current_question)
            self.setup_next_problem()

    def get_definitions(self):
        definitions_string = ""
        for d in self.quiz_data[self.current_question]['definitions']:
            definitions_string += d.split(": ")[1][0:70]
        return definitions_string

    def get_answers(self):
        answers_string = ""
        for a in self.current_answers:
            if len(answers_string) > 0:
                answers_string += "\n"
            answers_string += a
        return answers_string

    def sorting_priority(self, question):
        return 100

    def setup_questions(self, question_list):
        updated_question_list = question_list
        if self.prioritize is False:
            random.shuffle(updated_question_list)
        else:
            updated_question_list.sort(key=self.sorting_priority)
            updated_question_list.reverse()

        for v in updated_question_list[0:self.number_of_questions]:
            spellings, meanings = self.get_vocab_data(v)
            self.quiz_problems.append([v, spellings])

    def setup_quiz(self):
        question_list = data_utils.SavedData().get_vocab_list()
        self.quiz_data = data_utils.VocabQuizData().get_data()

        self.setup_questions(question_list)

    def update_quiz_data(self):
        question_list = data_utils.VocabQuizData().get_data()

        keys = self.quiz_data.keys()
        for v in question_list:
            if v not in keys:
                definitions = jp_utils.get_definitions(v)
                verb_type = str(jp_utils.get_verb_type(v))
                self.quiz_data[v] = {'definitions': definitions, 'verb_type': verb_type}

        data_utils.VocabQuizData().save_data(self.quiz_data)

    def get_vocab_data(self, vocab):
        try:
            definitions = self.quiz_data[vocab]['definitions']
        except KeyError:
            self.update_quiz_data()
            definitions = self.quiz_data[vocab]['definitions']

        spellings = []
        meanings = []
        for d in definitions:
            d_split = d.split(':', 1)
            spellings.append(d_split[0].split(' (')[0])
            meanings.append(d_split[1])

        return spellings, meanings

    def setup_next_problem(self):
        if len(self.quiz_problems) == 0:
            self.quiz_complete()
            return

        self.bottom_text.setText(str(len(self.quiz_problems)))
        question = self.quiz_problems.pop()

        self.current_question = question[0]
        self.current_answers = question[1]

        self.input_line.clear()
        self.main_text.setText(self.current_question)
        self.auto_resize()

    def quiz_complete(self):
        self.close()


class VocabTableView(QTableView):
    def __init__(self, vocab_model, parent=None):
        super(VocabTableView, self).__init__(parent)
        self.vocab_model = vocab_model

        self.q_hidden = False
        self.vr_hidden = False

    def default_hide_columns(self):
        # 'vocab', 'q_Correct', 'q_Incorrect', 'q_%', 'q_IaR', 'vr_C', 'vr_I', 'vr_%', 'vr_IaR', 'vr_Priority', 'vr_date'
        self.hide_column('q_Correct')
        self.hide_column('q_Incorrect')
        self.hide_column('q_%')
        self.hide_column('q_IaR')
        # self.hide_column('vr_C')
        # self.hide_column('vr_I')
        # self.hide_column('vr_%')
        # self.hide_column('vr_IaR')
        # self.hide_column('vr_Priority')
        self.hide_column('vr_date')

    def hide_column(self, name):
        self.setColumnHidden(self.vocab_model.column_list.index(name), True)

    def column_toggle_fn(self, col=None):
        return lambda: self.setColumnHidden(col, not self.isColumnHidden(col))

    def toggle_quiz_stats(self):
        self.q_hidden = not self.q_hidden
        for i in range(len(self.vocab_model.column_list)):
            if self.vocab_model.column_list[i].startswith('q_'):
                self.setColumnHidden(i, self.q_hidden)

    def toggle_vocab_rush(self):
        self.vr_hidden = not self.vr_hidden
        for i in range(len(self.vocab_model.column_list)):
            if self.vocab_model.column_list[i].startswith('vr_'):
                self.setColumnHidden(i, self.vr_hidden)

    def quiz_stats_toggle_fn(self):
        return lambda: self.toggle_quiz_stats()

    def vocab_rush_toggle_fn(self):
        return lambda: self.toggle_vocab_rush()

    def contextMenuEvent(self, pos):
        menu = QMenu(self)

        action = QAction("quiz_stats", self)
        action.triggered.connect(self.quiz_stats_toggle_fn())
        menu.addAction(action)

        action = QAction("vocab_rush_stats", self)
        action.triggered.connect(self.vocab_rush_toggle_fn())
        menu.addAction(action)

        menu.addSeparator()

        for i in range(len(self.vocab_model.column_list)):
            name = self.vocab_model.column_list[i]
            if name == 'vocab':
                continue
            action = QAction(name, self)
            action.triggered.connect(self.column_toggle_fn(i))
            menu.addAction(action)
            i += 1

        menu.popup(QCursor.pos())


class VocabTableModel(QAbstractTableModel):
    def __init__(self, data):
        super(VocabTableModel, self).__init__()
        self._data = data
        self.setHeaderData(1, Qt.Orientation.Vertical, 'test')

        self.sort_inverse = False
        self.sorted_column = -1

        self.column_list = ['vocab', 'q_Correct', 'q_Incorrect', 'q_%', 'q_IaR', 'vr_C', 'vr_I', 'vr_%', 'vr_IaR', 'vr_Priority', 'vr_date']

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.column_list[section]
        return super().headerData(section, orientation, role)

    def clear_data(self):
        self._data.clear()

    def add_vocab(self, v, c=0, i=0, r=0, vr_c=0, vr_i=0, vr_iar=0, vr_priority=100, vr_date="0-0-0"):
        if i+c != 0:
            percent = int(c*100/(i+c))
        else:
            percent = -1
        if vr_i+vr_c != 0:
            vr_percent = int(vr_c*100/(vr_i+vr_c))
        else:
            vr_percent = -1
        self._data.append([v, c, i, percent, r, vr_c, vr_i, vr_percent, vr_iar, vr_priority, vr_date])
        self.layoutChanged.emit()

    def remove_vocab(self, v):
        for i in range(len(self._data)):
            if self._data[i][0] == v:
                self._data.remove(self._data[i])
                self.layoutChanged.emit()
                return

    def get_vocab(self, model_index):
        return self._data[model_index.row()][0]

    def sort_by_column(self, index=0):
        if self.sorted_column == index:
            self.sort_inverse = not self.sort_inverse
        else:
            self.sorted_column = index
            self.sort_inverse = False

        self._data = sorted(self._data, key=lambda x: x[index])
        if self.sort_inverse:
            self._data.reverse()

        self.layoutChanged.emit()

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            return self._data[index.row()][index.column()]

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        try:
            return len(self._data[0])
        except IndexError:
            return 0


class MyColors(QColor):
    def __init__(self, r, g, b):
        super().__init__(r, g, b)

    def as_string(self):
        return "rgb(" + str(self.red()) + "," + str(self.green()) + "," + str(self.blue()) + ")"


class MyListWidgetItem(QListWidgetItem):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.read_status = 1  # not read

    def __lt__(self, other):
        if self.read_status < other.read_status:
            return True
        elif self.read_status > other.read_status:
            return False
        else:
            return self.text() < other.text()

    def __gt__(self, other):
        if self.read_status > other.read_status:
            return True
        elif self.read_status < other.read_status:
            return False
        else:
            return self.text() > other.text()

    def __eq__(self, other):
        return self.read_status == other.read_status and self.text() == other.text()

    def set_read_status(self, read_status):
        # 0 partially read, 1 not read, 2 fully read
        self.read_status = read_status
        if self.read_status == 1:
            self.setForeground(COLORS.BRIGHT_TEXT)
        elif self.read_status == 0:
            self.setForeground(COLORS.SECONDARY_TEXT)
        else:
            self.setForeground(COLORS.DARK_TEXT)


# TODO: Zoom for non-aspect ratio images... T_T
#       Should be able to just add offset to mouse pos? Maybe?
class ClickableLabel(QLabel):
    def __init__(self, parent=None, click_fn=None, max_width=0, max_height=0):
        super().__init__(parent)
        self.click_fn = click_fn

        self.original_pm = None
        self.max_width = max_width
        self.max_height = max_height

        self.zoom_lvl = 1.0
        self.prev_x_offset = 0.0
        self.prev_y_offset = 0.0
        self.pan_mode = False
        self.old_mouse_pos = None

    def setPixmap(self, pixmap, original=True):
        super().setPixmap(pixmap)
        if original:
            self.original_pm = self.pixmap().copy()
            self.reset_zoom()

    def find_offset(self, mp, prev_zoom, prev_offset, original_size):
        mouse = mp / prev_zoom
        zoom_radius = (original_size / self.zoom_lvl) / 2
        new_offset_width = mouse - zoom_radius

        offset = prev_offset + new_offset_width

        far_border = prev_offset + (original_size / prev_zoom)
        if self.zoom_lvl > prev_zoom:
            offset = max(offset, prev_offset)
            max_offset = far_border - zoom_radius * 2
            offset = min(max_offset, offset)
        else:
            min_offset = far_border - zoom_radius*2
            offset = max(0, offset, min_offset)
            offset = min(offset, original_size - zoom_radius * 2, prev_offset)
        return offset

    def mouseMoveEvent(self, event):  # Only happens when a mouse button is held/etc
        super().mouseMoveEvent(event)
        if self.pan_mode and self.old_mouse_pos:
            x_delta = self.old_mouse_pos.x() - event.pos().x()
            y_delta = self.old_mouse_pos.y() - event.pos().y()
            self.move_zoom(int(x_delta / self.zoom_lvl), int(y_delta / self.zoom_lvl))
        self.old_mouse_pos = event.pos()

    def reset_zoom(self):
        self.zoom_lvl = 1.0
        self.prev_x_offset = 0
        self.prev_y_offset = 0
        self.setPixmap(self.original_pm, False)

    def move_zoom(self, x_offset, y_offset):
        x_offset += self.prev_x_offset
        y_offset += self.prev_y_offset
        x_offset = min(max(x_offset, 0), self.max_width - (self.max_width / self.zoom_lvl))
        y_offset = min(max(y_offset, 0), self.max_height - (self.max_height / self.zoom_lvl))
        self.prev_x_offset = x_offset
        self.prev_y_offset = y_offset
        pm = self.original_pm.copy()
        size = (self.max_width * self.zoom_lvl, self.max_height * self.zoom_lvl)
        scaled_pm = pm.scaled(size[0], size[1], aspectMode=Qt.AspectRatioMode.KeepAspectRatio).copy(x_offset * self.zoom_lvl, y_offset * self.zoom_lvl, self.max_width, self.max_height)
        self.setPixmap(scaled_pm, False)

    def zoom(self, x, y, new_zoom):
        prev_zoom = self.zoom_lvl
        self.zoom_lvl = new_zoom

        x_offset = self.find_offset(x, prev_zoom, self.prev_x_offset, self.original_pm.width())
        self.prev_x_offset = x_offset
        y_offset = self.find_offset(y, prev_zoom, self.prev_y_offset, self.original_pm.height())
        self.prev_y_offset = y_offset

        if prev_zoom != self.zoom_lvl:
            pm = self.original_pm.copy()
            size = (self.max_width * self.zoom_lvl, self.max_height * self.zoom_lvl)

            scaled_pm = pm.scaled(size[0], size[1], aspectMode=Qt.AspectRatioMode.KeepAspectRatio).copy(x_offset * self.zoom_lvl, y_offset * self.zoom_lvl, self.max_width, self.max_height)
            self.setPixmap(scaled_pm, False)

    def wheelEvent(self, event):
        mouse_pos = event.position()

        new_zoom = 1.0
        if event.angleDelta().y() > 0.0:
            new_zoom = self.zoom_lvl + 1.0
        elif event.angleDelta().y() < 0.0:
            new_zoom = self.zoom_lvl - 1.0

        if new_zoom < 1.0:
            self.reset_zoom()
            return

        self.zoom(mouse_pos.x(), mouse_pos.y(), new_zoom)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.zoom_lvl == 1.0:
                right_side = event.pos().x() >= self.width()/2
                self.click_fn(right_side)
            else:
                self.pan_mode = True
        elif event.button() == Qt.MouseButton.MiddleButton:
            if self.zoom_lvl != 1.0:
                self.reset_zoom()
            else:
                self.zoom(event.pos().x(), event.pos().y(), 5.0)
        elif event.button() == Qt.MouseButton.RightButton:
            self.pan_mode = True

    def mouseReleaseEvent(self, event):
        if self.pan_mode:
            if event.button() == Qt.MouseButton.LeftButton:
                self.pan_mode = False
                self.old_mouse_pos = None
            elif event.button() == Qt.MouseButton.RightButton:
                self.pan_mode = False
                self.old_mouse_pos = None


# noinspection PyTypeChecker
class MyListWidget(QListWidget):
    def __init__(self, parent=None, saved_data=None, directory_prefix="", file_type=".txt"):
        super().__init__(parent)
        self.directory_prefix = directory_prefix
        self.file_type = file_type
        self.saved_data = saved_data

    def _get_read_status(self, filename):
        book_index = self.saved_data.get_book_index(filename)
        book_total_chars = self.saved_data.get_book_total_characters(filename)

        if book_index == 0:
            return 1
        elif book_index >= book_total_chars - 1:
            return 2
        else:
            return 0

    def refresh_list(self):
        try:
            dir_list = os.listdir(self.directory_prefix)
        except FileNotFoundError:
            dir_list = []
        for f in dir_list:
            file_path = os.path.join(self.directory_prefix, f)
            if f.endswith(self.file_type) or (self.file_type == "dir" and os.path.isdir(file_path)):
                if not self.findItems(f, Qt.MatchFlag.MatchExactly):
                    item = MyListWidgetItem(f)

                    filename = self.directory_prefix + str(item.text())
                    item.set_read_status(self._get_read_status(filename))

                    self.addItem(item)

        self.sortItems()


class COLORS:
    BLACK = MyColors(0, 0, 0)
    GRAY = MyColors(37, 37, 37)
    BLACK_BLUE = MyColors(0, 5, 15)
    DARK_BLUE = MyColors(0, 20, 40)
    BLUE = MyColors(0, 80, 180)
    BRIGHT_BLUE = MyColors(0, 120, 215)
    TEAL = MyColors(0, 170, 180)
    DARK_TEAL = MyColors(0, 120, 126)
    WHITE = MyColors(255, 255, 255)

    STANDARD_TEXT = BLUE
    SECONDARY_TEXT = TEAL
    BRIGHT_TEXT = BRIGHT_BLUE
    DARK_TEXT = DARK_BLUE
    SECONDARY_DARK_TEXT = DARK_TEAL
    WHITE_TEXT = WHITE
    BLACK_TEXT = BLACK

    STANDARD_BORDER = BLUE
    BRIGHT_BORDER = BRIGHT_BLUE
    DARK_BORDER = DARK_BLUE
    SECONDARY_DARK_BORDER = DARK_TEAL

    BLACK_BACKGROUND = BLACK
    DARK_BACKGROUND = BLACK_BLUE


# TODO: Add right click 'skip to here'
class NoScrollTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def wheelEvent(self, event):  # override to disable scrolling
        return True


class InputLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.gui_lost_focus = True  # Controls whether we need to switch to attempt auto switch to japanese or not...

    def event(self, cur_event):
        if type(cur_event) is QKeyEvent:
            if cur_event.key() == Qt.Key.Key_Tab:  # tab key
                return True  # Intentionally remove functionality
        return super().event(cur_event)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        if self.gui_lost_focus:
            Timer(.25, change_to_japanese).start()
            self.gui_lost_focus = False

    def focusOutEvent(self, event):
        if self.parent:
            self.parent.ignore_key_lock = True
        super().focusOutEvent(event)

    def set_gui_lost_focus(self):
        if self.parent:
            self.parent.ignore_key_lock = True
        self.gui_lost_focus = True


def set_font_size(q_widget, size):
    f = q_widget.font()
    f.setPointSize(size)
    q_widget.setFont(f)


def get_style_sheet():
    style_sheets = ("QMainWindow {"
                    "       background-color: darkgray;"
                    "       border: 1px solid black;"
                    "}"
                    "QListWidget {"
                    "       border: 1px solid " + COLORS.DARK_BORDER.as_string() + "; "
                    "       color: " + COLORS.STANDARD_TEXT.as_string() + "; "
                    "}"
                    "QTextEdit {"
                    "       border: 1px solid " + COLORS.DARK_BORDER.as_string() + "; "
                    "       color: " + COLORS.STANDARD_TEXT.as_string() + "; "
                    "}"
                    "QTableView {"
                    "       border: 1px solid " + COLORS.DARK_BORDER.as_string() + "; "
                    "       color: " + COLORS.STANDARD_TEXT.as_string() + "; "
                    "}"  
                    "QTableView::item {"
                    "       border: 1px solid " + COLORS.DARK_BORDER.as_string() + "; "
                    "       color: " + COLORS.STANDARD_TEXT.as_string() + "; "
                    "}"  
                    "QHeaderView {"
                    "       border: 1px solid " + COLORS.DARK_BORDER.as_string() + "; "
                    "       color: " + COLORS.STANDARD_TEXT.as_string() + "; "
                    "}"                                                       
                    "QHeaderView::section {"
                    "       border: 1px solid " + COLORS.DARK_BORDER.as_string() + "; "
                    "       color: " + COLORS.STANDARD_TEXT.as_string() + "; "
                    "       background-color: " + COLORS.BLACK_BACKGROUND.as_string() + "; "
                    "}"                                                         
                    "QWidget {"
                    "       color: " + COLORS.WHITE_TEXT.as_string() + "; "
                    "       background-color: " + COLORS.BLACK_BACKGROUND.as_string() + "; "
                    "}"
                    "QTabWidget::pane {"
                    "       border: 1px solid " + COLORS.DARK_BORDER.as_string() + "; "
                    "       color: " + COLORS.BLACK_TEXT.as_string() + "; "
                    "}"                                      
                    "QTabBar {"
                    "       border: 1px solid transparent; "
                    "       color: " + COLORS.BLACK_TEXT.as_string() + "; "
                    "}"
                    "QLineEdit {"
                    "       border: 1px solid transparent; "
                    "       color: " + COLORS.BRIGHT_TEXT.as_string() + "; "
                    "}"
                    "QLabel {"
                    "       border: 1px solid transparent; "
                    "       color: " + COLORS.STANDARD_TEXT.as_string() + "; "
                    "}"
                    "QTabBar::tab {"
                    "       border: 1px solid " + COLORS.SECONDARY_DARK_BORDER.as_string() + "; "
                    "       color: " + COLORS.SECONDARY_DARK_TEXT.as_string() + "; "
                    "}"
                    "QTabBar::tab::selected {"
                    "       border: 1px solid " + COLORS.STANDARD_BORDER.as_string() + "; "
                    "       color: " + COLORS.STANDARD_TEXT.as_string() + "; "
                    "}"
                    "QMenu {"
                    "       border: 3px solid " + COLORS.DARK_BORDER.as_string() + "; "
                    "}"
                    "QMenu::item {"
                    "       border: 3px solid transparent; "
                    "       color: " + COLORS.WHITE_TEXT.as_string() + "; "
                    "}"
                    "QMenu::item:selected {"
                    "       color: " + COLORS.BRIGHT_TEXT.as_string() + "; "
                    "       background-color: " + COLORS.DARK_BACKGROUND.as_string() + "; "
                    "}"
                    "QMenu::item {"
                    "       color: " + COLORS.WHITE_TEXT.as_string() + "; "
                    "       background-color: " + COLORS.BLACK_BACKGROUND.as_string() + "; "
                    "}"
                    "QPushButton {"
                    "       min-height: 20px; "
                    "       min-width: 50px; "
                    "       background-color: " + COLORS.DARK_BACKGROUND.as_string() + "; "
                    "       border: 2px solid " + COLORS.BRIGHT_BORDER.as_string() + "; "
                    "       color: " + COLORS.BRIGHT_TEXT.as_string() + "; "
                    "}"
                    "QPushButton:Disabled {"
                    "       background-color: " + COLORS.DARK_BACKGROUND.as_string() + "; "
                    "       border: 2px solid " + COLORS.SECONDARY_DARK_BORDER.as_string() + "; "
                    "       color: " + COLORS.SECONDARY_DARK_TEXT.as_string() + "; "
                    "}"
                    "QPushButton:hover:!pressed {"
                    "       background-color: " + COLORS.DARK_BACKGROUND.as_string() + "; "
                    "       border: 2px solid " + COLORS.STANDARD_BORDER.as_string() + "; "
                    "       color: " + COLORS.BRIGHT_TEXT.as_string() + "; "
                    "}"
                    "QPushButton:pressed {"
                    "       background-color: " + COLORS.DARK_BACKGROUND.as_string() + "; "
                    "       border: 2px solid " + COLORS.STANDARD_BORDER.as_string() + "; "
                    "       color: " + COLORS.STANDARD_TEXT.as_string() + "; "
                    "}"
                    )
    return style_sheets


def main():
    change_to_japanese()


if __name__ == '__main__':
    main()
