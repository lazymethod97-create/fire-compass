# FIRE Compass

FIRE後の生活費、資産寿命、資産取り崩し余力をシミュレーションするWebアプリです。

## Sprint 1
- FIRE基本情報入力
- 年間純生活費計算
- 推奨月間支出の目安
- 現金が生活費何か月分あるか
- 標準・悲観・楽観シナリオ
- 資産寿命の確認

## Sprint 2
- 最低現金バッファ（月数）の設定
- 現金超過時の追加投資候補額
- 現金不足時の投資資産からの補充候補額
- 今月の推奨行動
- ルールベースの判断理由
- Sprint 1シミュレーションとの二重計上防止

## Sprint 3
- 市場環境の選択
- 通常・弱気相場・暴落・深刻な暴落の4段階
- 市場環境に応じた現金バッファ調整
- 暴落時の追加投資抑制
- 暴落時の生活費削減
- 市場環境別の防御ルール表示
- 今月の推奨行動への反映

## 起動

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
