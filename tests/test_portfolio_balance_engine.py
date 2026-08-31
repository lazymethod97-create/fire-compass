from services.asset_import_engine import FundHolding, parse_sbi_fund_holdings_csv
from services.portfolio_balance_engine import (
    CONCENTRATION_WARNING_THRESHOLD_PCT,
    analyze_portfolio_balance,
    categorize_fund,
)

SAMPLE_CSV = (
    '"保有状況","ファンド名","口座種別","取引種別","評価金額","前年末評価金額",'
    '"売却金額","分配金額","買付金額","手数料","トータルリターン（円）","トータルリターン（率）"\r\n'
    '"保有中","ｅＭＡＸＩＳ　Ｓｌｉｍ　米国株式（Ｓ＆Ｐ５００）","特定/一般","金額",'
    '"2276347","0","0","0","1691000","0","+585347","+34.61%"\r\n'
    '"保有中","ｅＭＡＸＩＳ　Ｓｌｉｍ　米国株式（Ｓ＆Ｐ５００）","旧NISA/旧つみたてNISA","金額",'
    '"145992","0","0","0","78219","0","+67773","+86.64%"\r\n'
    '"保有中","ｅＭＡＸＩＳ　Ｓｌｉｍ　米国株式（Ｓ＆Ｐ５００）","NISA (成長)","金額",'
    '"3077602","0","0","0","2400000","0","+677602","+28.23%"\r\n'
    '"保有中","ｅＭＡＸＩＳ　Ｓｌｉｍ　米国株式（Ｓ＆Ｐ５００）","NISA (つみたて)","金額",'
    '"1421926","0","0","0","1101000","0","+320926","+29.14%"\r\n'
    '"保有中","ｅＭＡＸＩＳ　Ｓｌｉｍ　全世界株式（オール・カントリー）","特定/一般","金額",'
    '"1148596","0","0","0","836000","0","+312596","+37.39%"\r\n'
    '"保有中","ｅＭＡＸＩＳ　Ｓｌｉｍ　全世界株式（オール・カントリー）","旧NISA/旧つみたてNISA","金額",'
    '"578089","0","0","0","309226","0","+268863","+86.94%"\r\n'
    '"保有中","ｅＭＡＸＩＳ　Ｓｌｉｍ　全世界株式（オール・カントリー）","NISA (成長)","金額",'
    '"4434954","0","0","0","3400000","0","+1034954","+30.43%"\r\n'
    '"保有中","ｅＭＡＸＩＳ　Ｓｌｉｍ　全世界株式（オール・カントリー）","NISA (つみたて)","金額",'
    '"3464815","0","0","0","2409000","0","+1055815","+43.82%"\r\n'
    '"保有中","ｉＦｒｅｅＮＥＸＴ　ＦＡＮＧ＋インデックス","特定/一般","金額",'
    '"15367703","0","1700000","0","9802000","0","+7265703","+74.12%"\r\n'
    '"保有中","ｉＦｒｅｅＮＥＸＴ　ＦＡＮＧ＋インデックス","NISA (成長)","金額",'
    '"2162524","0","0","0","1000000","0","+1162524","+116.25%"\r\n'
    '"保有中","ｉＦｒｅｅＮＥＸＴ　インド株インデックス","NISA (成長)","金額",'
    '"410677","0","0","0","400000","0","+10677","+2.66%"\r\n'
    '"保有中","ニッセイＳＯＸ指数インデックスファンド（米国半導体株）＜購入・換金手数料なし＞",'
    '"特定/一般","金額","2820145","0","0","0","1000000","0","+1820145","+182.01%"\r\n'
    '"保有中","ｉＴｒｕｓｔインド株式","旧NISA/旧つみたてNISA","金額",'
    '"14926","0","0","0","12555","0","+2371","+18.88%"'
)


# --- categorize_fund ---

def test_categorize_fullwidth_sp500():
    assert categorize_fund("ｅＭＡＸＩＳ　Ｓｌｉｍ　米国株式（Ｓ＆Ｐ５００）") == "米国株式"


def test_categorize_all_country():
    assert (
        categorize_fund("ｅＭＡＸＩＳ　Ｓｌｉｍ　全世界株式（オール・カントリー）")
        == "全世界株式"
    )


def test_categorize_fang():
    assert categorize_fund("ｉＦｒｅｅＮＥＸＴ　ＦＡＮＧ＋インデックス") == "テーマ型（FANG+等）"


def test_categorize_sox_semiconductor():
    assert (
        categorize_fund("ニッセイＳＯＸ指数インデックスファンド（米国半導体株）")
        == "セクター型（半導体等）"
    )


def test_categorize_india():
    assert categorize_fund("ｉＴｒｕｓｔインド株式") == "新興国株式（インド等）"


def test_categorize_unknown_fund_is_uncategorized():
    assert categorize_fund("聞いたことのないファンド") == "未分類"


# --- analyze_portfolio_balance ---

def test_empty_holdings_returns_zero_result():
    result = analyze_portfolio_balance([])
    assert result.total_valuation == 0.0
    assert result.by_fund == []
    assert result.concentration_warnings == []


def test_real_sample_top_category_is_fang_and_flagged():
    parsed = parse_sbi_fund_holdings_csv(SAMPLE_CSV)
    result = analyze_portfolio_balance(parsed.holdings)

    assert result.top_category.label == "テーマ型（FANG+等）"
    assert result.top_category.weight_pct > CONCENTRATION_WARNING_THRESHOLD_PCT
    assert any("テーマ型（FANG+等）" in w for w in result.concentration_warnings)
    assert result.uncategorized_fund_names == []


def test_real_sample_by_fund_aggregates_across_account_types():
    parsed = parse_sbi_fund_holdings_csv(SAMPLE_CSV)
    result = analyze_portfolio_balance(parsed.holdings)

    sp500 = next(s for s in result.by_fund if "米国株式" in s.label)
    # 4口座種別ぶんの評価額が1ファンドとして合算されていること
    assert sp500.valuation_amount == 692.18  # 2276347+145992+3077602+1421926 円 -> 万円

    all_country = next(s for s in result.by_fund if "オール・カントリー" in s.label)
    assert all_country.valuation_amount == 962.65


def test_by_account_type_groups_old_and_new_nisa_together():
    parsed = parse_sbi_fund_holdings_csv(SAMPLE_CSV)
    result = analyze_portfolio_balance(parsed.holdings)

    labels = {s.label for s in result.by_account_type}
    assert labels == {"課税口座", "NISA（非課税）"}


def test_no_warning_when_balanced():
    holdings = [
        FundHolding("ファンドA", "特定/一般", 100.0, 90.0),
        FundHolding("ファンドB", "特定/一般", 100.0, 90.0),
        FundHolding("ファンドC", "特定/一般", 100.0, 90.0),
    ]
    result = analyze_portfolio_balance(holdings)

    assert result.concentration_warnings == []


def test_uncategorized_fund_is_reported_but_category_not_double_flagged():
    holdings = [
        FundHolding("謎の独自ファンド", "特定/一般", 100.0, 90.0),
    ]
    result = analyze_portfolio_balance(holdings)

    assert result.uncategorized_fund_names == ["謎の独自ファンド"]
    assert result.top_category.label == "未分類"
    # ファンド単位の集中度警告は分類に関わらず出る
    assert any("謎の独自ファンド" in w for w in result.concentration_warnings)
    # ただし「未分類」カテゴリそのものへの集中度警告は出さない（重複を避ける）
    assert not any("未分類" in w for w in result.concentration_warnings)
