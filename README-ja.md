# *macls.py*

外部依存のない単一ファイルのPython 3スクリプトで、macOSの `ls` をそのまま置き換えられるカラー表示版です。

English version: [README.md](README.md).

## 特徴

### 更新日時のグラデーション

標準の `ls` はファイルの種類でファイル名を色分けしますが、*macls.py* は実際に最近変更されたかどうかで色分けします: 名前の**前景色**が更新日時の新しさに応じたグラデーションでフェードします(触ったばかりのファイルは明るく、何ヶ月も開いていないファイルは暗く)。

<p align="center">
  <img src="docs/screenshots/macls-gradation.png" alt="macls.py coloring filenames by how recently each was modified, from vivid magenta down to gray" width="420">
</p>

すべての名前は「5分 / 30分 / 1時間 / 2時間 / 1日 / 1週間 / 1ヶ月 / それ以上」という更新日時の新しさで色分けされるので、`-t` を使ったりタイムスタンプを頭の中で比較したりしなくても、今まさに編集中のファイルが一目でわかります。

### Finder タグを背景色に

Finderでファイルにタグを付けると、ターミナルにもそれが反映されます:

- `--tag=bg`(既定)では、最も新しく付けたタグの色がエントリの背景色になります。他にもタグがあれば、名前の後ろに小さなドットで表示されます。
- `--tag=dot` では背景色は使わず、すべてのタグが名前の後ろに小さなドットとして表示されます。
- `--tag=str` では、すべてのタグ名が `report.pdf [Work, Urgent]` のように角括弧付きのリストとして名前の後ろに表示され、各タグの色で色付けされます。

<p align="center">
  <img src="docs/screenshots/macls-tags.png" alt="Finder-tagged files shown with their tag color as background" width="360">
</p>

### 崩れないコンパクトな複数列表示

通常の `ls -C` は、一覧内で最も長い1つの名前に合わせて全列の幅を揃えるため、長いファイル名が1つあるだけで表示全体が1列に近いところまで崩れてしまいます。*macls.py* の既定である `--columns=compact` では、長いファイル名は自分の分だけ複数の列スロットにまたがらせ、残りの列は詰めたまま保ちます。

| `--columns=classic` | `--columns=compact` |
|---|---|
| <img src="docs/screenshots/macls-classic.png" alt="classic column layout collapsing to one column because of a long filename" width="330"> | <img src="docs/screenshots/macls-compact.png" alt="compact column layout keeping two columns despite the long filename" width="330"> |

### 縞模様の列

`--stripe` は列(`-l`/`-1` では行)を交互に色分けし、横に広い一覧でも1行ずつ追いやすくします。`--columns=compact` のレイアウトにも対応しており、複数の列スロットにまたがるエントリでも、開始位置の列を基準に1つの帯として縞模様が付きます。

<p align="center">
  <img src="docs/screenshots/macls-stripe.png" alt="Alternating column stripe background" width="520">
</p>


### インライン画像サムネイル(iTerm2)

`-I` を指定すると、画像ファイル(`.png`、`.jpeg`、`.pdf` など)の名前の横に、iTerm2のインライン画像プロトコルを使ってサムネイルが表示されます。`open` や別のビューアーは不要です。Word/Excel/PowerPointファイル(`.docx`/`.xlsx`/`.pptx`、および旧形式の`.doc`/`.xls`/`.ppt`)もmacOSのQuick Look経由で実際のプレビューが表示されます。

`--scale` オプションでサムネイルを拡大できますが、これが効くのは `-1` または `-l` のときだけで、複数列表示では無視されます。

<p align="center">
  <img src="docs/screenshots/macls-images.png" alt="Alternating column stripe background" width="520">
</p>

### クリック可能なファイル名

*macls.py* が表示するすべてのファイル名は、その `file://` URLへのハイパーリンクになっています。Cmdクリックで Finder から開けます(iTerm2のみ)。

iTerm2では、ハイパーリンクであることを示す下線付きでファイル名が表示されます。この下線はiTerm2の設定(Settings > Advanced > Underline OSC 8 hyperlinks)でオフにできます。

### 末尾記号の色付け

`--suffix-color=type` は、`-F` 指定時に付く `/ @ * = |` の種別記号をファイル種別ごとの色で表示します。

<p align="center">
  <img src="docs/screenshots/macls-suffix-color.png" alt="Suffix coloring" width="520">
</p>

### クォート表示

`--quote` は、スペースやシェルの特殊文字を含む名前をシェルセーフなクォートで囲んで表示するので、一覧をそのままコマンドラインに貼り付けられます。

<p align="center">
  <img src="docs/screenshots/macls-quotes.png" alt="Quote filenames" width="520">
</p>

### 導入も簡単

*macls.py* は単一のPythonファイルとして実装されています。外部モジュールもコンパイルも不要です。`macls.py` を `PATH` の通ったディレクトリに置くだけで動きます。

### その他

- `-B` でディレクトリ名を太字表示
- `--group-directories-first` でディレクトリを先に表示
- `--theme`/`--base-fg` でグラデーションを明背景/暗背景向けに調整
- サポートしていないオプションが渡された場合は、そのまま標準の `ls` にフォールバック

## 必要環境

- Python 3.9+(最近のmacOS標準の `/usr/bin/python3` で動作するはずです)
- macOS(Finder タグと `-I` サムネイルはmacOS/iTerm2専用。基本的な一覧表示と色付けはLinux(WSL2含む)でも動作します)
- [iTerm2](https://iterm2.com/) 推奨(`-I` サムネイルとクリック可能なファイル名のため)

## インストール

```bash
chmod +x macls.py
```

`PATH` の通った場所に配置するか、シェルの設定ファイルにエイリアスを追加してください:

```bash
alias ls='/path/to/macls.py -BF --stripe --suffix-color=type --fg-mode=date --tag=bg --quote'
```

## 使い方

```bash
./macls.py
./macls.py -la ~/Desktop
./macls.py -I -1 --scale=2 ~/Pictures
./macls.py --stripe --tag=str
```

全オプション・色の詳細なリファレンス: **[macls.md](macls.md)**。

## しくみ

ディレクトリの列挙・ソートと `-l` のロング形式出力は、システムの `ls(1)` に委譲しているため、実際の `ls` の挙動から乖離しません。それ以外——Finderタグの取得、更新日時による色付け、表示幅計算、複数列レイアウト——はすべて外部プロセスやサードパーティ製パッケージなしの純粋なPython 3で実装されています。

## 謝辞

このプログラムの大部分は [Claude Code](https://claude.com/claude-code) によって書かれました。


## ライセンス

MIT — [LICENSE](LICENSE) を参照してください。
