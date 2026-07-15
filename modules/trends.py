"""簡易的な自然言語処理でニュースのトレンドを算出する。

外部APIやLLMは一切使わない。収集済みの記事タイトル（日英混在）を対象に、

  1. ドライバー / チーム名辞書 (gazetteer) による言及数カウント
  2. トピック用キーワード辞書によるカテゴリ集計
  3. 辞書に無い語を拾うための軽量な出現頻度解析 (カタカナ/漢字/英単語)

を行う。追加の依存ライブラリは不要で、GitHub Actions 上で確実・無料に動く。
"""

import re
from collections import Counter

# ── 別名辞書 ────────────────────────────────────────────────────────────
# (表示名, [別名...]) — 別名は日本語(部分一致)と英語(単語境界一致)を混在させてよい。
# 1記事タイトルにつき同一エンティティは最大1回だけカウントする(別名重複を防ぐ)。

_DRIVERS: list[tuple[str, list[str]]] = [
    ("Verstappen",  ["フェルスタッペン", "Verstappen"]),
    ("Hamilton",    ["ハミルトン", "Hamilton"]),
    ("Leclerc",     ["ルクレール", "Leclerc"]),
    ("Norris",      ["ノリス", "Norris"]),
    ("Piastri",     ["ピアストリ", "Piastri"]),
    ("Russell",     ["ラッセル", "Russell"]),
    ("Sainz",       ["サインツ", "Sainz"]),
    ("Alonso",      ["アロンソ", "Alonso"]),
    ("Perez",       ["ペレス", "Perez", "Pérez"]),
    ("Tsunoda",     ["角田", "Tsunoda"]),
    ("Gasly",       ["ガスリー", "Gasly"]),
    ("Ocon",        ["オコン", "Ocon"]),
    ("Stroll",      ["ストロール", "Stroll"]),
    ("Albon",       ["アルボン", "Albon"]),
    ("Hulkenberg",  ["ヒュルケンベルグ", "ヒュルケンベルク", "Hulkenberg", "Hülkenberg"]),
    ("Bottas",      ["ボッタス", "Bottas"]),
    ("Zhou",        ["周冠宇", "Zhou"]),
    ("Ricciardo",   ["リカルド", "Ricciardo"]),
    ("Lawson",      ["ローソン", "Lawson"]),
    ("Bearman",     ["ベアマン", "Bearman"]),
    ("Colapinto",   ["コラピント", "Colapinto"]),
    ("Bortoleto",   ["ボルトレート", "Bortoleto"]),
    ("Antonelli",   ["アントネッリ", "Antonelli"]),
    ("Hadjar",      ["ハジャル", "Hadjar"]),
    ("Doohan",      ["ドゥーハン", "Doohan"]),
    ("Magnussen",   ["マグヌッセン", "Magnussen"]),
]

_TEAMS: list[tuple[str, list[str]]] = [
    ("Red Bull",     ["レッドブル", "Red Bull"]),
    ("Ferrari",      ["フェラーリ", "Ferrari"]),
    ("Mercedes",     ["メルセデス", "Mercedes"]),
    ("McLaren",      ["マクラーレン", "McLaren"]),
    ("Aston Martin", ["アストンマーティン", "アストンマ", "Aston Martin"]),
    ("Alpine",       ["アルピーヌ", "Alpine"]),
    ("Williams",     ["ウィリアムズ", "Williams"]),
    ("Racing Bulls", ["レーシングブルズ", "Racing Bulls", "VCARB"]),
    ("Haas",         ["ハース", "Haas"]),
    ("Sauber",       ["ザウバー", "Sauber"]),
    ("Audi",         ["アウディ", "Audi"]),
    ("Cadillac",     ["キャデラック", "Cadillac"]),
]

# トピック: (表示ラベル, [別名...])
_TOPICS: list[tuple[str, list[str]]] = [
    ("予選・ポール",   ["予選", "ポールポジション", "ポール", "Qualifying", "pole"]),
    ("決勝・GP",       ["決勝", "グランプリ", "Grand Prix", "レースウィーク"]),
    ("スプリント",     ["スプリント", "Sprint"]),
    ("クラッシュ・事故", ["クラッシュ", "接触", "事故", "衝突", "Crash", "collision"]),
    ("ペナルティ",     ["ペナルティ", "グリッド降格", "降格", "Penalty", "penalis", "penaliz"]),
    ("契約・移籍",     ["契約", "移籍", "加入", "放出", "残留", "シート", "Contract", "signs", "signing", "deal", "transfer"]),
    ("マシン開発",     ["アップグレード", "開発", "改良", "新パーツ", "Upgrade", "development"]),
    ("タイヤ",         ["タイヤ", "ピレリ", "Tyre", "Tire", "Pirelli"]),
    ("天候・雨",       ["ウェット", "天候", "Rain", "wet"]),
    ("テスト・走行",   ["テスト", "フリー走行", "Test", "practice"]),
    ("規則・FIA",      ["レギュレーション", "規則", "ルール", "FIA", "regulation"]),
    ("表彰台",         ["表彰台", "ポディウム", "Podium"]),
    ("リタイア・トラブル", ["リタイア", "マシントラブル", "故障", "retire", "DNF"]),
    ("選手権・タイトル", ["選手権", "ランキング", "タイトル", "Championship", "title", "standings"]),
]

