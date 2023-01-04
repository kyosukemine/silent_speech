import os
import glob
import subprocess

# 変換するディレクトリのパス
dir_path = "./EMG_data"

# ディレクトリ内のファイルのリストを取得する
flac_files = glob.glob("./EMG_data/**/*.flac", recursive=True)

# ファイルを1つずつ処理する
for flac_file in flac_files:
    # 拡張子がflacであるファイルだけ処理する
    # flacファイルのパス
    dir_path, file_name = os.path.split(flac_file)
    print(dir_path, file_name)
    save_dir = os.path.join("./create_textgrid_jp", dir_path[2:])
    wav_path = os.path.join(save_dir, file_name[:-5] + ".wav")
    os.makedirs(save_dir, exist_ok=True)
    if os.path.exists(wav_path):
        continue
    # ffmpegを使用してflacをwavに変換する
    subprocess.run(["ffmpeg", "-i", flac_file, wav_path])
