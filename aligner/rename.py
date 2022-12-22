import json
import glob
import os

filenames = glob.glob("./text_alignmented_war/**/*_audio.TextGrid")
print(filenames)
for _filename in filenames:
    
    # print(os.path.split(filename)[0].split("/")[-1])
    base, filename = os.path.split(_filename)
    sess = base.split("/")[-1]
    # break

    os.rename(_filename, base + f"/{sess}_" + filename)
    # with open(filename[:-10] + "info.json", "r") as f:
    #     j = json.load(f)
    # if j["text"] == "":
    #     os.remove(filename)
    #     # os.remove(filename[:-4] + "text")
    # else:
    #     with open(filename[:-4] + "txt", "w") as f:
    #         f.write(j["text"])
