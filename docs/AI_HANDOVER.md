# AI HANDOVER

## 現在地
FIRE Compass Sprint 5 実装。

## GitHub
Source of Truth:
https://github.com/lazymethod97-create/fire-compass

Sprint 4完了コミット:
5cd4240d02e4220937f613b156ffdfe3c5cd4857

## Sprint 1〜4
- Streamlit UI
- FIRE資産寿命シミュレーション
- 現金バッファ・追加投資ルール
- 暴落時の防御戦略
- GeminiによるAI FIREアドバイス
- APIキー未設定・APIエラー時はルールベースへフォールバック
- Geminiへ金融計算を任せず、Python側の計算結果だけをAIへ渡す

## Sprint 5実装
ファイル:
- services/tax_optimization.py
- tests/test_tax_optimization.py

機能:
- NISA総枠1,800万円の残りを計算
- NISA成長投資枠1,200万円の残りを計算
- NISA年間投資枠360万円の残りを計算
- iDeCo月額掛金から年間拠出額を計算
- iDeCo上限を入力可能にして制度変更に対応
- 年金受給開始年齢65〜75歳を入力
- 年金受給開始後の年間生活費不足額を計算
- app.pyに入力・結果表示を統合

重要:
- NISA残り総枠は市場評価額ではなく累計投資額（簿価）を基準にする
- iDeCo上限は加入区分等で異なるため、UIから変更可能にする
- 年金は税引後手取りではなく入力された年金見込額をそのまま使用
- 既存のfire_engine.py、action_engine.py、crash_strategy.pyは変更しない

## テスト
Sprint 5追加テスト: 5件

開発環境で以下を実行:
python -m pytest -q

想定:
既存12件 + Sprint 5 5件 = 17件

## 次の作業
1. Streamlit起動確認
2. NISA・iDeCo・年金の入力と結果表示確認
3. python -m pytest -q
4. git status / git diff
5. git add .
6. git commit -m "Complete Sprint 5 NISA iDeCo pension optimization"
7. git push origin main
8. push後にGitHub mainの最新コミットを確認

## 設計方針
1 Sprint = 1主要機能。
既存のFIREシミュレーションを壊さず、税制・年金最適化を独立モジュールで追加する。
