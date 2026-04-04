# fetch-market-data

米国株・日本株のティッカーシンボルを引数として渡し、指定した指標をJSON形式で返すCLIツール。

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
| `--operating-income` | 営業利益（直近年度） |
| `--net-income` | 純利益（直近年度） |
| `--trailing-eps` | EPS（実績） |
| `--forward-eps` | EPS（予想） |
| `--cash` | 現金・現金同等物 |
| `--goodwill` | のれん |
| `--intangible-assets` | 無形資産 |
| `--operating-cf` | 営業キャッシュフロー |
| `--fcf` | フリーキャッシュフロー |

### 収益性・リスク

| オプション | 説明 |
|---|---|
| `--roe` | ROE |
| `--roa` | ROA |
| `--beta` | ベータ値 |

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

    # 新しい指標を追加（例: PEG比率を別ソースから取得）
    "new-metric": MetricDef("info", lambda d: d.get("someKey")),
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
