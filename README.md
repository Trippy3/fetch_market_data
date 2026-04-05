# fetch-market-data

米国株・日本株のティッカーシンボルを引数として渡し、指定した指標をJSON形式で返すCLIツール。

## 概要

株価データの取得には [yfinance](https://github.com/ranaroussi/yfinance) を使用しています。Yahoo Finance のデータを Python から利用できる非公式ライブラリです。

## Claude Code Plugin

このリポジトリは Claude Code Plugin として配布されています。インストールすることで AI エージェントがこのツールを自律的に使いこなせる Skill が利用可能になります。

```bash
claude plugin install github:Trippy3/fetch_market_data
```

## 要件

- [uv](https://github.com/astral-sh/uv) がインストールされていること

## インストール不要で実行 (uvx)

```bash
uvx --from . fetch-market-data AAPL MSFT 7203.T
```

## 使い方

```
fetch-market-data SYMBOL [SYMBOL ...] [--price] [--market-cap] [--trailing-pe] ...
```

指標オプションを省略した場合は `--price` がデフォルトで適用されます。複数の指標を同時に指定できます。

### 例

```bash
# デフォルト (--price と同じ)
fetch-market-data AAPL MSFT 7203.T

# 複数指標を同時指定
fetch-market-data AAPL MSFT --price --market-cap --trailing-pe --dividend-yield

# 日本株
fetch-market-data 7203.T 6758.T --price --pbr --roe
```

## 出力形式

ティッカーシンボルをキーとするJSONオブジェクトを `stdout` に出力します。

```json
{
  "AAPL": {
    "price": 255.92,
    "market-cap": 3761492983808,
    "trailing-pe": 32.354,
    "dividend-yield": 0.0041,
    "currency": "USD",
    "error": null
  },
  "7203.T": {
    "price": 3255.0,
    "market-cap": 42423669489664,
    "trailing-pe": 11.4564,
    "dividend-yield": 0.0291,
    "currency": "JPY",
    "error": null
  }
}
```

`currency` と `error` は常に含まれる固定フィールドです。取得できなかった指標は `null` になります。

## 対応市場

| 市場 | ティッカー形式 | 例 |
|---|---|---|
| 米国株 | シンボルそのまま | `AAPL`, `MSFT` |
| 日本株 | 証券コード + `.T` | `7203.T`, `6758.T` |

## 指標一覧

### 株価・市場データ

| オプション | 説明 |
|---|---|
| `--price` | 現在株価（デフォルト） |
| `--volume` | 出来高（直近） |
| `--avg-volume` | 出来高（3ヶ月平均） |
| `--week52-high` | 52週高値 |
| `--week52-low` | 52週安値 |
| `--market-cap` | 時価総額 |
| `--price-change` | 前日比（金額） |
| `--price-change-pct` | 前日比（%、小数） |
| `--weekly-change` | 週足変化率（小数） |
| `--monthly-change` | 月足変化率（小数） |

### バリュエーション

| オプション | 説明 |
|---|---|
| `--trailing-pe` | PER（実績） |
| `--forward-pe` | PER（予想） |
| `--pbr` | PBR |
| `--psr` | PSR |
| `--ev-ebitda` | EV/EBITDA |
| `--peg` | PEGレシオ |
| `--dividend-yield` | 配当利回り |
| `--payout-ratio` | 配当性向 |

### 財務・業績

| オプション | 説明 |
|---|---|
| `--revenue` | 売上高（直近年度） |
| `--revenue-growth` | 売上高YoY成長率（小数） |
| `--operating-income` | 営業利益（直近年度） |
| `--operating-margin` | 営業利益率（小数） |
| `--gross-margin` | 売上総利益率（小数） |
| `--net-income` | 純利益（直近年度） |
| `--trailing-eps` | EPS（実績） |
| `--forward-eps` | EPS（予想） |
| `--cash` | 現金・現金同等物 |
| `--goodwill` | のれん |
| `--intangible-assets` | 無形資産 |
| `--equity-ratio` | 自己資本比率（小数） |
| `--debt-ebitda` | 有利子負債/EBITDA |
| `--operating-cf` | 営業キャッシュフロー |
| `--fcf` | フリーキャッシュフロー |
| `--fcf-margin` | FCFマージン（小数） |

### 収益性・リスク

| オプション | 説明 |
|---|---|
| `--roe` | ROE |
| `--roa` | ROA |
| `--beta` | ベータ値 |

### 株主還元

| オプション | 説明 |
|---|---|
| `--buyback` | 自己株買い金額（直近年度、通常負値） |
| `--dividend-history` | 配当履歴（日付→金額のJSON） |
| `--dividend-growth` | 増配率・YoY（小数） |
| `--total-return-ratio` | 総還元性向（配当＋自己株買い）/純利益 |

### 成長・アナリストデータ

| オプション | 説明 |
|---|---|
| `--eps-estimate` | アナリストEPS予想（DataFrame形式のJSON） |
| `--revenue-estimate` | アナリスト売上予想（DataFrame形式のJSON） |
| `--price-target` | アナリスト目標株価（min/mean/max等のJSON） |
| `--ratings` | レーティング分布（buy/hold/sell等のJSON） |

### イベント・定性情報

| オプション | 説明 |
|---|---|
| `--guidance` | 業績ガイダンス・カレンダー情報（JSON） |
| `--next-earnings` | 次回決算発表予定日 |
| `--insider-trades` | インサイダー取引履歴（JSON） |
| `--major-holders` | 大株主保有状況（JSON） |

## 開発

```bash
# 依存関係のインストール
uv sync

# テスト実行
uv run pytest tests/ -v --cov=src

# ローカル実行
uv run fetch-market-data AAPL --price --market-cap
```

### Lint / Format (ruff)

[ruff](https://github.com/astral-sh/ruff) をlinter・formatterとして使用しています。

```bash
# lint チェック
uv run ruff check src/ tests/

# lint 自動修正
uv run ruff check --fix src/ tests/

# フォーマット
uv run ruff format src/ tests/

# lint + フォーマットをまとめて確認
uv run ruff check src/ tests/ && uv run ruff format --check src/ tests/
```

設定は `pyproject.toml` の `[tool.ruff]` セクションで管理しています。有効なルールセット:

| ルール | 内容 |
|---|---|
| `E`, `W` | pycodestyle（スタイル） |
| `F` | pyflakes（未使用変数・インポートなど） |
| `I` | isort（インポート順） |
| `B` | flake8-bugbear（バグになりやすいパターン） |
| `UP` | pyupgrade（新しいPython構文への移行） |

### 新しい指標の追加

`src/fetch_market_data/fetcher.py` の `_METRICS` に1行追加するだけです。

```python
_METRICS: dict[str, MetricDef] = {
    # 既存の指標 ...

    # 新しい指標を追加（例: 単一ソース）
    "new-metric": MetricDef(("info",), lambda d: d.get("someKey")),

    # 複数ソースが必要な指標（例: balance_sheet と income_stmt から計算）
    "cross-metric": MetricDef(("balance_sheet", "income_stmt"), lambda bs, inc: ...),
}
```

追加後は自動的に `--new-metric` オプションとして利用可能になります。

対応データソース:

| ソース | 内容 | 速度 |
|---|---|---|
| `fast_info` | 株価・出来高など基本情報 | 速い |
| `info` | バリュエーション・財務比率など | 普通 |
| `income_stmt` | 損益計算書（年次/四半期） | 遅い |
| `balance_sheet` | 貸借対照表（年次/四半期） | 遅い |
| `cashflow` | キャッシュフロー計算書（年次/四半期） | 遅い |
| `history_2d` / `history_5d` / `history_1mo` | 価格履歴（期間指定） | 普通 |
| `dividends` | 配当履歴 Series | 普通 |
| `calendar` | 決算予定・ガイダンス dict | 普通 |
| `earnings_estimate` / `revenue_estimate` | アナリスト予想 DataFrame | 普通 |
| `analyst_price_targets` | 目標株価 dict | 普通 |
| `recommendations_summary` | レーティング分布 DataFrame | 普通 |
| `insider_transactions` | インサイダー取引 DataFrame | 遅い |
| `major_holders` | 大株主 DataFrame | 遅い |
