import re
import sys
import random
from datetime import date

from PySide6.QtWidgets import QApplication  # TODO: Refactor to use pyside_utils

import file_utils
import jp_utils
import pyside_utils


PRINT_WRONG_VOCAB = True  # TODO: Should be in GUI somehow instead...


def load_data():
    data = file_utils.load_json(file_utils.JSON_SAVED_DATA)
    book_dict = file_utils.read_key(data, "book_dict", {file_utils.DEFAULT_TXT_FILE: 0})
    vocab_list = file_utils.read_key(data, "vocab_list", [])

    return book_dict, vocab_list


class VocabRushData:
    def __init__(self, load=True):
        self.loaded_data = load
        if load:
            self.vocab_data = file_utils.load_json(file_utils.VOCAB_RUSH_DATA)
        else:
            self.vocab_data = {}
        # 'correct', 'incorrect', 'in_a_row', 'last_date'

    def get_total_correct(self, vocab):
        try:
            return file_utils.read_key(self.vocab_data[vocab], 'correct', 0)
        except KeyError:
            return 0

    def get_total_incorrect(self, vocab):
        try:
            return file_utils.read_key(self.vocab_data[vocab], 'incorrect', 0)
        except KeyError:
            return 0

    def get_in_a_row(self, vocab):
        try:
            return file_utils.read_key(self.vocab_data[vocab], 'in_a_row', 0)
        except KeyError:
            return 0

    def get_last_date(self, vocab):
        try:
            return file_utils.read_key(self.vocab_data[vocab], 'last_date', None)
        except KeyError:
            return "0-0-0"

    def get_priority(self, vocab):
        # TODO: Update priority function...
        data = file_utils.read_key(self.vocab_data, vocab, None)
        if data is None:
            return 100.0
        c = data['correct']
        i = data['incorrect']
        r = data['in_a_row']
        d = data['last_date']

        if c < 10 or i > c or d == "0-0-0" or r < 5:
            return 100.0
        elif r > 20:
            return 1.0
        elif r > 50:
            return .1
        elif r > 100:
            return .001

        return 50.0

    def _set_vocab_to_default(self, vocab):
        self.vocab_data[vocab] = {'correct': 0, 'incorrect': 0, 'in_a_row': 0, 'last_date': "0-0-0"}

    def mark_correct(self, vocab):
        try:
            self.vocab_data[vocab]['correct'] += 1
            self.vocab_data[vocab]['in_a_row'] += 1
            self.vocab_data[vocab]['last_date'] = str(date.today())
        except KeyError:
            self._set_vocab_to_default(vocab)
            self.vocab_data[vocab]['correct'] = 1
            self.vocab_data[vocab]['in_a_row'] = 1
            self.vocab_data[vocab]['last_date'] = str(date.today())

    def mark_incorrect(self, vocab):
        try:
            if self.get_in_a_row(vocab) < 0:
                self.vocab_data[vocab]['in_a_row'] -= 1
            else:
                self.vocab_data[vocab]['in_a_row'] = -1
        except KeyError:
            self._set_vocab_to_default(vocab)
            self.vocab_data[vocab]['in_a_row'] -= 1
        self.vocab_data[vocab]['incorrect'] += 1

    def update_vocab_rush_data(self):
        if self.loaded_data:
            print("Attempting to update vocab rush data from loaded data...")
            return

        combined_data = file_utils.load_json(file_utils.VOCAB_RUSH_DATA)

        debug_print = False
        if debug_print:
            self.print_vocab_data(combined_data)

        for k, v in self.vocab_data.items():
            try:
                combined_data[k]['correct'] += v['correct']
                combined_data[k]['incorrect'] += v['incorrect']

                if v['in_a_row'] < 0:
                    combined_data[k]['in_a_row'] = v['in_a_row']
                else:
                    # TODO: Minor bug... if loaded in_a_row is negative, but new is positive, should set to new instead of add
                    combined_data[k]['in_a_row'] += v['in_a_row']

                combined_data[k]['last_date'] = v['last_date']
            except KeyError:
                combined_data[k] = v

        combined_data.pop("")
        file_utils.save_json_data(file_utils.VOCAB_RUSH_DATA, combined_data)

        if debug_print:
            self.vocab_data.pop("")
            self.print_vocab_data(combined_data)
            self.print_vocab_data(self.vocab_data)

    @staticmethod
    def print_vocab_data(data):
        correct_list = [(k, v['correct']) for k, v in data.items()]
        correct_list.sort(key=lambda x: x[1])
        incorrect_list = [(k, v['incorrect']) for k, v in data.items()]
        incorrect_list.sort(key=lambda x: x[1])
        in_a_row_list = [(k, v['in_a_row']) for k, v in data.items()]
        in_a_row_list.sort(key=lambda x: x[1])
        date_list = [(k, v['last_date']) for k, v in data.items()]
        date_list.sort(key=lambda x: x[1])  # TODO: Dates currently include None
        print(correct_list)
        print(incorrect_list)
        print(in_a_row_list)
        print(date_list)


