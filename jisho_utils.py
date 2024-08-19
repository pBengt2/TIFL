from jisho_api.sentence import Sentence as Jisho


def strip_parenthesis(input_str):
    ret = ''
    skip1c = 0
    skip2c = 0
    for i in input_str:
        if i == '[':
            skip1c += 1
        elif i == '(':
            skip2c += 1
        elif i == ']' and skip1c > 0:
            skip1c -= 1
        elif i == ')' and skip2c > 0:
            skip2c -= 1
        elif skip1c == 0 and skip2c == 0:
            ret += i
    return ret


def get_jisho_sentences(word, remove_notes=True):
    txt = Jisho.request(word)
    sentences = []
    for d in txt.data:
        jp = d.japanese
        if remove_notes:
            jp = strip_parenthesis(jp)
        sentences.append(jp)
    return sentences