# ── ホットキーワード抽出用の正規表現 / ストップワード ──────────────────
_RE_KATAKANA = re.compile(r"[ァ-ヶー]{3,}")   # 3文字以上のカタカナ列
_RE_KANJI = re.compile(r"[一-龠々]{2,}")        # 2文字以上の漢字列
_RE_LATIN = re.compile(r"[A-Za-z][A-Za-z'’&-]{2,}")  # 3文字以上の英単語

# 頻出するが話題性の無い語は除外する
_STOPWORDS: set[str] = {
    # カタカナ
    "ドライバー", "チーム", "レース", "シーズン", "グランプリ", "マシン",
    "コメント", "インタビュー", "ニュース", "モータースポーツ", "フォーミュラ",
    "スタート", "レポート", "プレビュー", "ランキング",
    # 漢字
    "今回", "今季", "今年", "昨年", "来季", "来年", "選手", "発表", "参戦",
    "獲得", "可能", "必要", "状況", "全て", "自身", "以上", "以下", "最新",
    "記事", "写真", "動画", "情報", "内容", "理由", "結果", "現在", "問題",
    # 英語
    "the", "and", "for", "with", "his", "her", "not", "but", "you", "are",
    "was", "has", "have", "this", "that", "from", "они", "will", "who", "why",
    "how", "new", "out", "все", "says", "said", "after", "before", "over",
    "into", "más", "the", "все", "формула", "формулы", "года", "год",
    "f1", "gp", "grand", "prix", "news", "формулу",
}

_MIN_KEYWORD_COUNT = 2   # この件数未満のキーワードは表示しない
_TOP_KEYWORDS = 15


def _iter_titles(sources: list[dict]):
    """全ソースの記事タイトルを順に返す。"""
    for src in sources:
        for art in src.get("articles", []):
            title = art.get("title") or ""
            if title:
                yield title


def _count_gazetteer(
    titles: list[str], entries: list[tuple[str, list[str]]]
) -> list[dict]:
    """辞書エントリごとに「言及した記事数」を数えて降順で返す。"""
    counts: Counter = Counter()
    lowered = [t.lower() for t in titles]

    for name, aliases in entries:
        # 英語別名は単語境界、日本語別名は部分一致で判定する
        matchers = []
        for a in aliases:
            if a.isascii():
                matchers.append(("re", re.compile(rf"(?<![a-z]){re.escape(a.lower())}(?![a-z])")))
            else:
                matchers.append(("in", a))

        n = 0
        for orig, low in zip(titles, lowered):
            hit = False
            for kind, m in matchers:
                if kind == "in":
                    if m in orig:
                        hit = True
                        break
                else:
                    if m.search(low):
                        hit = True
                        break
            if hit:
                n += 1
        if n > 0:
            counts[name] = n

    return _ranked(counts)


def _count_keywords(titles: list[str], exclude: set[str]) -> list[dict]:
    """辞書に無い語を頻度解析でホットキーワードとして抽出する。"""
    counts: Counter = Counter()
    exclude_low = {e.lower() for e in exclude}

    for title in titles:
        # 1タイトル内の重複は1回に丸める
        terms: set[str] = set()
        terms.update(_RE_KATAKANA.findall(title))
        terms.update(_RE_KANJI.findall(title))
        terms.update(m.rstrip("-'’&") for m in _RE_LATIN.findall(title))

        for term in terms:
            key = term.lower()
            if term in _STOPWORDS or key in _STOPWORDS:
                continue
            if key in exclude_low:
                continue
            counts[term] += 1

    filtered = Counter({k: v for k, v in counts.items() if v >= _MIN_KEYWORD_COUNT})
    return _ranked(filtered, limit=_TOP_KEYWORDS, key_name="term")


def _ranked(counts: Counter, limit: int | None = None, key_name: str = "name") -> list[dict]:
    """Counter を [{name/term, count, pct}] のリストにして降順で返す。"""
    items = counts.most_common(limit)
    if not items:
        return []
    top = items[0][1]
    return [
        {key_name: k, "count": v, "pct": round(v / top * 100)}
        for k, v in items
    ]


def analyze_trends(sources: list[dict], top_drivers: int = 10, top_teams: int = 10) -> dict:
    """収集済みソースからトレンド情報を算出して返す。"""
    titles = list(_iter_titles(sources))

    drivers = _count_gazetteer(titles, _DRIVERS)[:top_drivers]
    teams = _count_gazetteer(titles, _TEAMS)[:top_teams]
    topics = _count_gazetteer(titles, _TOPICS)

    # 既に別カードで表示している辞書語(ドライバー/チーム/トピック)は
    # キーワードから除外し、「辞書外の頻出語」だけを残す
    exclude: set[str] = set()
    for _, aliases in _DRIVERS + _TEAMS + _TOPICS:
        exclude.update(aliases)
    keywords = _count_keywords(titles, exclude)

    return {
        "total_articles": len(titles),
        "drivers": drivers,
        "teams": teams,
        "topics": topics,
        "keywords": keywords,
    }
