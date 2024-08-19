import requests.exceptions
from nhk_easy import api as nhk_api
from jamdict import Jamdict
import MeCab

import japverbconj
from japverbconj.constants.enumerated_types import Formality, VerbClass
from japverbconj.verb_form_gen import generate_japanese_verb_by_str as verb_conj

from jisho_api.word import Word


nhk = nhk_api.Api()
JAM = Jamdict()
wakati = MeCab.Tagger("")


def get_base_form(word):
    parsed = wakati.parse(word).split(',')
    if len(parsed) > 7:
        base_form = parsed[7]  # seems like 7 is base form... TODO: Would be nice to map these out...

        debug_print = False
        if debug_print:
            print("get_base_form_debug")
            print(word)
            print(base_form)

        return base_form

    return ""


def get_sentence_components(sentence):
    parsed = wakati.parseToNode(sentence)
    components = []
    while parsed:
        components.append(parsed.surface)
        parsed = parsed.next

    if components[0] == "":
        components.pop(0)
    return components


def get_definitions(word, num_definitions=3, basic=True, recursive_call=False):
    # 'info', 'kana_forms', 'kanji_forms', 'senses', 'set_info', 'text', 'to_dict', 'to_json'
    if word is None or len(word) == 0:
        return []
    lookup_result = JAM.lookup(word)
    results = []
    num = 0
    for e in lookup_result.entries:
        if basic:
            results.append(e.text())
        else:
            results.append(str(e))
        num += 1
        if num >= num_definitions:
            break
    if len(results) == 0 and not recursive_call:
        base_word = get_base_form(word)
        if base_word != word:
            return get_definitions(get_base_form(word), num_definitions, basic, True)
    return results


def download_nhk_news():
    nhk.download_top_news(furigana=False, html_output=False, mp3=False, text=True)


def get_verb_type(word):
    # TODO: more checks for irregular (ie, other forms)
    if word == "くる" or word == "する":
        return VerbClass.IRREGULAR

    current_data = None

    i = 0
    while current_data is None and i < 20:
        try:
            current_data = Word.request(word).data
        except requests.exceptions.JSONDecodeError:
            i += 1

    if i == 20:
        print("ERR: get_verb_type(): JSONDecodeError : " + str(word))
        exit(-3784)

    for d in current_data:
        for s in d.dict()['senses']:
            if len(s['parts_of_speech']) == 0:
                continue
            cur_s = str(s['parts_of_speech'][0]).lower()
            if cur_s.startswith('godan'):
                return VerbClass.GODAN
            elif cur_s.startswith('ichidan'):
                return VerbClass.ICHIDAN

    return None


def conj_verb(verb, verb_type, base, tense, polarity):
    if verb_type == "VerbClass.ICHIDAN":
        verb_type = VerbClass.ICHIDAN
    elif verb_type == "VerbClass.GODAN":
        verb_type = VerbClass.GODAN
    elif verb_type == "VerbClass.IRREGULAR":
        verb_type = VerbClass.IRREGULAR

    try:
        return verb_conj(verb, verb_type, base, tense, polarity)
    except japverbconj.constants.exceptions.NonIrregularVerbError:
        return None
    except japverbconj.constants.exceptions.InvalidJapaneseVerbEndingError:
        return None
    except japverbconj.constants.exceptions.InvalidJapaneseVerbLengthError:
        return None


def get_all_forms(word):
    base_forms = ["pla", "pol", "te", "ta", "tari", "cond", "vol", "pot", "imp", "prov", "caus", "pass"]
    tenses = ["nonpast", "past"]
    polarity = ["pos", "neg"]

    forms = []
    v = get_verb_type(word)
    if v is None:
        return []

    for b in base_forms:
        for t in tenses:
            for p in polarity:
                try:
                    forms.append({"result": verb_conj(word, v, b, t, p), "word": word, "type": v, "base": b, "tense": t, "polarity": p})
                except japverbconj.constants.exceptions.NonIrregularVerbError:
                    print("err: " + str(v) + str(b) + str(t) + str(p))
    return forms


def get_form(word, base, tense, polarity):
    v = get_verb_type(word)
    verb_conj(word, v, base, tense, polarity)


def main():
    word = "飲む"

    forms = get_all_forms(word)
    for v in forms:
        print(v)


if __name__ == '__main__':
    main()
