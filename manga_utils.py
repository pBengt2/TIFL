import mokuro as mok
import file_utils
import os

mp = mok.MangaPageOcr()
MANGA_DIR = r"F:/Manga/new/Temp/"
TODO_DEST_DIR = r"F:/Python/vampaJP/Manga/"

DEBUG_PRINT = True


def scan_img_text(img_file):
    res = mp(img_path=img_file)

    lines = ""
    for block in res['blocks']:
        for line in block['lines']:
            lines += line + "\n"

    return lines


def scan_manga_directory(manga_directory):
    chapters = file_utils.get_directory_list(manga_directory)
    for chapter in chapters:
        cur_directory = str(os.path.join(manga_directory, chapter))
        files = file_utils.get_file_list(cur_directory, ".jpg")
        txt_directory = str(cur_directory+"/TXT/")
        for cur_file in files:
            txt_file = os.path.join(txt_directory, cur_file.split(".")[0]+".txt")
            if not os.path.isfile(txt_file):
                if DEBUG_PRINT:
                    print(txt_file)
                lines = scan_img_text(os.path.join(cur_directory, cur_file))
                file_utils.save_txt_file(txt_file, lines)


def add_manga_directory(manga_directory):
    dest_dir = TODO_DEST_DIR+manga_directory.split("/")[-2] + r"/"
    file_utils.copy_directory(manga_directory, dest_dir)
    scan_manga_directory(dest_dir)


def main():
    add_manga_directory(MANGA_DIR)


if __name__ == '__main__':
    main()