def update_vocab_quiz_stats(correct_vocab, wrong_vocab):
    finalized_correct_vocab = []
    for vocab in correct_vocab:
        if vocab not in wrong_vocab and vocab != "":
            finalized_correct_vocab.append(vocab)

    total_stats = file_utils.load_json(file_utils.VOCAB_STATS_DATA)

    for v in finalized_correct_vocab:
        try:
            total_stats[v]
        except KeyError:
            total_stats[v] = {"correct": 0, "incorrect": 0, "in_a_row": 0}
        total_stats[v]["correct"] += 1
        total_stats[v]["in_a_row"] += 1

    for v in wrong_vocab:
        try:
            total_stats[v]
        except KeyError:
            total_stats[v] = {"correct": 0, "incorrect": 0, "in_a_row": 0}
        total_stats[v]["incorrect"] += 1
        total_stats[v]["in_a_row"] = 0

    if PRINT_WRONG_VOCAB:
        print(wrong_vocab)

    file_utils.save_json_data(file_utils.VOCAB_STATS_DATA, total_stats)


def find_word(book, word):
    try:
        text = file_utils.read_txt_file(book)
    except FileNotFoundError or PermissionError:
        print("Error reading book: " + str(book))
        return []
    indices = [m.start() for m in re.finditer(word, text)]
    return indices


def get_book_list(book_dict):
    return list(book_dict.keys())


def update_vocab_uses_dict(vocab_uses_dict):
    try:
        vocab_dict = vocab_uses_dict['vocab']
        read_books_list = vocab_uses_dict['books']
    except KeyError:
        vocab_dict = {}
        read_books_list = []

    book_dict, vocab_list = load_data()
    book_list = get_book_list(book_dict)

    # Update new vocab with every book
    for vocab in vocab_list:
        try:
            vocab_dict[vocab]
        except KeyError:
            vocab_dict[vocab] = {}
            for book in book_list:
                indices = find_word(book, vocab)
                if len(indices) > 0:
                    vocab_dict[vocab][book] = indices

    # Update old vocab with only new books
    for book in book_list:
        if book not in read_books_list:
            read_books_list.append(book)
            for vocab in vocab_list:
                indices = find_word(book, vocab)
                if len(indices) > 0:
                    vocab_dict[vocab][book] = indices

    vocab_uses_dict['books'] = read_books_list
    vocab_uses_dict['vocab'] = vocab_dict
    file_utils.save_json_data(file_utils.VOCAB_USES_DATA, vocab_uses_dict)


def is_end_char(c):
    if c == '.' or c == '。' or c == '!' or c == '！' or c == '？' or c == '…':
        return True
    return False


def get_sentence(text, index):
    i_start = index
    i_end = index

    while i_start > 0 and not is_end_char(text[i_start-1]):
        i_start -= 1

    if text[i_start] == " " or text[i_start] == '\u3000':
        i_start += 1
    while i_end < len(text) and not is_end_char(text[i_end]):
        i_end += 1
    i_end += 1
    if i_end >= len(text):
        i_end = len(text) - 1

    return text[i_start:i_end]


def find_sentences(word_dict, word):
    book_dict = word_dict[word]
    for book in list(book_dict.keys()):
        if len(book_dict[book]) > 0:
            text = file_utils.read_txt_file(book)
            sentences = []
            for i in book_dict[book]:
                sentences.append(get_sentence(text, i))
            return sentences
    return []


def update_sentences_dict(word_dict):
    sentences_dict = {}
    for key in list(word_dict.keys()):
        sentences = find_sentences(word_dict, key)
        sentences_dict[key] = sentences

    file_utils.save_json_data(file_utils.VOCAB_SENTENCES_DATA, sentences_dict)
    return sentences_dict


def update_all():
    vocab_uses_dict = file_utils.load_json(file_utils.VOCAB_USES_DATA)
    update_vocab_uses_dict(vocab_uses_dict)
    update_sentences_dict(vocab_uses_dict['vocab'])


