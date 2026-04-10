# AGENTS.md — fetch-market-data

## What

米国・日本株式の市場データを取得・スクリーニングする Python パッケージ。2つのCLIツールを提供する。

| Tool | Purpose |
|------|---------|
| `fetch-market-data` | ティッカー指定で財務指標を取得 → JSON |
| `screen-market-data` | 財務条件でスクリーニングし候補ティッカーを返す → JSON |

Data source: Yahoo Finance via yfinance。Python >=3.12 必須。

## Why (Design Decisions)

- **2段階ワークフロー**: `screen-market-data` で絞り込み → `fetch-market-data` で詳細指標取得
- **TSE市場区分は区別不可**: EquityQuery は Prime/Standard/Growth を区別できず、すべて `exchange=JPX` を返す
- **Phase 2 不要**: `fetch-market-data` が `--payout-ratio`, `--equity-ratio`, `--operating-margin` 等を持つため、post-screen フィルタを別ツールで実装する必要がない
- **ページネーション**: `yf.screen()` は `offset` + `count=True` をサポート。レスポンスの `total` でマッチ総件数、`--offset` でページ送りが可能

## How (Development)

```bash
uv sync --group dev          # 依存インストール
uv run pytest                # テスト実行
uv run ruff check src tests  # lint
```

ローカルツール実行（コード変更後は `--reinstall` 必須）:

```bash
uvx --from . --reinstall screen-market-data --region jp --roe-min 10
uvx --from . --reinstall fetch-market-data 7203.T --price
```

## Repository Structure

```
src/fetch_market_data/
  cli.py / fetcher.py        # fetch-market-data
  screen_cli.py / screener.py # screen-market-data
tests/
skills/
  fetch-market-data/SKILL.md       # @skills/fetch-market-data/SKILL.md
  screen-market-data/SKILL.md      # @skills/screen-market-data/SKILL.md
.claude-plugin/plugin.json         # バージョン管理（両ツール追加時に更新）
```

## Key Technical Notes

- Exchange codes: NYSE=`NYQ`, NASDAQ=`NMS`, Japan=`JPX`
- EquityQuery `is-in` は内部で `OR` of `EQ` に変換される（`to_dict()` テストに影響）
- プラグインバージョン変更時は `plugin.json` と `marketplace.json` を両方更新

## Tool Details

各ツールの構文・オプション・スクリーニングパターンは Skill ファイルを参照:

- @skills/fetch-market-data/SKILL.md
- @skills/screen-market-data/SKILL.md
