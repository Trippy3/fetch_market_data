# 指標実装 ToDoリスト

凡例:
- `[ ]` 未実装
- `[x]` 実装済み
- `[-]` 対象外（Yahoo Finance非対応）

---

## 株価・市場データ

| 指標 | オプション | 取得方法 |
|---|---|---|
| 現在株価 | `--price` | `fast_info.last_price` |
| 52週高値 | `--week52-high` | `info['fiftyTwoWeekHigh']` |
| 52週安値 | `--week52-low` | `info['fiftyTwoWeekLow']` |
| 出来高（直近） | `--volume` | `fast_info.last_volume` |
| 出来高（3ヶ月平均） | `--avg-volume` | `fast_info.three_month_average_volume` |
| 時価総額 | `--market-cap` | `info['marketCap']` |
| 前日比（金額） | `--price-change` | `history(period='2d')` から計算 |
| 前日比（%） | `--price-change-pct` | `history(period='2d')` から計算 |
| 週足変化率 | `--weekly-change` | `history(period='5d')` から計算 |
| 月足変化率 | `--monthly-change` | `history(period='1mo')` から計算 |

- [x] `--price`
- [x] `--week52-high`
- [x] `--week52-low`
- [x] `--volume`
- [x] `--avg-volume`
- [x] `--market-cap`
- [ ] `--price-change`
- [ ] `--price-change-pct`
- [ ] `--weekly-change`
- [ ] `--monthly-change`

---

## バリュエーション指標

| 指標 | オプション | 取得方法 |
|---|---|---|
| PER（実績） | `--trailing-pe` | `info['trailingPE']` |
| PER（予想） | `--forward-pe` | `info['forwardPE']` |
| PBR | `--pbr` | `info['priceToBook']` |
| PSR | `--psr` | `info['priceToSalesTrailing12Months']` |
| EV/EBITDA | `--ev-ebitda` | `info['enterpriseToEbitda']` |
| PEGレシオ | `--peg` | `info['pegRatio']` |
| 配当利回り | `--dividend-yield` | `info['dividendYield']` |
| 配当性向 | `--payout-ratio` | `info['payoutRatio']` |

- [x] `--trailing-pe`
- [x] `--forward-pe`
- [x] `--pbr`
- [x] `--psr`
- [x] `--ev-ebitda`
- [x] `--peg`
- [x] `--dividend-yield`
- [x] `--payout-ratio`

---

## 財務・業績データ（損益計算書）

| 指標 | オプション | 取得方法 |
|---|---|---|
| 売上高（実績） | `--revenue` | `income_stmt.loc['Total Revenue']` |
| 売上高（予想） | `--revenue-estimate` | `ticker.revenue_estimate` |
| 売上高YoY成長率 | `--revenue-growth` | `income_stmt` から計算 |
| 営業利益 | `--operating-income` | `income_stmt.loc['Operating Income']` |
| 営業利益率 | `--operating-margin` | `income_stmt` から計算 |
| 純利益 | `--net-income` | `income_stmt.loc['Net Income']` |
| EPS（実績） | `--trailing-eps` | `info['trailingEps']` |
| EPS（予想） | `--forward-eps` | `info['forwardEps']` |
| グロスマージン | `--gross-margin` | `income_stmt` から計算（Gross Profit / Revenue） |

- [x] `--revenue`
- [ ] `--revenue-estimate`
- [ ] `--revenue-growth`
- [x] `--operating-income`
- [ ] `--operating-margin`
- [x] `--net-income`
- [x] `--trailing-eps`
- [x] `--forward-eps`
- [ ] `--gross-margin`

---

## 財務・業績データ（貸借対照表）

| 指標 | オプション | 取得方法 |
|---|---|---|
| 現金・現金同等物 | `--cash` | `balance_sheet.loc['Cash And Cash Equivalents']` |
| のれん | `--goodwill` | `balance_sheet.loc['Goodwill']` |
| 無形資産 | `--intangible-assets` | `balance_sheet.loc['Other Intangible Assets']` |
| 自己資本比率 | `--equity-ratio` | `balance_sheet` から計算（Equity / Assets） |
| 有利子負債/EBITDA | `--debt-ebitda` | `balance_sheet` + `income_stmt` から計算 |

