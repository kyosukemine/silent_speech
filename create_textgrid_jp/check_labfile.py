import glob

lab_files = glob.glob("./create_textgrid_jp/EMG_data/**/*.lab", recursive=True)
for lab_file in lab_files:
    with open(lab_file, "r") as f:
        txt = f.read()
    if txt == "":
        print(lab_file)
