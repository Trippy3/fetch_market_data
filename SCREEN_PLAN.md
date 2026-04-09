# screen-market-data 実装計画

## 概要

既存の `fetch-market-data` パッケージに `screen-market-data` コマンドを追加する。
yfinance の `EquityQuery` / `yf.screen()` を使い、国内・米国株のスクリーニングを行い
ティッカーシンボルの一覧を JSON で返す。

```bash
uvx --from git+https://github.com/Trippy3/fetch_market_data screen-market-data [options]
```

---

## 調査結論

### 東証市場区分（プライム/スタンダード/グロース）

yfinance の `EquityQuery` は TSE 市場区分コードに非対応。
全銘柄が `exchange=JPX` として返り、市場区分の区別が不可能。
→ 初版スコープ外。将来的に J-Quants API 連携で対応予定。

### 後処理フィルタ（フェーズ2）の扱い

当初計画していた後処理フィルタ（配当性向・自己資本比率・営業利益率など）は
既存の `fetch-market-data` ツールで取得できるため不要。

想定ワークフロー:
```bash
# Step 1: screen-market-data で候補銘柄を絞る
screen-market-data --region jp --roe-min 10 --div-yield-min 1.5

# Step 2: fetch-market-data で詳細指標を取得（既存ツールで代用）
fetch-market-data 4776.T 6036.T --payout-ratio --equity-ratio --operating-margin
```

### EquityQuery 非対応条件（スコープ外）

| 条件 | 理由 |
|------|------|
| ROE 3期連続改善 | 複数期データの計算が必要 |
| 売上成長3年平均 | 複数期データの計算が必要 |
| TAM $10B以上 | 定性評価、自動化不可 |
| Net Revenue Retention | 非公開データ |
| 競合脅威・シェア低下 | 定性評価、自動化不可 |

---

## ディレクトリ構造変更点

```
fetch-market-data/
├── src/
│   └── fetch_market_data/
│       ├── cli.py              (既存: fetch-market-data)
│       ├── fetcher.py          (既存)
│       ├── screen_cli.py       ← 新規: screen-market-data エントリーポイント
│       └── screener.py         ← 新規: EquityQuery スクリーニングロジック
├── tests/
│   ├── test_cli.py             (既存)
│   ├── test_fetcher.py         (既存)
│   ├── test_new_metrics.py     (既存)
│   ├── test_screen_cli.py      ← 新規
│   └── test_screener.py        ← 新規
├── skills/
│   ├── fetch-market-data/      (既存)
│   └── screen-market-data/     ← 新規スキル（Phase 3 で対応）
│       ├── SKILL.md
│       ├── examples/
│       └── references/
└── pyproject.toml              ← [project.scripts] に1行追加
```

---

## CLIオプション仕様

### 市場指定（いずれか必須）

| オプション | 説明 | EquityQuery フィールド |
|-----------|------|----------------------|
| `--region jp` | 日本市場全体 | `region=jp` |
| `--region us` | 米国市場全体（NYSE+NASDAQ） | `region=us` |
| `--exchange nasdaq` | NASDAQ のみ | `exchange=NMS` |
| `--exchange nyse` | NYSE のみ | `exchange=NYQ` |

### フィルタ条件

| オプション | 説明 | EquityQuery フィールド |
|-----------|------|----------------------|
| `--roe-min FLOAT` | ROE 下限（%） | `returnonequity.lasttwelvemonths` |
| `--div-yield-min FLOAT` | 配当利回り下限（%） | `forward_dividend_yield` |
| `--div-growth-years INT` | 連続増配年数下限 | `consecutive_years_of_dividend_growth_count` |
| `--revenue-growth-min FLOAT` | 売上成長率下限（%、YoY） | `totalrevenues1yrgrowth.lasttwelvemonths` |
| `--debt-ebitda-max FLOAT` | 有利子負債/EBITDA 上限 | `totaldebtebitda.lasttwelvemonths` |
| `--fcf-positive` | FCF がプラスのみ | `leveredfreecashflow.lasttwelvemonths > 0` |
| `--gross-margin-min FLOAT` | 粗利率下限（%） | `grossprofitmargin.lasttwelvemonths` |
| `--peg-max FLOAT` | PEGレシオ上限 | `pegratio_5y` |
| `--insider-min FLOAT` | インサイダー保有比率下限（%） | `pctheldinsider` |
| `--market-cap-min FLOAT` | 時価総額下限（億円 or 百万USD） | `intradaymarketcap` |
| `--sector TEXT` | セクター指定 | `sector` |

### 出力制御

| オプション | デフォルト | 説明 |
|-----------|-----------|------|
| `--size INT` | 50 | 取得件数上限 |
| `--sort-by TEXT` | `intradaymarketcap` | ソートフィールド |
| `--sort-asc` | False（降順） | 昇順ソート |

---

## 出力フォーマット

```json
{
  "query": {
    "region": "jp",
    "conditions": {
      "roe_min": 10,
      "div_yield_min": 1.5,
      "div_growth_years": 3,
      "revenue_growth_min": 3
    }
  },
  "count": 8,
  "tickers": ["4776.T", "6036.T", "3854.T", "4482.T", "3064.T", "3939.T", "3916.T", "3482.T"]
}
```

---

## 実装フェーズ

| フェーズ | 内容 | 状態 |
|---------|------|------|
| Phase 1 | `screener.py` + `screen_cli.py` 実装 | 実装予定 |
| Phase 2 | テスト作成・カバレッジ確認 | 実装予定 |
| Phase 3 | Skills / README 更新 | 実装予定 |
| Phase 4 | 東証市場区分（J-Quants 連携） | 将来対応 |

---

## METRICS_TODO への追記事項（将来）

- `--roe-3y-consecutive`: ROE 3期連続改善フラグ（`ticker.income_stmt` 複数期計算）
- `--revenue-growth-3y`: 売上成長率3年平均（`ticker.financials` 複数期平均）
