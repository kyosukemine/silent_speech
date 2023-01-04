# How to create textgrid file form japanese flac file

```bash
sudo apt-get install praat
```

1.[音素セグメンテーション]https://julius.osdn.jp/index.php?q=ouyoukit.html)
1. [juliusのインストール](https://qiita.com/ekzemplaro/items/dcfd51c24f2c3a020c7b)
2. julius音素セグメンテーションキットインストール
3. flac to wav
   1. ffmpeg必要
```
python3  convert_text_to_hiragana.py
python3 ./TextGridConverter/convert_label.py ./EMG_data
```
memo
- segmentation-kit内のsegment_julius.plを変更
  - ゔ 追加
  - てょ -> t e y o 
  - んー -> ん
- emotion対応
- kokoro対応
  - kakasiでふりがな付与
1. 発話内容作成
   1. 
2. 