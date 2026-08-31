from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field

# Sprint 28で追加。証券会社（SBI証券）が出力する「保有ファンド一覧」CSVを
# 読み込み、課税口座残高・NISA残高・NISA投資枠（累計投資額）を概算する。
#
# このモジュールはCSVの読み込み・集計のみを行い、fire_engine /
# action_engine / monthly_budget_engine / withdrawal_engine /
# tax_optimizationの計算ロジックには一切関与しない。算出した金額は
# あくまでapp.py側の入力欄の「初期値」として使われ、最終的な数値は
# 引き続きユーザーが確認・手入力で調整できる。

REQUIRED_COLUMNS = ("保有状況", "ファンド名", "口座種別", "評価金額", "買付金額")

_HELD_STATUS = "保有中"

_TAXABLE_ACCOUNT_TYPES = ("特定/一般",)
_OLD_NISA_ACCOUNT_TYPES = ("旧NISA/旧つみたてNISA",)
_NEW_NISA_GROWTH_ACCOUNT_TYPES = ("NISA (成長)",)
_NEW_NISA_TSUMITATE_ACCOUNT_TYPES = ("NISA (つみたて)",)

# 評価額をNISA残高として合算する口座種別（新NISA・旧NISAの両方を含む。
# 旧NISAは非課税での保有自体は続いているため、残高としては合算するが、
# 新NISAの生涯投資枠のカウントには含めない）。
_ALL_NISA_ACCOUNT_TYPES = (
    _OLD_NISA_ACCOUNT_TYPES
    + _NEW_NISA_GROWTH_ACCOUNT_TYPES
    + _NEW_NISA_TSUMITATE_ACCOUNT_TYPES
)

# 買付金額を新NISAの累計投資額（生涯投資枠1800万円に対する概算）として
# 合算する口座種別。旧NISAは新NISAの生涯投資枠にカウントされないため含めない。
_NEW_NISA_CONTRIBUTED_ACCOUNT_TYPES = (
    _NEW_NISA_GROWTH_ACCOUNT_TYPES + _NEW_NISA_TSUMITATE_ACCOUNT_TYPES
)


class AssetImportError(Exception):
    """CSVの読み込み・解析に失敗した場合の例外。"""


@dataclass
class FundHolding:
    fund_name: str
    account_type: str
    valuation_amount: float  # 万円
    purchase_amount: float  # 万円


@dataclass
class AssetImportResult:
    taxable_assets: float = 0.0  # 万円。特定/一般口座の評価金額合計
    nisa_assets: float = 0.0  # 万円。NISA各口座（旧NISA含む）の評価金額合計
    # 万円。新NISA（成長＋つみたて）の買付金額合計から概算した累計投資額。
    # 旧NISAは新NISAの生涯投資枠にカウントされないため含まない。
    nisa_contributed: float = 0.0
    # 万円。新NISA成長投資枠のみの買付金額合計から概算した累計投資額。
    nisa_growth_contributed: float = 0.0
    holdings: list[FundHolding] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    skipped_rows: int = 0


def decode_csv_bytes(raw: bytes) -> str:
    """証券会社CSVによくある文字コード（UTF-8 BOM付き／Shift-JIS系）を
    順に試して文字列にデコードする。
    """
    for encoding in ("utf-8-sig", "cp932"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue

    raise AssetImportError(
        "CSVの文字コードを判定できませんでした（UTF-8またはShift-JISで"
        "保存し直してから再度お試しください）。"
    )


def _parse_amount(raw_value: str, column_name: str, row_number: int) -> float:
    cleaned = (raw_value or "").strip().replace(",", "").replace("+", "")

    if cleaned == "":
        raise AssetImportError(
            f"{row_number}行目の「{column_name}」が空です。"
        )

    try:
        return float(cleaned)
    except ValueError as error:
        raise AssetImportError(
            f"{row_number}行目の「{column_name}」（{raw_value}）を"
            "数値として読み取れませんでした。"
        ) from error


def parse_sbi_fund_holdings_csv(csv_text: str) -> AssetImportResult:
    """SBI証券の「保有ファンド一覧」CSV（文字列）を解析する。

    金額（評価金額・買付金額）は円で記載されている前提で、万円に換算する。
    「保有状況」が"保有中"以外の行（売却済など）はスキップする。
    口座種別が想定外の値の行も集計から除外し、warningsに理由を記録する
    （合計を過大・過小に見せないため、不明な行は無視して警告するに留める）。
    """
    reader = csv.DictReader(io.StringIO(csv_text))

    if reader.fieldnames is None:
        raise AssetImportError("CSVにヘッダー行が見つかりませんでした。")

    fieldnames = {name.strip() for name in reader.fieldnames if name}
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in fieldnames]
    if missing_columns:
        raise AssetImportError(
            "CSVの形式が想定と異なります。次の列が見つかりません: "
            + "、".join(missing_columns)
        )

    result = AssetImportResult()

    taxable_yen = 0.0
    nisa_yen = 0.0
    nisa_contributed_yen = 0.0
    nisa_growth_contributed_yen = 0.0

    unknown_account_types: set[str] = set()

    for row_number, row in enumerate(reader, start=2):  # 1行目はヘッダー
        status = (row.get("保有状況") or "").strip()
        if status != _HELD_STATUS:
            result.skipped_rows += 1
            continue

        account_type = (row.get("口座種別") or "").strip()
        fund_name = (row.get("ファンド名") or "").strip()

        valuation_yen = _parse_amount(row.get("評価金額", ""), "評価金額", row_number)
        purchase_yen = _parse_amount(row.get("買付金額", ""), "買付金額", row_number)

        result.holdings.append(
            FundHolding(
                fund_name=fund_name,
                account_type=account_type,
                valuation_amount=round(valuation_yen / 10000, 2),
                purchase_amount=round(purchase_yen / 10000, 2),
            )
        )

        if account_type in _TAXABLE_ACCOUNT_TYPES:
            taxable_yen += valuation_yen
        elif account_type in _ALL_NISA_ACCOUNT_TYPES:
            nisa_yen += valuation_yen
            if account_type in _NEW_NISA_CONTRIBUTED_ACCOUNT_TYPES:
                nisa_contributed_yen += purchase_yen
            if account_type in _NEW_NISA_GROWTH_ACCOUNT_TYPES:
                nisa_growth_contributed_yen += purchase_yen
        else:
            unknown_account_types.add(account_type)
            result.skipped_rows += 1

    result.taxable_assets = round(taxable_yen / 10000, 2)
    result.nisa_assets = round(nisa_yen / 10000, 2)
    result.nisa_contributed = round(nisa_contributed_yen / 10000, 2)
    result.nisa_growth_contributed = round(nisa_growth_contributed_yen / 10000, 2)

    for account_type in sorted(unknown_account_types):
        result.warnings.append(
            f"未知の口座種別「{account_type}」の行は集計に含めていません。"
            "内容を確認し、必要であれば手入力で反映してください。"
        )

    result.warnings.append(
        "「今年のNISA投資額」はCSVから年ごとの内訳を判別できないため、"
        "取り込んでいません。必要であれば手入力してください。"
    )

    return result
