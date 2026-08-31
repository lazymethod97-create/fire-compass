from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field
from typing import Iterable

from services.asset_import_engine import FundHolding

# Sprint 29で追加。保有ファンド一覧（asset_import_engineの解析結果）から、
# ファンド別・カテゴリ別・口座種別別の配分比率と集中度を算出する。
#
# このモジュールは配分比率の計算のみを行い、fire_engine / action_engine /
# tax_optimization等の既存の金融計算ロジックには一切関与しない。断定的な
# 投資助言（売買すべきかどうか）は行わない。カテゴリ分類はファンド名に
# 含まれるキーワードによる簡易的な推定であり、対応表にない銘柄は
# 「未分類」として明示する（誤分類を避けるため推測でカテゴリを割り当てない）。
# 文章での総評（AIによるコメント）はservices.ai_advisor.generate_
# portfolio_commentary()が別途担当し、ここで算出した数値をそのまま使う。

# 集中度の目安として注意喚起するしきい値（1ファンド・1カテゴリの比率）。
CONCENTRATION_WARNING_THRESHOLD_PCT = 40.0

_UNCATEGORIZED_LABEL = "未分類"

# キーワードはunicodedata.normalize("NFKC", ...).upper()で正規化した
# 文字列に対して判定する（全角英数字と半角英数字、大文字小文字の違いを
# 吸収するため）。上から順に最初に一致したものを採用する。
_CATEGORY_KEYWORD_RULES: tuple[tuple[str, str], ...] = (
    ("FANG", "テーマ型（FANG+等）"),
    ("SOX", "セクター型（半導体等）"),
    ("半導体", "セクター型（半導体等）"),
    ("インド", "新興国株式（インド等）"),
    ("オール・カントリー", "全世界株式"),
    ("全世界株式", "全世界株式"),
    ("S&P", "米国株式"),
    ("米国株式", "米国株式"),
)

_TAXABLE_ACCOUNT_LABEL = "課税口座"
_NISA_ACCOUNT_LABEL = "NISA（非課税）"

_TAXABLE_ACCOUNT_TYPES = ("特定/一般",)
_NISA_ACCOUNT_TYPES = ("旧NISA/旧つみたてNISA", "NISA (成長)", "NISA (つみたて)")


def _normalize(text: str) -> str:
    # 全角英数字・記号を半角に統一し、大文字化してから判定する
    # （"Ｓ＆Ｐ５００" と "S&P500" を同一視するため）。
    return unicodedata.normalize("NFKC", text).upper()


def categorize_fund(fund_name: str) -> str:
    """ファンド名からキーワードで資産カテゴリを推定する。

    対応表にない場合は"未分類"を返す（誤分類を避けるため推測はしない）。
    """
    normalized_name = _normalize(fund_name)

    for keyword, category in _CATEGORY_KEYWORD_RULES:
        if _normalize(keyword) in normalized_name:
            return category

    return _UNCATEGORIZED_LABEL


@dataclass
class AllocationSlice:
    label: str
    valuation_amount: float  # 万円
    weight_pct: float


@dataclass
class PortfolioBalanceResult:
    total_valuation: float = 0.0  # 万円
    by_fund: list[AllocationSlice] = field(default_factory=list)
    by_category: list[AllocationSlice] = field(default_factory=list)
    by_account_type: list[AllocationSlice] = field(default_factory=list)
    top_fund: AllocationSlice | None = None
    top_category: AllocationSlice | None = None
    concentration_warnings: list[str] = field(default_factory=list)
    uncategorized_fund_names: list[str] = field(default_factory=list)


def _aggregate(
    pairs: Iterable[tuple[str, float]],
    total: float,
) -> list[AllocationSlice]:
    totals: dict[str, float] = {}
    for label, amount in pairs:
        totals[label] = totals.get(label, 0.0) + amount

    slices = [
        AllocationSlice(
            label=label,
            valuation_amount=round(amount, 2),
            weight_pct=round((amount / total * 100.0) if total > 0 else 0.0, 1),
        )
        for label, amount in totals.items()
    ]
    slices.sort(key=lambda item: item.valuation_amount, reverse=True)
    return slices


def analyze_portfolio_balance(
    holdings: list[FundHolding],
) -> PortfolioBalanceResult:
    """保有ファンド一覧から、ファンド別・カテゴリ別・口座種別別の配分比率と
    集中度を算出する。

    集中度は「1ファンド」「1カテゴリ」の比率がCONCENTRATION_WARNING_
    THRESHOLD_PCT（デフォルト40%）を超えた場合にのみ注意喚起する。
    投資判断（売買すべきかどうか）そのものは一切行わない。
    """
    holdings = list(holdings)
    result = PortfolioBalanceResult()

    if not holdings:
        return result

    total = round(sum(h.valuation_amount for h in holdings), 2)
    result.total_valuation = total

    if total <= 0:
        return result

    result.by_fund = _aggregate(
        ((h.fund_name, h.valuation_amount) for h in holdings), total
    )

    account_type_pairs = []
    for h in holdings:
        if h.account_type in _TAXABLE_ACCOUNT_TYPES:
            account_type_pairs.append((_TAXABLE_ACCOUNT_LABEL, h.valuation_amount))
        elif h.account_type in _NISA_ACCOUNT_TYPES:
            account_type_pairs.append((_NISA_ACCOUNT_LABEL, h.valuation_amount))
        else:
            account_type_pairs.append((h.account_type, h.valuation_amount))
    result.by_account_type = _aggregate(account_type_pairs, total)

    categorized_pairs = []
    uncategorized_names: set[str] = set()
    for holding in holdings:
        category = categorize_fund(holding.fund_name)
        if category == _UNCATEGORIZED_LABEL:
            uncategorized_names.add(holding.fund_name)
        categorized_pairs.append((category, holding.valuation_amount))

    result.by_category = _aggregate(categorized_pairs, total)
    result.uncategorized_fund_names = sorted(uncategorized_names)

    if result.by_fund:
        result.top_fund = result.by_fund[0]
    if result.by_category:
        result.top_category = result.by_category[0]

    if (
        result.top_fund
        and result.top_fund.weight_pct > CONCENTRATION_WARNING_THRESHOLD_PCT
    ):
        result.concentration_warnings.append(
            f"「{result.top_fund.label}」が保有ファンド全体の"
            f"{result.top_fund.weight_pct:.1f}%を占めており、"
            "1銘柄への集中度が高めです。"
        )

    if (
        result.top_category
        and result.top_category.label != _UNCATEGORIZED_LABEL
        and result.top_category.weight_pct > CONCENTRATION_WARNING_THRESHOLD_PCT
    ):
        result.concentration_warnings.append(
            f"「{result.top_category.label}」カテゴリが保有ファンド全体の"
            f"{result.top_category.weight_pct:.1f}%を占めており、"
            "同じような値動きをしやすい資産への集中度が高めです。"
        )

    return result