- [x] `--cash`
- [x] `--goodwill`
- [x] `--intangible-assets`
- [ ] `--equity-ratio`
- [ ] `--debt-ebitda`

---

## キャッシュフロー

| 指標 | オプション | 取得方法 |
|---|---|---|
| 営業CF | `--operating-cf` | `cashflow.loc['Operating Cash Flow']` |
| FCF | `--fcf` | `info['freeCashflow']` |
| FCFマージン | `--fcf-margin` | FCF / 売上高で計算 |

- [x] `--operating-cf`
- [x] `--fcf`
- [ ] `--fcf-margin`

---

## 収益性・効率性指標

| 指標 | オプション | 取得方法 |
|---|---|---|
| ROE | `--roe` | `info['returnOnEquity']` |
| ROA | `--roa` | `info['returnOnAssets']` |
| ROIC | `-` | Yahoo Finance非対応 |

- [x] `--roe`
- [x] `--roa`
- [-] ROIC（Yahoo Finance非対応）

---

## 成長・将来性データ

| 指標 | オプション | 取得方法 |
|---|---|---|
| 通期業績ガイダンス | `--guidance` | `ticker.calendar`（精度に限界あり） |
| アナリストEPS予想 | `--eps-estimate` | `ticker.earnings_estimate` |
| アナリスト売上予想 | `--revenue-estimate` | `ticker.revenue_estimate` |
| アナリスト目標株価 | `--price-target` | `ticker.analyst_price_targets` |
| レーティング分布 | `--ratings` | `ticker.recommendations_summary` |
| RPO / ARR / NRR | `-` | Yahoo Finance非対応 |
| 受注残・バックログ | `-` | Yahoo Finance非対応 |

- [ ] `--guidance`
- [ ] `--eps-estimate`
- [ ] `--revenue-estimate`
- [ ] `--price-target`
- [ ] `--ratings`
- [-] RPO / ARR / NRR（Yahoo Finance非対応）
- [-] 受注残・バックログ（Yahoo Finance非対応）

---

## 株主還元

| 指標 | オプション | 取得方法 |
|---|---|---|
| 配当履歴 | `--dividend-history` | `ticker.dividends` |
| 増配率 | `--dividend-growth` | `ticker.dividends` から計算 |
| 自己株買い金額 | `--buyback` | `cashflow.loc['Repurchase Of Capital Stock']` |
| 総還元性向 | `--total-return-ratio` | （配当 + 自己株買い）/ 純利益で計算 |
| 消却有無 | `-` | Yahoo Finance非対応 |

- [ ] `--dividend-history`
- [ ] `--dividend-growth`
- [ ] `--buyback`
- [ ] `--total-return-ratio`
- [-] 消却有無（Yahoo Finance非対応）

---

## リスク・定性情報

| 指標 | オプション | 取得方法 |
|---|---|---|
| 直近の決算発表日 | `--next-earnings` | `ticker.calendar` |
| インサイダー取引 | `--insider-trades` | `ticker.insider_transactions` |
| 大株主の保有状況 | `--major-holders` | `ticker.major_holders` / `institutional_holders` |
| ベータ値 | `--beta` | `info['beta']` |
| 重要イベント | `-` | Yahoo Finance非対応 |
| 訴訟・規制リスク | `-` | Yahoo Finance非対応 |
| 競合他社の動向 | `-` | Yahoo Finance非対応 |
| マクロ感応度（詳細） | `-` | Yahoo Finance非対応（ベータ値のみ取得可） |

- [ ] `--next-earnings`
- [ ] `--insider-trades`
- [ ] `--major-holders`
- [x] `--beta`
- [-] 重要イベント（Yahoo Finance非対応）
- [-] 訴訟・規制リスク（Yahoo Finance非対応）
- [-] 競合他社動向（Yahoo Finance非対応）
