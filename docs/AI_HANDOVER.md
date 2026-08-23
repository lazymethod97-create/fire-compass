# AI HANDOVER

## 現在地
FIRE Compass Sprint 9 実装。

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

## Sprint 6実装方針

機能:
- FIREシミュレーション結果の保存
- JSON形式の履歴管理
- 最大20件
- 履歴一覧表示
- 個別削除
- 全履歴削除

追加:
- services/history_manager.py
- tests/test_history_manager.py

重要:
- fire_engine.pyは変更しない
- action_engine.pyは変更しない
- crash_strategy.pyは変更しない
- tax_optimization.pyは変更しない
- AI計算ロジックは変更しない
- 履歴ファイルは .fire_compass_history.json
- 履歴ファイルはGit管理しない

## Sprint 7完了

主要機能:
保存済みFIREシミュレーション履歴のレポート出力。

追加:
- services/report_generator.py
- tests/test_report_generator.py
- pages/7_📄_FIREレポート.py

設計:
- Sprint 6の履歴データを再利用
- fire_engine.pyを変更しない
- action_engine.pyを変更しない
- crash_strategy.pyを変更しない
- tax_optimization.pyを変更しない
- ai_advisor.pyを変更しない
- history_manager.pyを変更しない
- 新規依存関係を追加しない
- HTMLレポートとして独立
- ブラウザの印刷機能でPDF化可能
- 金融商品の売買を断定しない注意事項を表示

テスト:
python -m pytest -q
25 passed

次Sprint:
Sprint 8 — 公開化・セキュリティ・監視

## Sprint 8完了
主要機能:
公開環境セキュリティガード。

追加:
- services/security.py
- tests/test_security.py
- tests/test_history_public_mode.py
- pages/8_🔒_公開運用・セキュリティ.py

設計:
- FIRE_COMPASS_PUBLIC_MODE で公開モードを判定
- 公開モード時の履歴をStreamlitセッション単位へ分離
- セッションIDはSHA-256でハッシュ化
- セッションIDを取得できない場合は共有履歴ファイルへ書き込まない
- GEMINI_API_KEYの値自体は画面へ表示しない
- safe_error_messageで内部情報を利用者へ返さない
- fire_engine.pyを変更しない
- action_engine.pyを変更しない
- crash_strategy.pyを変更しない
- tax_optimization.pyを変更しない
- ai_advisor.pyを変更しない
- report_generator.pyを変更しない

テスト:
python -m pytest -q
32 passed

## Sprint 9完了
主要機能:
保存済みシミュレーション履歴の比較表示（2〜4件）。

追加:
- services/comparison_engine.py
- tests/test_comparison_engine.py
- pages/9_📊_シミュレーション比較.py

設計:
- Sprint 6の履歴データ（history_manager.load_history）をそのまま再利用
- 主要指標（資産寿命判定・純年間支出・推奨月間支出・現金生活費・目標現金・
  追加投資額・取り崩し額・今月の推奨行動・年金開始後の年間不足・
  NISA/iDeCo関連）を並べて表示
- 先頭の履歴を基準に数値項目の差分を表示（非数値項目は差分なし）
- 比較件数は2〜4件（それ未満・超過はエラーメッセージで案内）
- fire_engine.pyを変更しない
- action_engine.pyを変更しない
- crash_strategy.pyを変更しない
- tax_optimization.pyを変更しない
- ai_advisor.pyを変更しない
- report_generator.pyを変更しない
- security.pyを変更しない
- history_manager.pyの既存関数（load_history / clear_history）をそのまま利用し、
  ロジック自体は変更しない
- 金融計算ロジックは一切追加していない（保存済み結果の整形・表示のみ）

付随バグ修正（既存機能修復）:
- app.pyの「🗑️ 全履歴を削除」ボタンが `Path` 未importのため
  実行時に NameError でクラッシュしていた不具合を修正
- 修正後は history_manager.clear_history() を利用し、公開モード時の
  Streamlitセッション単位の履歴分離（Sprint 8）にも整合する動作にした
- 新規ロジックの追加ではなく、既存の clear_history() を呼び出すだけの最小修正

テスト:
python -m pytest -q
41 passed（既存32件 + Sprint 9 9件）

## 次の作業
1. Streamlit起動確認（🧭 FIRE Compass / 📄 FIREレポート / 🔒 公開運用・セキュリティ / 📊 シミュレーション比較）
2. 履歴を2件以上保存し、シミュレーション比較ページで表示確認
3. 「🗑️ 全履歴を削除」ボタンがエラーなく動作することを確認
4. python -m pytest -q
5. git status / git diff / git diff --check
6. git add .
7. git commit -m "Complete Sprint 9 simulation comparison view"
8. git push origin main
9. push後にGitHub mainの最新コミットを確認

## Sprint 10候補（未着手）
- 監視・ログ機能の強化（アクセスログ、エラーログの外部連携）
- docs/ROADMAP.mdのSprint 8欄の文字化け修正（別Sprintでの軽微修正候補）