class VocabQuizGui(pyside_utils.QuizGui):
    def __init__(self, parent=None, number_of_vocab=-1, prioritize=False, save_stats=True):
        self.vocab_stats = file_utils.load_json(file_utils.VOCAB_STATS_DATA)
        super().__init__(parent, number_of_questions=number_of_vocab, prioritize=prioritize, save_stats=save_stats)

    def save_data(self, b_force=False):
        if self.save_stats:
            update_vocab_quiz_stats(self.correct_questions, self.wrong_questions)

    def sorting_priority(self, vocab):
        scalar = random.triangular(1, 100)
        try:
            stats = self.vocab_stats[vocab]
            c = stats["correct"]
            i = stats["incorrect"]
            r = stats["in_a_row"]
            t = c+i
            if t == 0:
                return 100 * 10 * scalar
            p_val = 100 * i / t
            p_val = p_val * max(1, 10 - r)
            p_val = p_val * scalar
            return p_val
        except KeyError:
            return 100 * 10 * scalar


class VocabRushGui(pyside_utils.QuizGui):

    def __init__(self, parent=None, prioritize=False, save_stats=True):
        self.current_vocab_rush_data = VocabRushData(False)
        self.vocab_rush_data = VocabRushData()
        self.vocab_rush_extras = []
        self.vocab_rush_current_wrong = False
        self.vocab_rush_is_retry = False

        super().__init__(parent, number_of_questions=-1, prioritize=prioritize, save_stats=save_stats)

    def save_data(self, b_force=False):
        if self.save_stats:
            self.current_vocab_rush_data.update_vocab_rush_data()

    def sorting_priority(self, vocab):
        return self.vocab_rush_data.get_priority(vocab)

    def vocab_rush_incorrect(self):
        for i in range(3):
            self.vocab_rush_extras.append([self.current_question, self.current_answers])
        self.vocab_rush_current_wrong = True
        self.bottom_text.setText(str(len(self.vocab_rush_extras)))

    def vocab_rush_match(self):
        if self.vocab_rush_is_retry:
            return

        if self.vocab_rush_current_wrong:
            self.vocab_rush_current_wrong = False
            self.current_vocab_rush_data.mark_incorrect(self.current_question)
            return

        self.current_vocab_rush_data.mark_correct(self.current_question)

    def ctrl_pressed(self):
        pyside_utils.QuizGui.ctrl_pressed(self)
        self.vocab_rush_incorrect()

    def input_line_is_changed(self):
        txt = self.input_line.displayText()
        if self.current_question == txt:
            self.vocab_rush_match()
            if self.current_question not in self.wrong_questions:
                self.correct_questions.append(self.current_question)
            self.setup_next_problem()

    def setup_questions(self, question_list):
        updated_question_list = question_list
        # Currently putting more copies of higher priority words in question list...
        if self.prioritize:
            num_vocab = len(updated_question_list)
            # Duplicate higher priority words...
            for i in range(num_vocab):
                num_dup = int((num_vocab - i) / num_vocab * 5)
                for j in range(num_dup):
                    updated_question_list.append(updated_question_list[i])
            random.shuffle(updated_question_list)

        for v in updated_question_list:
            spellings, meanings = self.get_vocab_data(v)
            self.quiz_problems.append([v, spellings])

    def get_vocab_rush_problem(self):
        if len(self.vocab_rush_extras) > 50 or (len(self.vocab_rush_extras) > 10 and bool(random.getrandbits(1))):
            self.vocab_rush_is_retry = True
            random.shuffle(self.vocab_rush_extras)
            return self.vocab_rush_extras.pop()

        self.vocab_rush_is_retry = False
        index = random.randint(0, len(self.quiz_problems)-1)
        return self.quiz_problems[index]

    def setup_next_problem(self):
        if len(self.quiz_problems) == 0:
            self.quiz_complete()
            return

        prob = self.get_vocab_rush_problem()
        self.bottom_text.setText(str(len(self.vocab_rush_extras)))
        self.current_question = prob[0]
        self.current_answers = prob[1]

        self.input_line.clear()
        self.main_text.setText(self.current_question)
        self.auto_resize()


