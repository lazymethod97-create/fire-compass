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

## 起動

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

## テスト

```powershell
pytest
```

Sprint 2では、既存2テストに加えて取り崩し・追加投資ルール4テストを追加しています。

## ルール

このアプリは金融商品の売買を自動で決定するものではなく、入力条件に基づくシミュレーションと行動候補を提供します。
