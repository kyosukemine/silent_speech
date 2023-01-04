import glob
import json
import os
import pykakasi
import re
import csv
import subprocess
import regex
kks = pykakasi.kakasi()
kanji = regex.compile(r'[\p{Script=Han}ヶ々^《》]+')


dir_path = "./EMG_data/"
json_files = glob.glob(dir_path + "**/*.json", recursive=True)
with open("./create_textgrid_jp/emotion.csv", "r") as f:
    csv_reader = csv.reader(f)
    emotino_orig_to_kata = {}
    for r in csv_reader:
        # print(r)
        # break
        emotino_orig_to_kata[r[0]] = r[1]
# print(emotino_orig_to_kata)
# exit()


def main():
    for json_file in json_files:
        if "silent" in json_file:
            continue
        if "test" in json_file:
            continue
        if not "kokoro" in json_file:
            continue
        # if not "102/20221212/kokoro/voiced/0/36" in json_file:
        #     continue
        dir_path, file_name = os.path.split(json_file)
        # print(dir_path, file_name)
        flac_path = os.path.join(dir_path, file_name[:-9] + "audio.flac")
        save_dir = os.path.join("./create_textgrid_jp", dir_path[2:])
        wav_path = os.path.join(save_dir, file_name[:-9] + "audio.wav")
        txt_path = os.path.join(save_dir, file_name[:-9] + "audio.txt")
        inf_path = os.path.join(save_dir, file_name[:-9] + "audio.info")

        with open(json_file, "r") as f:
            json_data = json.load(f)

        text = json_data["text"]
        if text == "":
            continue
        # # re.sub("\(.+?\)", "", text)
        # text = re.sub("\《.+?\》", "", text)
        # result = kks.convert(text)
        # print(text)
        if "emotion" in json_file:
            text = emotion(text)
        elif "kokoro" in json_file:
            text = kokoro(text)
        # break
        text = text.replace("、", " sp ")
        text = text[:-1] if text[-1] == "。" else text
        text = text.replace("。", " sp ")
        text = text.replace("？", "")
        text = text.replace("―", "")
        text = text.replace("…", "")
        text = text.replace("）", "")
        text = text.replace("（", "")
        text = text.replace("んー", "ん")
        text = text.replace("Ｋ", "けー")
        text = text.replace("｜", "")

        os.makedirs(save_dir, exist_ok=True)
        with open(txt_path, "w") as f:
            f.write(text)
        with open(inf_path, "w") as f:
            f.write(json_data["text"])

        subprocess.run(["ffmpeg", "-i", flac_path, wav_path])
        subprocess.run(['perl', './create_textgrid_jp/segmentation-kit/segment_julius.pl', save_dir])
        os.remove(wav_path)
        # print(text)
        # break
    
    # アライメント結果が空のファイル名出力
    lab_files = glob.glob("./create_textgrid_jp/EMG_data/**/*.lab", recursive=True)
    for lab_file in lab_files:
        with open(lab_file, "r") as f:
            txt = f.read()
        if txt == "":
            print(lab_file)


def emotion(text: str):
    text = emotino_orig_to_kata[text]
    result = kks.convert(text)
    ret = ''.join([item['hira'] for item in result])

    return ret


def kokoro(text: str):
    # result = kks.convert(text)
    print(text)
    iter_text = iter(text[::-1])
    list_text = []
    # ふりがなが振られている漢字をひらがなに直す
    i = len(text)-1
    while i >= 0:
        # for s in iter_text:
        s = text[i]
        break_frg = False
        continue_frg = False
        if s == "》":
            i -= 1
            s = text[i]
            while not s == "《":
                list_text.append(s)
                i -= 1
                s = text[i]

            i -= 1
            s = text[i]
            while kanji.fullmatch(s):
                i -= 1
                try:
                    s = text[i]
                except IndexError:
                    break_frg = True
                    break
                if s == "｜":
                    continue_frg = True
                    break
                if s == "》":
                    continue_frg = True
                    i += 1
                    break
            if break_frg:
                break
            if continue_frg:
                continue
        list_text.append(s)
        i -= 1
    text = ''.join(list_text[::-1])
    print(text)
    text = text.replace("雑司ヶ谷", "ぞうしがや")

    result = kks.convert(text)
    # ret = []
    # iter_result = iter(result[::-1])
    # for token in iter_result:
    #     if "》" in token["orig"]:
    #         ret.append(token["orig"].replace("》", "").replace("《", ""))
    #         _token = next(iter_result)
    #         while p.fullmatch(_token["orig"]):
    #             if "｜" in _token["orig"]:
    #                 break
    #             _token = next(iter_result)
    #         token = _token
    #     ret.append(token["orig"])

    # print(ret[::-1])

    ret = ''.join([item['hira'] for item in result])
    print(ret)
    return ret
    pass


main()
