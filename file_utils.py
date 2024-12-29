import json
import os
import shutil

DEFAULT_TXT_FILE = r"dummy_input.txt"


def change_current_directory(full_path):
    _create_directory_if_needed(full_path)
    os.chdir(full_path)


def _dont_delete_or_move_files():
    return [DEFAULT_TXT_FILE, "requirements.txt", "black.png", "dummy_input.txt", "readme.md", "license"]


def get_current_directory():
    return os.getcwd()


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


def move_files(directory, target_directory, file_extensions, ignore_files=None):
    _create_directory_if_needed(target_directory)
    updated_ignore_files = _dont_delete_or_move_files()
    if ignore_files is not None:
        for f in ignore_files:
            updated_ignore_files.append(f)

    to_move = get_file_list(directory, file_extensions)
    for fn in to_move:
        if fn.lower() not in updated_ignore_files:
            cur_name = directory + "/" + fn
            dest_name = target_directory + "/" + fn
            os.rename(cur_name, dest_name)


def delete_files(directory, file_extension, ignore_files=None):
    updated_ignore_files = _dont_delete_or_move_files()
    if ignore_files is not None:
        for f in ignore_files:
            updated_ignore_files.append(f)

    to_delete = get_file_list(directory, file_extension)
    for fn in to_delete:
        if fn.lower() not in updated_ignore_files:
            os.remove(fn)


def _create_directory_if_needed(filename):
    if not os.path.exists(filename.rsplit(r'/', 1)[0]):
        os.makedirs(filename.rsplit(r'/', 1)[0])


def save_txt_file(filename, text):
    _create_directory_if_needed(filename)
    with open(filename, "w", encoding="utf8") as f:
        f.write(text)


def save_json_data(filename, data):
    _create_directory_if_needed(filename)
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
