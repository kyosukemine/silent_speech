import json

# with open("./testset_largedev.json", "r") as f:
#     j = json.load(f)
#     print(len(j['test']))
#     print(len(j['dev']))


import glob

silent_dirs = glob.glob("./EMG_data/100/**/english/war/silent/**/*.json")
book_index_dict = []
for silent_dir in silent_dirs:
    # print(silent_dir)
    with open(silent_dir, "r") as f:
        j = json.load(f)
        # print(j.items())
        if j["sentence_index"] != -1:
            print(j["sentence_index"], j["text"])
            print(j["book"])
            book_index_dict.append([j["book"], j["sentence_index"]])
book_index_dict.sort()
print(book_index_dict)

split_dev_rate = 0.1

output = {"dev": book_index_dict[-2*int(len(book_index_dict)*split_dev_rate):-int(len(book_index_dict)*split_dev_rate)], "test": book_index_dict[-int(len(book_index_dict)*split_dev_rate):]}
print(output)

# with open("./testset_dev_closed.json", "w") as f:
with open("./testset_dev_open.json", "w") as f:
    json.dump(output, f, indent=4)
