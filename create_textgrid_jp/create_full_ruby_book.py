import pykakasi
import regex
kks = pykakasi.kakasi()
kanji = regex.compile(r'[\p{Script=Han}ヶ]+')

def main():
    with open("./create_textgrid_jp/kokoro_toEx.txt", "r") as f:
        book = f.readlines()
    new_book = []
    for line in book:
        orig_text = line.replace("\n", "")
        orig_text = orig_text.replace("雑司ヶ谷", "ゾウシガヤ")
        result = kks.convert(orig_text)
        result = iter(result[::-1])
        print(orig_text)
        ret = []
        for token in result:
            if "》" in token["orig"]:
                ret.append(token["orig"])
                ret.append(next(result)["orig"])

            elif not token["orig"] == token["hira"]:
                tmp = []
                hira = iter(token["hira"][::-1])
                orig = iter(token["orig"][::-1])
                h = next(hira)
                o = next(orig)
                while h == o:
                    tmp.append(o)
                    h = next(hira)
                    o = next(orig)
                tmp.append("》")
                tmp.append(h)
                while True:
                    try:
                        tmp.append(next(hira))
                    except StopIteration:
                        break
                tmp.append("《")
                tmp.append(o)
                while True:
                    try:
                        tmp.append(next(orig))
                    except StopIteration:
                        break
                ret.append(''.join(tmp[::-1]))
            else:
                ret.append(token["orig"])
        text = ''.join(ret[::-1])
        text = text.replace("｜", "")
        print(text)
        text = text.replace("ゾウシガヤ", "雑司ヶ谷")
        text = text.replace("《にん》", "《ひと》")
        new_book.append(text + "\n")

    with open("./create_textgrid_jp/kokoro_full_ruby.txt", "w") as f:
        f.writelines(new_book)


main()