class ConjugationRushGui(pyside_utils.QuizGui):

    def __init__(self, parent=None, prioritize=False, save_stats=True, max_conj=-1):
        self.max_conj = max_conj
        self.verb_map = {}
        super().__init__(parent, number_of_questions=-1, prioritize=prioritize, save_stats=save_stats)

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

    def get_definitions(self):
        definitions_string = ""
        for d in self.quiz_data[self.verb_map[self.current_question]]['definitions']:
            definitions_string += d.split(':', 1)[0].split(' (')[0]
            definitions_string += "\n" + d.split(": ")[1][0:70]
        return definitions_string

    @staticmethod
    def _get_readable_string(verb_type, b, t, p):
        temp_str = ""
        if p == "neg":
            temp_str += "neg_"
        if t == "past":
            temp_str += "past_"
        if b == "pla":
            pass
        elif b == "pol":
            temp_str += "polite"
        elif b == "te":
            temp_str += "te"  #
        elif b == "ta":
            temp_str += "ta"  # 'plain past affirmative'
        elif b == "tari":
            temp_str += "tari"  # list
        elif b == "cond":
            temp_str += "conditional"  # hypothetical / 'tara-form'
        elif b == "vol":
            temp_str += "volitional"  # Suggestion, ie: 'let's eat'
        elif b == "pot":
            temp_str += "potential"  # ability / possibility to do, ie 'can eat'
        elif b == "imp":
            temp_str += "imperative"  # order / command
        elif b == "prov":
            temp_str += "provisional"  # uncertainty / hypothetical / "ba-form"
        elif b == "caus":
            temp_str += "causative"  # forced / allowed to do action
        elif b == "pass":
            temp_str += "passive"  # 'was done to' ie, 'was eaten'
        else:
            temp_str += b
        temp_str += ":" + verb_type.split(".")[-1]
        return temp_str

    @staticmethod
    def _get_conj_complexity(b, t, p):
        cur_conj = 0
        if p == "neg":
            cur_conj += 1
        if t == "past":
            cur_conj += 1
        if b not in ["pla", "pol"]:
            cur_conj += 1
        return cur_conj

    def setup_questions(self, question_list):
        verb_list = [q for q in question_list if self.quiz_data[q]['verb_type'] != "None"]

        forms = {}  # conj_form, {verb_type, conj_list}
        for word in verb_list:
            verb_type = self.quiz_data[word]['verb_type']
            base_forms = ["pla", "pol", "te", "ta", "tari", "cond", "vol", "pot", "imp", "prov", "caus", "pass"]
            tenses = ["nonpast", "past"]
            polarity = ["pos", "neg"]

            for b in base_forms:
                for t in tenses:
                    for p in polarity:
                        conj_form = jp_utils.conj_verb(word, verb_type, b, t, p)
                        if conj_form is not None:
                            try:
                                self.verb_map[conj_form]
                            except KeyError:
                                self.verb_map[conj_form] = word
                            temp_str = self._get_readable_string(verb_type, b, t, p)
                            try:
                                forms[conj_form].append(temp_str)
                                forms[conj_form][0] = min(self._get_conj_complexity(b, t, p), forms[conj_form][0])
                            except KeyError:
                                forms[conj_form] = [self._get_conj_complexity(b, t, p), temp_str]

        keys = list(forms.keys())
        random.shuffle(keys)
        for k in keys:
            if forms[k][0] <= self.max_conj:
                self.quiz_problems.append([k, forms[k][1:]])


def vocab_quiz(number_of_vocab=-1, prioritize=False, save_stats=True):
    window = VocabQuizGui(number_of_vocab=number_of_vocab, prioritize=prioritize, save_stats=save_stats)
    window.show()
    return window


def vocab_rush(prioritize=False, save_stats=True):
    window = VocabRushGui(prioritize=prioritize, save_stats=save_stats)
    window.show()
    return window


def conj_rush(prioritize=False, save_stats=True, max_conj=1):
    window = ConjugationRushGui(prioritize=prioritize, save_stats=save_stats, max_conj=max_conj)
    window.show()
    return window


def test_vocab_quiz():
    number_of_vocab = 10
    prioritize = True
    save_stats = False

    app = QApplication(sys.argv)
    window = vocab_quiz(number_of_vocab, prioritize, save_stats)
    window.show()
    app.exec_()


def test_vocab_rush():
    prioritize = False
    save_stats = False

    app = QApplication(sys.argv)
    window = vocab_rush(prioritize, save_stats)
    window.show()
    app.exec_()


def test_conjugation_rush():
    prioritize = False
    save_stats = False

    app = QApplication(sys.argv)
    window = conj_rush(prioritize, save_stats, 1)
    window.show()
    app.exec_()


def main():
    # test_vocab_quiz()
    # test_vocab_rush()
    test_conjugation_rush()


if __name__ == '__main__':
    main()
