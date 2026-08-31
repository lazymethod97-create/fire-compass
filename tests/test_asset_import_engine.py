import pytest

from services.asset_import_engine import (
    AssetImportError,
    decode_csv_bytes,
    parse_sbi_fund_holdings_csv,
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


def test_real_sample_csv_totals():
    result = parse_sbi_fund_holdings_csv(SAMPLE_CSV)

    assert result.taxable_assets == 2161.28
    assert result.nisa_assets == 1571.15
    assert result.nisa_contributed == 1071.0
    assert result.nisa_growth_contributed == 720.0
    assert result.skipped_rows == 0
    assert len(result.holdings) == 13


def test_annual_contribution_warning_always_present():
    result = parse_sbi_fund_holdings_csv(SAMPLE_CSV)

    assert any("今年のNISA投資額" in w for w in result.warnings)


def test_non_held_status_is_skipped():
    csv_text = (
        '"保有状況","ファンド名","口座種別","取引種別","評価金額","前年末評価金額",'
        '"売却金額","分配金額","買付金額","手数料","トータルリターン（円）","トータルリターン（率）"\r\n'
        '"売却済","テストファンド","特定/一般","金額","100000","0","0","0","90000","0","+10000","+11.1%"'
    )

    result = parse_sbi_fund_holdings_csv(csv_text)

    assert result.taxable_assets == 0.0
    assert result.skipped_rows == 1
    assert result.holdings == []


def test_unknown_account_type_excluded_with_warning():
    csv_text = (
        '"保有状況","ファンド名","口座種別","取引種別","評価金額","前年末評価金額",'
        '"売却金額","分配金額","買付金額","手数料","トータルリターン（円）","トータルリターン（率）"\r\n'
        '"保有中","テストファンド","謎の口座","金額","100000","0","0","0","90000","0","+10000","+11.1%"'
    )

    result = parse_sbi_fund_holdings_csv(csv_text)

    assert result.taxable_assets == 0.0
    assert result.nisa_assets == 0.0
    assert result.skipped_rows == 1
    assert any("謎の口座" in w for w in result.warnings)


def test_missing_required_column_raises():
    csv_text = '"保有状況","ファンド名"\r\n"保有中","テストファンド"'

    with pytest.raises(AssetImportError):
        parse_sbi_fund_holdings_csv(csv_text)


def test_non_numeric_amount_raises():
    csv_text = (
        '"保有状況","ファンド名","口座種別","取引種別","評価金額","前年末評価金額",'
        '"売却金額","分配金額","買付金額","手数料","トータルリターン（円）","トータルリターン（率）"\r\n'
        '"保有中","テストファンド","特定/一般","金額","N/A","0","0","0","90000","0","+10000","+11.1%"'
    )

    with pytest.raises(AssetImportError):
        parse_sbi_fund_holdings_csv(csv_text)


def test_decode_utf8_sig():
    raw = SAMPLE_CSV.encode("utf-8-sig")
    assert decode_csv_bytes(raw) == SAMPLE_CSV


def test_decode_cp932_fallback():
    text = '"保有状況","ファンド名"\r\n"保有中","テスト"'
    raw = text.encode("cp932")
    assert decode_csv_bytes(raw) == text


def test_decode_unrecognized_encoding_raises():
    with pytest.raises(AssetImportError):
        decode_csv_bytes(b"\x81\xff broken")
