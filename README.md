# FIRE Compass

FIRE後の生活費、資産寿命、資産取り崩し余力をシミュレーションするWebアプリです。

## Sprint 1
- FIRE基本情報入力
- 年間純生活費計算
- 推奨月間支出の目安
- 現金が生活費何か月分あるか
- 標準・悲観・楽観シナリオ
- 資産寿命の確認

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

## 注意
このアプリは金融商品の売買を自動で決定するものではなく、入力条件に基づくシミュレーションを提供します。
