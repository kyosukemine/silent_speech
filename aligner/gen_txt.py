import json
import glob
import os

filenames = glob.glob("./text_alignments_war/**/*_audio.flac")
print(filenames)
for filename in filenames:
    with open(filename[:-10] + "info.json", "r") as f:
        j = json.load(f)
    if j["text"] == "":
        os.remove(filename)
        # os.remove(filename[:-4] + "text")
    else:
        with open(filename[:-4] + "txt", "w") as f:
            f.write(j["text"])
