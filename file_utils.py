import json
import os
import shutil

DEFAULT_TXT_FILE = r"dummy_input.txt"

JSON_SAVED_DATA = r"Data/saved.json"  # 'book_dict' { 'filename' { 'index', 'total_chars', 'saved_chapter', 'saved_page' }: , vocab_list: [vocab], last_open_file: filename, last_date: date_string
VOCAB_USES_DATA = r"Data/vocab_uses.json"  # 'books' : [book], 'vocab' : { filename : [index] }
VOCAB_SENTENCES_DATA = r"Data/vocab_sentences.json"  # vocab : [sentences]
VOCAB_QUIZ_DATA = r"Data/vocab_quiz.json"  # vocab : { 'definitions', 'verb_type' }
VOCAB_STATS_DATA = r"Data/vocab_stats.json"  # 'vocab': { 'correct', 'incorrect', 'in_a_row' }
VOCAB_RUSH_DATA = r"Data/vocab_rush.json"  # vocab: { 'correct', 'incorrect', 'in_a_row', 'last_date' }


def get_file_list(directory, ext=None):
    if ext is None:
        return [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    return [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f)) and f.lower().endswith(ext.lower())]


def get_directory_list(directory):
    return [f for f in os.listdir(directory) if f is not None and os.path.isdir(os.path.join(directory, f))]


def copy_directory(src, dest):
    shutil.copytree(src, dest, dirs_exist_ok=True)


def read_txt_file(filename):
    try:
        text_file = open(filename, "r", encoding="utf8")
    except FileNotFoundError:
        print("file not found : " + filename)
        return ""
    except TypeError:
        print("invalid text file name : " + str(filename))
        return ""
    data = text_file.read()
    data = data.replace("\n", "")
    data = data.replace('\u3000', "").replace('\t', "")
    data = data.replace(' ', '')
    data = data.replace('．．．', '。')
    data = data.replace('．．', '。')
    data = data.replace('♥', '。')
    data = data.replace('♡', '。')
    text_file.close()
    return data


def create_directory_if_needed(filename):
    if not os.path.exists(filename.rsplit(r'/', 1)[0]):
        os.makedirs(filename.rsplit(r'/', 1)[0])


def save_txt_file(filename, text):
    create_directory_if_needed(filename)
    with open(filename, "w", encoding="utf8") as f:
        f.write(text)


def save_json_data(filename, data):
    create_directory_if_needed(filename)
    with open(filename, "w") as data_file:
        json.dump(data, data_file, indent=2, ensure_ascii=False)


def load_json(filename):
    try:
        with open(filename, "r") as read_file:
            data = json.load(read_file)
            return data
    except FileNotFoundError:
        print("json not found : " + filename)
        return {}


def read_key(data, key, default_val=None):
    try:
        return data[key]
    except KeyError:
        return default_val
