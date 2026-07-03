# F1 News

F1関連ニュースを複数サイトからスクレイピングし、静的サイトとして S3 でホスティングするツール。

## 仕組み

```
GitHub Actions (30分ごと / mainへのpush時)
  → scrape_news() で各サイトをスクレイピング
  → generate.py が Jinja2 テンプレートで index.html を生成
  → AWS S3 にアップロード → 静的サイトとして公開
```

## ソース一覧

| サイト | 方式 |
|---|---|
| autosport-japan | HTML scraping |
| F1-Gate | HTML scraping |
| F1情報通 | HTML scraping |
| motorsport.com (JP) | RSS |
| motorsport.com (EN) | RSS |
| BBC Sport F1 | RSS |
| Sky Sports F1 | HTML scraping |

## 構成

```
config/config.yaml        # スクレイピング設定
modules/
  load_config.py          # 設定読み込み
  scraper.py              # HTML / RSS スクレイパー
  structure.py            # データクラス定義
templates/index.html.j2   # Jinja2 + Alpine.js テンプレート
generate.py               # HTML 生成スクリプト
template.yaml             # CloudFormation (S3バケット定義)
.github/workflows/deploy.yml  # GitHub Actions ワークフロー
```

## AWS インフラ

CloudFormation (`template.yaml`) で S3 バケットを管理。
初回は GitHub Actions が自動でスタックを作成する。

必要な GitHub Secrets:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
