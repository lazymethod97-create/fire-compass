# AI HANDOVER

## 現在地
FIRE Compass Sprint 26 実装（Sprint 17 定期レビュー対応完了）。

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

## Sprint 10完了
主要機能:
アプリケーションのイベント・エラーログ機能。

追加:
- services/app_logger.py
- tests/test_app_logger.py
- pages/10_📋_ログ・監視.py

設計:
- Sprint 1〜9の調査の結果、監視・ログ機能が一切存在せず、
  特にGemini APIエラー時（services/ai_advisor.pyのexcept節）に
  失敗理由が記録されない点が最大の運用課題だと判明した
- services/app_logger.pyでイベントをJSON Lines形式でローカルファイル
  （.fire_compass_events.log）へ記録
- 最大500件を超えた古い記録は自動的に切り捨てる（history_manager.pyの
  最大件数管理と同じ考え方）
- ログファイルはGit管理対象外（.gitignoreへ追加）
- 外部送信は一切行わない（Sprint 8のセキュリティ方針を継続）
- fire_engine.pyを変更しない
- action_engine.pyを変更しない
- crash_strategy.pyを変更しない
- tax_optimization.pyを変更しない
- history_manager.pyのロジック本体を変更しない
- report_generator.pyを変更しない
- comparison_engine.pyを変更しない
- security.pyを変更しない（safe_error_messageをそのまま再利用）

最小限の既存ファイル変更（ロジックは変更せず、ログ記録の呼び出しのみ追加）:
- services/ai_advisor.py：
  - APIキー未設定時 → INFOログ
  - Gemini APIから空応答を受け取った時 → WARNINGログ
  - Gemini API呼び出しで例外発生時 → ERRORログ
    （safe_error_messageで安全な文言に変換してから記録し、
    APIキー等の秘密値は記録しない）
  - フォールバックの文章・戻り値・プロンプト内容は一切変更していない
- app.py：
  - シミュレーション実行成功時 → simulation_executedイベント
  - 履歴保存時 → history_savedイベント
  - 履歴の個別削除時 → history_deletedイベント
  - 履歴の全削除時 → history_clearedイベント
  - すべて_safe_log_event()でtry/exceptに包み、ログ記録の失敗が
    アプリ本体の動作へ影響しないようにしている

テスト:
python -m pytest -q
54 passed（既存41件 + Sprint 10 13件）

## 次の作業
1. Streamlit起動確認（🧭 FIRE Compass / 📄 FIREレポート /
   🔒 公開運用・セキュリティ / 📊 シミュレーション比較 / 📋 ログ・監視）
2. シミュレーションを実行し、📋 ログ・監視ページにsimulation_executed
   イベントが記録されることを確認
3. GEMINI_API_KEYを設定せずにシミュレーションを実行し、
   ai_advice_fallback（INFO）が記録されることを確認
4. python -m pytest -q
5. git status / git diff / git diff --check
6. git add .
7. git commit -m "Complete Sprint 10 application event and error logging"
8. git push origin main
9. push後にGitHub mainの最新コミットを確認

## Sprint 11完了
主要機能:
ログ・監視ページからのログCSVエクスポート。

追加・変更:
- services/app_logger.py：
  - export_events_to_csv(events) を追加
    - load_eventsの戻り値（timestamp / level / event_type / message）を
      そのままCSV文字列へ変換するだけの整形専用関数
      （金融計算・AIアドバイスのロジックには一切関与しない）
    - Excel（Windows）で文字化けしないよう、UTF-8 BOM付き・CRLF区切りで出力
    - list以外が渡された場合はValueError、dict以外の要素は無視
  - events_export_filename(level=None) を追加
    - ダウンロード用ファイル名（fire_compass_events_[レベル_]日時.csv）を生成
  - 既存のlog_event / load_events / clear_eventsは変更しない
- pages/10_📋_ログ・監視.py：
  - 「イベント一覧」の下に「ログのエクスポート」セクションを追加
  - 現在選択中のレベルフィルタに従った表示中のログをCSVダウンロード可能に
  - st.download_buttonはSprint 7のレポートページと同じ使い方
  - ログが0件のときはダウンロードボタンをdisabledにする
  - 既存の削除機能・表示ロジックは変更しない

設計:
- fire_engine.pyを変更しない
- action_engine.pyを変更しない
- crash_strategy.pyを変更しない
- tax_optimization.pyを変更しない
- ai_advisor.pyを変更しない
- history_manager.pyを変更しない
- report_generator.pyを変更しない
- security.pyを変更しない
- comparison_engine.pyを変更しない
- app_logger.pyの既存関数（log_event / load_events / clear_events）の
  ロジック自体は変更せず、新規関数を追加するのみ

テスト:
python -m pytest -q
62 passed（既存54件 + Sprint 11 8件）

追加テスト（tests/test_app_logger.py）:
- CSVヘッダー・行の出力確認
- 空リスト時はヘッダーのみ
- list以外の入力でValueError
- dict以外の要素をスキップ
- カンマ・引用符を含むメッセージの正しいエスケープ
- ファイル名生成（デフォルト／レベル指定／不正なレベル指定時の無視）

## 次の作業
1. Streamlit起動確認（🧭 FIRE Compass / 📄 FIREレポート /
   🔒 公開運用・セキュリティ / 📊 シミュレーション比較 / 📋 ログ・監視）
2. 📋 ログ・監視ページで「📥 表示中のログをCSVでダウンロード」ボタンから
   CSVファイルをダウンロードし、Excelで文字化けなく開けることを確認
3. レベルフィルタ（ERROR/WARNING/INFO）を切り替えたとき、
   ダウンロードされるCSVの内容とファイル名が連動することを確認
4. python -m pytest -q
5. git status / git diff / git diff --check
6. git add .
7. git commit -m "Complete Sprint 11 log CSV export"
8. git push origin main（直接push不可のためbundle経由で反映）
9. push後にGitHub mainの最新コミットを確認

## Sprint 12完了
主要機能:
シミュレーション比較結果のCSVエクスポート。

背景（調査結果）:
- Sprint 7（FIREレポート）とSprint 11（ログ）には既にエクスポート機能があるが、
  Sprint 9のシミュレーション比較ページには画面表示のみで、
  比較結果を保存・共有する手段がなかった
- これがSprint 1〜11の中で最も明確な機能不足だったため、Sprint 12として選定した

追加・変更:
- services/comparison_engine.py：
  - format_comparison_value(value, diff, unit) を追加
    - pages/9のセル表示ロジックをそのまま関数化した共通の整形関数
    - 既存のbuild_comparison()のロジックは変更なし
  - export_comparison_to_csv(comparison) を追加
    - Sprint 11のapp_logger.export_events_to_csvと同じ方針
      （UTF-8 BOM付き・CRLF区切りでExcel文字化け対策）
    - ComparisonResult以外が渡された場合はValueError
  - comparison_export_filename() を追加
    - ダウンロード用ファイル名（fire_compass_comparison_日時.csv）を生成
- pages/9_📊_シミュレーション比較.py：
  - セル表示をformat_comparison_value()経由に置き換え（表示結果は変更なし）
  - 「比較結果のエクスポート」セクションを追加し、
    Sprint 11と同じst.download_buttonパターンでCSVダウンロード可能に
  - 既存の選択・比較表示ロジックは変更なし

設計:
- fire_engine.pyを変更しない
- action_engine.pyを変更しない
- crash_strategy.pyを変更しない
- tax_optimization.pyを変更しない
- ai_advisor.pyを変更しない
- history_manager.pyを変更しない
- report_generator.pyを変更しない
- security.pyを変更しない
- app_logger.pyを変更しない
- comparison_engine.pyの既存関数（build_comparison）のロジック自体は
  変更せず、新規関数を追加するのみ
- 金融計算ロジックは一切追加していない（比較結果の整形・出力のみ）

テスト:
python -m pytest -q
70 passed（既存62件 + Sprint 12 8件）

追加テスト（tests/test_comparison_engine.py）:
- format_comparison_valueのNone・数値+差分・差分0・非数値の各ケース
- CSVヘッダー（比較対象/実行日時）とBOM・CRLFの出力確認
- 指標行に差分が正しく含まれること
- ComparisonResult以外を渡した場合のValueError
- ファイル名生成（プレフィックス・拡張子）

## 次の作業
1. Streamlit起動確認（🧭 FIRE Compass / 📄 FIREレポート /
   🔒 公開運用・セキュリティ / 📊 シミュレーション比較 / 📋 ログ・監視）
2. 📊 シミュレーション比較ページで2件以上の履歴を選び、
   比較表がSprint 11以前と同じ内容で表示されることを確認
3. 「📥 比較結果をCSVでダウンロード」ボタンからCSVファイルをダウンロードし、
   Excelで文字化けなく開けることを確認
4. python -m pytest -q
5. git status / git diff / git diff --check
6. git add .
7. git commit -m "Complete Sprint 12 comparison result CSV export"
8. git push origin main（直接push不可のためbundle経由で反映）
9. push後にGitHub mainの最新コミットを確認

## Sprint 13完了
主要機能:
ログのキーワード検索・期間（日付範囲）フィルタ機能。

背景（調査結果）:
- Sprint 11・Sprint 12のAI_HANDOVER.mdの両方で「ログ検索性、期間指定など」が
  未着手候補として繰り返し記録されていた
- 現状の「📋 ログ・監視」ページはレベル（INFO/WARNING/ERROR）でしか絞り込めず、
  ログが増えるほど目的のイベントを見つけにくいという運用課題が残っていた

追加・変更:
- services/app_logger.py：
  - filter_events(events, keyword, start_date, end_date) を追加
    - event_type / messageへのキーワード部分一致（大文字小文字を区別しない）
    - timestampの日付部分（YYYY-MM-DD）による期間絞り込み（開始日・終了日を含む）
    - load_events()の戻り値に対して追加で適用する表示専用の絞り込み関数
    - 既存のlog_event / load_events / clear_events / export_events_to_csvは変更しない
- pages/10_📋_ログ・監視.py：
  - レベル選択の下にキーワード検索欄・開始日/終了日の日付入力を追加
  - load_events()の結果にfilter_events()を適用してから一覧表示・CSV出力に利用
  - 「絞り込み後の件数」を表示
  - 既存の削除機能・CSVエクスポート機能（Sprint 11）の枠組みは変更しない

設計:
- fire_engine.pyを変更しない
- action_engine.pyを変更しない
- crash_strategy.pyを変更しない
- tax_optimization.pyを変更しない
- ai_advisor.pyを変更しない
- history_manager.pyを変更しない
- report_generator.pyを変更しない
- security.pyを変更しない
- comparison_engine.pyを変更しない
- app_logger.pyの既存関数（log_event / load_events / clear_events /
  export_events_to_csv）のロジック自体は変更せず、新規関数を追加するのみ
- 金融計算ロジックは一切追加していない（ログの絞り込み表示のみ）

テスト:
python -m pytest -q
79 passed（既存70件 + Sprint 13 9件）

追加テスト（tests/test_app_logger.py）:
- filter_eventsに非リストを渡した場合のValueError
- キーワードによるevent_type一致・message一致（大文字小文字区別なし）
- キーワード空欄時は全件返却
- 開始日のみ・終了日のみ・期間指定（両方）での絞り込み
- キーワードと期間の組み合わせ絞り込み
- dict以外の要素をスキップ

## 次の作業
1. Streamlit起動確認（🧭 FIRE Compass / 📄 FIREレポート /
   🔒 公開運用・セキュリティ / 📊 シミュレーション比較 / 📋 ログ・監視）
2. 📋 ログ・監視ページでキーワード検索・開始日/終了日を入力し、
   一覧表示とCSVダウンロードの両方に絞り込みが反映されることを確認
3. キーワード・期間を未入力にした場合、Sprint 11以前と同じ挙動（レベルのみで絞り込み）になることを確認
4. python -m pytest -q
5. git status / git diff / git diff --check
6. git add .
7. git commit -m "Complete Sprint 13 log keyword and date range filter"
8. git push origin main（直接push不可のためbundle経由で反映）
9. push後にGitHub mainの最新コミットを確認

## Sprint 14レビュー結果

Sprint 1〜13の全機能を「機能の本当に役立っているか定期レビュー」の
5つの観点（使用頻度・最終ゴールとの直結度・二重表示・初心者の迷いにくさ・
管理系機能の圧迫）で分類した。

- Sprint 1〜5（基本シミュレーション・市場環境別防御・AIアドバイス・
  NISA/iDeCo/年金最適化）：**維持** — 最終ゴールに直結する中核機能
- Sprint 6（履歴保存）：**維持だが要改善** — 保存時にしか名前を付けられず、
  あとから変更できない利便性の穴があった
- Sprint 7（HTMLレポート出力）：**維持**
- Sprint 8（公開セキュリティガード）：**維持**
- Sprint 9（シミュレーション比較）：**維持**
- Sprint 10〜13（ログ記録・CSV・キーワード検索・期間フィルタ）：**維持だが注意**
  — 運用監視に必要だが、4Sprint連続で「FIRE意思決定支援」からやや離れた
  管理系機能が積み上がった。削除は提案しないが、これ以上のログ機能拡張は
  一旦停止し、次はユーザー向け価値へ回帰すべきと判断した

削除・簡略化候補：なし（きたさんの承認が必要な項目は今回発生していない）。

このレビュー結果を踏まえ、唯一「要改善」と特定されたSprint 6の
履歴名称変更機能をSprint 14として選定した。

## Sprint 14完了
主要機能:
保存済み履歴1件の名称をあとから変更できる機能。

背景（レビュー結果）:
- Sprint 6以来、履歴の保存時にしか名前を付けられず、あとから
  「名称未設定」や誤った名前のまま変更できない利便性の穴が残っていた
- Sprint 14候補として過去に挙がっていた「ドキュメント表記統一」「JSON保存方式の
  運用限界見直し」は、それぞれ優先度が低い・時期尚早（件数上限に達していない）
  と判断し見送った

追加・変更:
- services/history_manager.py：
  - rename_history(history_id, new_name, path=None) を追加
    - 指定したhistory_idのレコードのnameフィールドのみを書き換える
    - inputs / results / scenariosなど、シミュレーション結果本体には
      一切関与しない
    - history_idが空の場合、新しい名称が空（前後空白のみ含む）の場合は
      ValueError
    - 対象のhistory_idが見つからない場合はFalseを返す
  - 既存のload_history / save_history / delete_history / clear_historyは
    変更しない
- app.py：
  - 「保存済み履歴」の各カードに、名称変更用のテキスト入力と
    「✏️ 名称変更」ボタンを追加
  - 変更成功時はhistory_renamedイベントをログ記録（_safe_log_event経由）
  - 既存の削除ボタン・全削除ボタンのロジックは変更しない

設計:
- fire_engine.pyを変更しない
- action_engine.pyを変更しない
- crash_strategy.pyを変更しない
- tax_optimization.pyを変更しない
- ai_advisor.pyを変更しない
- report_generator.pyを変更しない
- security.pyを変更しない
- comparison_engine.pyを変更しない
- app_logger.pyを変更しない
- history_manager.pyの既存関数のロジック自体は変更せず、新規関数を
  追加するのみ
- 金融計算ロジックは一切追加していない（表示用の名称変更のみ）

テスト:
python -m pytest -q
84 passed（既存79件 + Sprint 14 5件）

追加テスト（tests/test_history_manager.py）:
- 名称変更後、名称以外のフィールド（id・assetsなど）が変わらないこと
- 前後の空白がトリムされること
- 存在しないhistory_idを指定した場合はFalseを返すこと
- history_idが空の場合はValueError
- 新しい名称が空（空白のみ含む）の場合はValueError

## 次の作業
1. Streamlit起動確認（🧭 FIRE Compass / 📄 FIREレポート /
   🔒 公開運用・セキュリティ / 📊 シミュレーション比較 / 📋 ログ・監視）
2. シミュレーションを保存後、履歴カードの「✏️ 名称変更」ボタンから
   名称が変更されることを確認
3. 名称を空欄にして「✏️ 名称変更」を押すと警告が表示されることを確認
4. python -m pytest -q
5. git status / git diff / git diff --check
6. git add .
7. git commit -m "Complete Sprint 14 history rename"
8. git push origin main（直接push不可のためbundle経由で反映）
9. push後にGitHub mainの最新コミットを確認

## Sprint 15完了
主要機能:
保存済み履歴一覧のCSVエクスポート。

背景（調査結果）:
- Sprint 11（ログCSV）・Sprint 12（比較結果CSV）で既にCSVエクスポートが
  あるが、アプリの中核データであるSprint 6の「保存済み履歴」自体には
  エクスポート手段が一つもなかった
- 履歴は最大20件までしか保持できない仕様（Sprint 6以来）であり、
  上限を超えて古い履歴が自動的に消える前に、手元へ保存しておく手段が
  なかった。JSON保存方式自体の見直し（Sprint 14で時期尚早と判断）を
  行わなくても、エクスポート機能があればこの懸念を実務的に緩和できる
- Sprint 14の「ログ関連機能の拡張はSprint 17まで一旦停止」という方針の
  対象はapp_logger.py（ログ機能）であり、history_manager.py（履歴機能）は
  対象外のため、この方針には反しない
- ドキュメント表記統一は優先度が低いため見送った

追加・変更:
- services/history_manager.py：
  - export_history_to_csv(records) を追加
    - Sprint 11のapp_logger.export_events_to_csv、Sprint 12の
      comparison_engine.export_comparison_to_csvと同じ方針
      （UTF-8 BOM付き・CRLF区切りでExcel文字化け対策）
    - 列の指標名・単位はcomparison_engine.METRIC_DEFSをそのまま再利用し、
      比較ページと同じ表記に揃えた（指標一覧の重複を作らない）
    - list以外が渡された場合はValueError、dict以外の要素は無視
    - resultsが欠けている履歴は「---」で表示
  - history_export_filename() を追加
    - ダウンロード用ファイル名（fire_compass_history_日時.csv）を生成
  - 既存のload_history / save_history / delete_history /
    rename_history / clear_historyは変更しない
- app.py：
  - 「11. 保存・履歴管理」セクションの履歴一覧下に
    「📥 保存済み履歴をCSVでダウンロード」ボタンを追加
  - 既存の保存・名称変更・削除・全削除のロジックは変更しない

設計:
- fire_engine.pyを変更しない
- action_engine.pyを変更しない
- crash_strategy.pyを変更しない
- tax_optimization.pyを変更しない
- ai_advisor.pyを変更しない
- report_generator.pyを変更しない
- security.pyを変更しない
- app_logger.pyを変更しない
- comparison_engine.pyを変更しない（METRIC_DEFS / format_comparison_valueを
  読み取り専用でimportして再利用するのみ）
- history_manager.pyの既存関数のロジック自体は変更せず、新規関数を
  追加するのみ
- 金融計算ロジックは一切追加していない（履歴一覧の整形・出力のみ）

テスト:
python -m pytest -q
91 passed（既存84件 + Sprint 15 7件）

追加テスト（tests/test_history_manager.py）:
- CSVヘッダー・BOM・指標名の出力確認
- 履歴名・実行日時・指標値が正しく出力されること
- resultsが欠けている履歴が「---」で出力されること
- dict以外の要素をスキップすること
- 空リスト時はヘッダーのみ
- list以外の入力でValueError
- ファイル名生成（プレフィックス・拡張子）

## 次の作業
1. Streamlit起動確認（🧭 FIRE Compass / 📄 FIREレポート /
   🔒 公開運用・セキュリティ / 📊 シミュレーション比較 / 📋 ログ・監視）
2. 履歴を1件以上保存し、「📥 保存済み履歴をCSVでダウンロード」ボタンから
   CSVファイルをダウンロードし、Excelで文字化けなく開けることを確認
3. 履歴が0件の場合はダウンロードセクション自体が表示されないことを確認
4. python -m pytest -q
5. git status / git diff / git diff --check
6. git add .
7. git commit -m "Complete Sprint 15 history CSV export"
8. git push origin main（直接push不可のためbundle経由で反映）
9. push後にGitHub mainの最新コミットを確認

## Sprint 16完了
主要機能:
保存済み履歴一覧のキーワード検索・作成日期間フィルタ。

背景（調査結果）:
- Sprint 13でログには「キーワード検索・期間フィルタ」を追加済みだが、
  同じ課題（最大保存件数まで増えると目的のものを見つけにくい）は
  履歴（Sprint 6）にも存在し、未対応のまま残っていた
- 対象はhistory_manager.py（履歴機能）であり、Sprint 14で立てた
  「ログ関連機能の拡張はSprint 17まで一旦停止」の対象
  （app_logger.py／ログ機能）ではないため、その方針には反しない
- 絞り込み結果はSprint 15のCSVエクスポートにも反映することとした
  （きたさんの確認の上、pages/10のログページと同じ挙動に統一）

追加・変更:
- services/history_manager.py：
  - filter_history(records, keyword, start_date, end_date) を追加
    - app_logger.filter_events()（Sprint 13）と同じ設計方針
    - keywordは履歴名（nameフィールド）への部分一致（大文字小文字を
      区別しない）
    - start_date / end_dateはcreated_atの日付部分（先頭10文字）で
      期間を絞り込む（両端を含む）
    - list以外が渡された場合はValueError、dict以外の要素は無視
    - 既存のload_history / save_history / delete_history /
      rename_history / clear_history / export_history_to_csvは
      変更しない
- app.py：
  - 「保存済み履歴」セクションにキーワード検索欄・作成日（開始/終了）の
    日付入力を追加
  - filter_history()の結果を履歴カード一覧・CSVエクスポートの両方に適用
  - 「絞り込み後の件数」を表示
  - 絞り込み後の件数が0件のときはCSVダウンロードボタンをdisabledにする
  - 既存の保存・名称変更・削除・全削除のロジックは変更しない

設計:
- fire_engine.pyを変更しない
- action_engine.pyを変更しない
- crash_strategy.pyを変更しない
- tax_optimization.pyを変更しない
- ai_advisor.pyを変更しない
- report_generator.pyを変更しない
- security.pyを変更しない
- app_logger.pyを変更しない
- comparison_engine.pyを変更しない
- history_manager.pyの既存関数のロジック自体は変更せず、新規関数を
  追加するのみ
- 金融計算ロジックは一切追加していない（履歴一覧の絞り込み表示のみ）

テスト:
python -m pytest -q
99 passed（既存91件 + Sprint 16 8件）

追加テスト（tests/test_history_manager.py）:
- filter_historyに非リストを渡した場合のValueError
- キーワードによるname一致（大文字小文字区別なし）
- キーワード空欄時は全件返却
- 開始日のみ・終了日のみ・期間指定（両方）での絞り込み
- キーワードと期間の組み合わせ絞り込み
- dict以外の要素をスキップ

## 次の作業
1. Streamlit起動確認（🧭 FIRE Compass / 📄 FIREレポート /
   🔒 公開運用・セキュリティ / 📊 シミュレーション比較 / 📋 ログ・監視）
2. 履歴を複数件保存し、履歴名キーワード・作成日（開始/終了）で
   絞り込んだ結果が一覧表示とCSVダウンロードの両方に反映されることを確認
3. キーワード・期間を未入力にした場合、Sprint 15以前と同じ挙動
   （全件表示・全件エクスポート）になることを確認
4. python -m pytest -q
5. git status / git diff / git diff --check
6. git add .
7. git commit -m "Complete Sprint 16 history keyword and date range filter"
8. git push origin main（直接push不可のためbundle経由で反映）
9. push後にGitHub mainの最新コミットを確認

## Sprint 17完了
主要機能:
定期レビュー（3Sprintごと・前回Sprint14）の実施。

背景:
- Sprint16完了時点の「次の作業」で予告されていた、Sprint1〜16全機能の
  再評価（5つの観点：使用頻度・最終ゴールとの直結度・二重表示・混乱リスク・
  初心者の迷いにくさ・管理系機能の圧迫）

結果概要:
- Sprint1〜5（基本シミュレーション・AIアドバイス・NISA/iDeCo/年金最適化）：
  維持。ただし「生活費」を名乗る数値がsection4・5・10の3箇所に分散しており
  （monthly_budget.safe_monthly / strategy.recommended_monthly_spending /
  result.recommended_monthly_spending）、混乱リスクとして指摘
- Sprint6・7・9・14（履歴保存・レポート・比較・履歴名称変更）：維持。ただし
  pages/7_📄_FIREレポート.pyとapp.py内蔵の「📄 レポート」ボタンが
  build_report_html/report_filenameを共に呼び出す完全に同一機能であり、
  二重導線と指摘
- Sprint8（公開セキュリティガード）：機能自体は妥当だが、
  pages/8_🔒_公開運用・セキュリティ.pyが非公開モード時（＝通常のローカル
  個人利用）でも常時サイドバーに表示され続け、無関係な情報として指摘
- Sprint10〜13（ログ記録・CSV・検索・フィルタ）：Sprint14レビューで
  既に「これ以上のログ機能拡張は一旦停止すべき」と結論づけていた方針を
  確認。today時点でも継続の方針
- Sprint15・16（履歴CSV・検索・フィルタ）：Sprint14の凍結方針の対象は
  app_logger.py（ログ機能）のみでhistory_manager.py（履歴機能）は
  対象外という当時の判断自体は筋が通っているが、「Sprint13で実装した
  ものをSprint16で別画面にも横展開する」という対称性駆動のパターンが
  定着しつつある点は要注意。実利用頻度を見てから凍結・縮小を再検討
- 追加指摘（アーキテクチャ）：simple_mode（Sprint20で新設）がapp.py本体
  にしか作用しておらず、pages/8・9・10はStreamlitのpages/方式である限り
  simple_modeの状態と無関係に常時サイドバーへ表示され続けることが判明
- 追加指摘（計算ロジック）：取り崩しプランの
  `monthly_budget.safe_monthly + this_month_large_expense_total`が
  大型支出を二重計上している可能性を指摘されたが、
  monthly_budget_engine.pyのupcoming_large_expenseはガードレール判定
  （green→yellow格下げ）にのみ使用されsafe_monthlyからは減算されない
  ことをコード確認済み。二重計上のバグではないと結論
- 追加指摘：services/配下は既存99件のテストで手厚くカバーされているが、
  session_state・UI分岐・ボタン押下順序が集中するapp.py自体には直接の
  テストが一つもない。今後、Streamlitの`AppTest`等による軽量な統合
  テストの検討価値ありと指摘

削除・簡略化候補：
- pages/7_📄_FIREレポート.py（app.py内蔵ボタンに一本化するため削除）

このレビュー結果を踏まえ、Sprint18〜23として以下を選定した：
1. 前回入力の自動読み込み機能（入力欄の再入力コスト解消）
2. NISA/iDeCo/課税口座欄をセクション3.8へ移動（CSV取り込みが実行前に
   反映されない不具合の修正、Sprint18で判明）
3. 簡易モード＋月次チェックリスト
4. 生活費控除（国保・国民年金・住民税）の概算重ね掛けを目立たせる表示
5. 判定根拠（reasonsタグ）のカテゴリグルーピング
6. レビュー対応（生活費指標の一本化・チェックリストの位置づけ明記・
   レポート導線の統一・pages/8/9/10のsimple_mode/public_mode連携）

## Sprint 18完了
主要機能:
前回保存した入力値を、次回起動時に自動反映する機能。

背景:
- current_age・current_assets・cash_assets・annual_spending・
  prior_year_income等、入力欄がすべてハードコードされた初期値になって
  おり、ブラウザセッションが切れるたび（月1回の起動のたび）に全項目を
  手入力し直す必要があった

追加・変更:
- app.py：
  - `PREVIOUS_INPUT_DEFAULTS`（キー→ハードコード初期値の対応表、
    23項目）を新設
  - 起動時（セッション内で1回だけ）に、保存済み履歴の最新レコードの
    inputsをsession_stateへ`setdefault`で自動反映（履歴になければ
    ハードコード初期値にフォールバック）
  - 対象23ウィジェットを`value=`指定から`key=`指定（session_state経由）
    に統一
  - タイトル下に「🔄 前回の値を読み込み直す」手動ボタンを追加（強制上書き
    ＋再実行）
  - 「現在の市場環境」は自動判定ロジック（Sprint2）を優先するため、
    意図的にこの読み込み対象から除外
  - `latest_simulation["inputs"]`に`prior_year_income`・`household_size`・
    `taxable_gain_ratio_pct`を追加（従来この3項目は履歴に保存されて
    いなかった）

設計:
- fire_engine.py／action_engine.py／crash_strategy.py／
  tax_optimization.py／ai_advisor.py／monthly_budget_engine.py／
  history_manager.pyは変更しない
- 金融計算ロジックは一切変更していない（入力欄の初期値設定のみ）

テスト:
未実行（要対応。app.py側の変更のためservices/配下の既存99件には影響
しない想定だが、実行して確認すること）

## Sprint 19完了
主要機能:
NISA・iDeCo・課税口座の入力欄を、実行ボタンより前のセクション3.8へ移動。

背景（Sprint18中に判明した不具合）:
- 旧「8. NISA・iDeCo・年金最適化」内にあったNISA等の入力欄が、
  「🧭 FIREシミュレーションを実行」ボタン押下後にしか描画されない構造
  だったため、SBI証券CSVをアップロードしてもその場では画面に反映されず、
  一度実行ボタンを押すまで見えなかった

追加・変更:
- app.py：
  - NISA・iDeCo・課税口座の入力欄一式を、旧セクション8から切り出し、
    新設の「3.8. 資産内訳（NISA・iDeCo・課税口座）」として実行ボタン
    直前（3.7の後）に移動
  - 旧セクション8「NISA・iDeCo・年金最適化」は、
    `run_tax_optimization`の計算結果・提案表示のみを行う場所として残す

設計:
- tax_optimization.pyを含む既存の計算モジュールは変更しない
- 変数の再代入・計算式は一切変更せず、UI上の入力欄の位置のみを移動

テスト:
未実行（要対応）

## Sprint 20完了
主要機能:
簡易モード（表示範囲の絞り込み）と月次チェックリスト。

背景:
- セクションが0〜13＋3.5/3.6/3.7/3.8/4.5/12.5の19個に達し、月次で
  「何をどの順番で確認すればいいか」の導線がなかった

追加・変更:
- 新規 services/checklist_state.py：
  - チェックリストの5項目定義（`CHECKLIST_ITEMS`）
  - 表示モード（簡易/詳細）とチェック状態を`.fire_compass_checklist.json`
    へ永続化する`load_checklist_state` / `save_checklist_state` /
    `reset_checklist_items`
  - history_manager.pyと同じ公開モード対応のファイルパス設計
    （公開モード時はセッションIDでファイルを分離）
- app.py：
  - タイトル下に「🗂️ 簡易モード」トグルと5項目チェックボックス、
    「↺ チェックをリセット」ボタンを追加
  - チェック状態・モード設定は次回起動時も保持（月が変わっても自動
    リセットはしない。手動リセットボタンのみ）
  - 簡易モードON時、以下をst.expanderで折りたたみ表示
    （expanded=not simple_mode）：
    - 「📝 入力・資産の確認・編集（0〜3.8）」
    - 「🔍 詳細分析を見る（6〜12）」
    - 「📁 保存・履歴管理（13）」
  - 常時表示のまま残したのは、チェックリスト自体・実行ボタン・
    4/4.5/5/12.5

設計:
- 既存の計算モジュールは一切変更しない。表示の折りたたみとチェック
  リストの追加のみ
- チェックリストは表示用のメモであり、判定計算には使用しない
  （Sprint23でこの旨を画面上にも明記）

テスト:
未実行。checklist_state.pyについてはhistory_manager.pyの既存テスト
（tests/test_history_manager.py）と同じ観点（保存/読込/リセット、
壊れたJSONへの耐性等）でtests/test_checklist_state.pyを追加することを
推奨

## Sprint 21完了
主要機能:
社会保険料・国民年金・住民税の概算重ね掛けを目立たせる表示。

背景:
- 国民健康保険料・国民年金保険料・住民税という3つの全国一律の簡易
  モデルを積み上げて安全生活費から一発で差し引いており、個々には
  「概算です」と注記があるものの、合算後の数字が精密に見えてしまう
  という指摘
- 幅（レンジ）表示も検討したが、全国一律モデルには統計的根拠のある
  上限・下限がないため見送り、「概算であることを目立たせる」方向を採用

追加・変更:
- app.py：
  - section4「安全生活費」のメトリクスラベルに、控除がある場合のみ
    「（概算込み）」を付与
  - 従来2つに分かれていた小さいキャプション（国保・国民年金の注記／
    住民税の注記）を1つの`st.info()`（合計金額つき）に統合
  - section3.7の合計メトリクスのラベルを「合計（月額目安）」→
    「合計（全国一律モデルの概算）」に変更し、常時表示の注記
    キャプションを追加

設計:
- social_insurance_engine.py／resident_tax_engine.py／
  monthly_budget_engine.pyの計算ロジックは一切変更しない。表示文言・
  レイアウトの変更のみ

テスト:
未実行（表示文言のみの変更のためservices/配下への影響はない想定）

## Sprint 22完了
主要機能:
判定根拠（reasonsタグ）のカテゴリグルーピング表示。

背景:
- reasonsタグがSprint追加のたびに場当たり的にフラットな箇条書きへ
  追加されており、今後も増え続ける構造だった

追加・変更:
- services/budget_explanation.py：
  - タグ→カテゴリの対応表`_REASON_CATEGORY`と、カテゴリの表示順・
    ラベル`_CATEGORY_ORDER` / `_CATEGORY_LABELS`を新設
    （生活費調整の主な要因／上限生活費／今月以降の大型支出／
    固定費の控除〈概算〉の4カテゴリ）
  - `BudgetExplanation`を`details: List[str]`から
    `groups: List[BudgetExplanationGroup]`（カテゴリ見出し＋説明文
    リスト）へ変更。該当タグが0件のカテゴリはgroupsに含まれない
- app.py：
  - 「📋 この判定の根拠を見る」の描画を、カテゴリ見出し付きの表示へ
    追従修正

設計:
- monthly_budget_engine.pyのreasonsタグ自体・計算ロジックは変更しない
- 今後タグが増える場合、budget_explanation.py内の対応表に1行追加
  するだけでよく、app.py側は無改修で済む設計

テスト:
実行結果：271 passed, 12 failed（すべてtests/test_budget_explanation.py、
`AttributeError: 'BudgetExplanation' object has no attribute 'details'`）。
テストファイル自体は変更せず、`BudgetExplanation`に`groups`から動的に
組み立てる後方互換の`details`プロパティを追加して対応（Sprint23で修正、
下記参照）

## Sprint 23完了
主要機能:
Sprint17レビュー対応（生活費指標の整理・チェックリストの位置づけ明記・
レポート導線の統一・pages/8/9/10のsimple_mode/public_mode連携）。

背景:
- monthly_budget_engine.pyのupcoming_large_expenseの実装を確認し、
  取り崩しプランの大型支出二重計上疑惑はバグではないと結論（Sprint17の
  項参照）
- 生活費指標の乱立（section4/5/10）はSprint20で10は簡易モードの
  折りたたみに格納済みだったが、section5「市場ルール上の生活費目安」は
  常時表示のままだったため対応
- pages/7とapp.py内蔵レポートボタンの機能重複、pages/8の常時露出、
  simple_modeがpages/に及ばない問題への対応

追加・変更:
- app.py：
  - section5の「市場ルール上の生活費目安」を、目標現金・追加投資額・
    取り崩し額の3列メトリクスから外し、「参考：市場ルール単体での
    生活費目安を見る」という折りたたみへ格下げ
  - 月次チェックリストのキャプションに「このチェックリストは表示用の
    メモであり、FIREの判定計算には一切使用されません」を追記
- pages/7_📄_FIREレポート.py：削除（app.py内蔵の「📄 レポート」
  ボタンに機能を一本化）
- pages/8_🔒_公開運用・セキュリティ.py：
  - `FIRE_COMPASS_PUBLIC_MODE`が無効（非公開モード）の場合は案内文の
    みを表示して`st.stop()`する形に変更。公開モード有効時は従来通り
- pages/9_📊_シミュレーション比較.py／
  pages/10_📋_ログ・監視.py：
  - `st.session_state.get("simple_mode", True)`を参照し、簡易モード中
    は案内文のみを表示して`st.stop()`する形に変更。詳細モードに切替
    後は従来通り使用可能

設計:
- Streamlitの`pages/`方式は、ファイルが存在する限りサイドバー一覧から
  機械的に消すことはできないため、st.navigation()への全面移行（大掛かり
  な方式変更）は見送り、各ページ内でのコンテンツ出し分けにとどめた
- 履歴・ログのCSV/検索/フィルタ機能（Sprint11〜13, 15〜16）は、削除・
  凍結の判断材料となる実利用頻度が不明なため、今回は対応を見送り
  （次回以降、利用実績を踏まえて再検討）
- fire_engine.py／action_engine.py／crash_strategy.py／
  tax_optimization.py／ai_advisor.py／monthly_budget_engine.py／
  history_manager.py／app_logger.py／comparison_engine.py／
  security.pyのロジック自体は変更しない

テスト:
未実行（要対応）

## 次の作業
1. Streamlit起動確認（🧭 FIRE Compass / 🔒 公開運用・セキュリティ /
   📊 シミュレーション比較 / 📋 ログ・監視。📄 FIREレポートは
   pages/7削除により表示されなくなっていることを確認）
2. Sprint18〜23の動作確認項目（各Sprintの本文参照）
3. python -m pytest -q を実行し、Sprint22のBudgetExplanation構造変更
   （details→groups）で既存テストが壊れていないか確認。壊れていれば
   tests/test_budget_explanation.pyを新しい構造に合わせて修正
4. Sprint18〜23で追加したapp.py側のロジック（checklist_state.pyの
   保存・読込、simple_modeのpages/連携等）に対するテストが手薄なため、
   余力があれば追加を検討
5. git status / git diff / git diff --check
6. git add .
7. git commit -m "Complete Sprint 17-23 periodic review and follow-up fixes"
8. git push origin main（直接push不可のためbundle経由で反映）
9. push後にGitHub mainの最新コミットを確認

## Sprint 23追記：pytest実行結果とBudgetExplanationのテスト修正
`python -m pytest -q`実行結果：271 passed, 12 failed。失敗12件は
すべてtests/test_budget_explanation.pyで、Sprint22の`details`→`groups`
変更が原因（`AttributeError: 'BudgetExplanation' object has no
attribute 'details'`）。

対応：
- services/budget_explanation.py：
  - `BudgetExplanation`に、`groups`から都度組み立てる後方互換の
    `details`プロパティ（`@property`）を追加
  - 独自の状態は持たず、`groups`が正のデータソースのまま
  - テストファイル自体は変更していない（`.details`を参照する既存の
    12テストがすべて無改修で通ることを個別に確認済み）

設計:
- fire_engine.py／action_engine.py／crash_strategy.py／
  tax_optimization.py／ai_advisor.py／monthly_budget_engine.pyは
  変更しない

テスト:
上記12件がすべて通ることをロジック単体で確認済み（環境上pytestは
未実行のため、python -m pytest -qで最終確認すること）

## Sprint 24完了
主要機能:
「7. AI FIREアドバイス」に、今月の取り崩し方針（どの口座からいくら・
なぜ取り崩すか）まで踏まえた助言をさせる。

背景:
- きたから「その時々の状況によりいくらまで投資信託を取り崩すのがベストか、
  現金をいくら残すべきか、どのタイミングで投資信託をどれくらい売れば
  いいか、資産の継続性を加味してアドバイスする機能」の要望
- 確認の結果、計算自体はwithdrawal_engine.py（9.今月の取り崩しプラン）・
  crash_strategy.py（5.今月の推奨行動）・fire_engine.py（12.シナリオ
  結果）に既に存在したが、Sprint18〜22で追加されたmonthly_budget
  （4.今月のFIRE判定）・withdrawal_plan（9.）がai_advisor.py側に
  一切渡されておらず、AIアドバイスがSprint4時点の情報のみで喋っていた
  ことが判明。既存セクションに情報を追加する方針（新規セクション新設は
  Sprint17レビューの「二重表示回避」の趣旨に反するため見送り）

追加・変更:
- app.py：
  - セクション8（tax_result）・セクション9（withdrawal_plan）の計算を、
    セクション7（AI FIREアドバイス）より前（strategy/target_cash算出の
    直後）に前倒し。表示位置（サブヘッダーの順序）は変更せず、二重計算に
    ならないよう元の位置にあった計算コードは削除
  - `generate_ai_advice`の呼び出しに`monthly_budget`・`withdrawal_plan`
    を追加
- services/ai_advisor.py：
  - `_withdrawal_steps_text()`を新設。withdrawal_plan.stepsを
    「口座: 金額（税額目安） - 理由」の形式に整形するだけのヘルパー
    （金額の再計算はしない）
  - `_build_fallback_advice()` / `_build_prompt()` /
    `generate_ai_advice()`に`monthly_budget`・`withdrawal_plan`引数を
    追加。フォールバック文に「今月の取り崩し方針」セクションを新設し、
    Gemini側のプロンプトにも同名の出力セクションと
    「【今月のFIRE判定】」「【今月の取り崩しプラン】」の入力ブロックを追加
  - 出力文字数の目安を300〜500字→300〜600字に微調整（セクションが
    1つ増えたため）
  - プロンプトの指示に「【今月の取り崩しプラン】にない口座・金額を
    勝手に追加しない」という制約を明記
  - Sprint23の方針に合わせ、フォールバック文中の
    「推奨月間支出：strategy.recommended_monthly_spending」の表示は
    「安全生活費（4.今月のFIRE判定）：monthly_budget.safe_monthly」に
    差し替え（生活費指標の一本化と整合）

設計:
- fire_engine.py／crash_strategy.py／withdrawal_engine.py／
  monthly_budget_engine.py／tax_optimization.pyの計算ロジックは
  一切変更しない。ai_advisor.pyはこれらの計算結果を文章化するだけ、
  という既存の設計方針を維持
- generate_portfolio_commentary()関連（Sprint29）は変更していない

テスト:
_build_fallback_advice() / _build_prompt()をダミーデータで単体実行し、
例外なく期待通りの文言が生成されることを確認済み（pytestは未実行）。
既存のtests/test_ai_advisor.pyがあれば、generate_ai_advice /
_build_fallback_advice / _build_promptの引数が増えている点の追従修正が
必要な可能性がある

追記（pytest実行後）:
実行結果：279 passed, 4 failed（すべてtests/test_ai_advisor.py、
`monthly_budget`・`withdrawal_plan`を渡さない既存の呼び出しで
`TypeError: missing 2 required positional arguments`）。テストファイルは
変更せず、`generate_ai_advice` / `_build_fallback_advice` /
`_build_prompt`の`monthly_budget`・`withdrawal_plan`をデフォルト値
`None`のキーワード引数に変更して対応。省略時はSprint23以前と完全に
同じ文言・構成を返す（新セクション「今月の取り崩し方針」も省略時は
出力されない）ことをダミーデータで確認済み。

## Sprint 25完了
主要機能:
きたからの「アプリ全体を通した忖度なしレビュー」を受けて、③セクション6の
動的化、⑤入力セクション番号の3ブロック再編、⑥月次チェックリストの
自動連動を実施。

背景:
- レビューで指摘した項目のうち、優先度高（①ポートフォリオ総評の
  スコープ逸脱、②大型支出予定のスコープ逸脱）は継続課題として保留し、
  優先度中〜自己批判の3点（③⑤⑥）から着手することで合意

追加・変更:
- app.py：
  - セクション6「市場環境別の防御ルール」を、通常〜深刻な暴落の4パターン
    全部を毎回再計算して表示する静的な早見表から、**今の市場環境の行
    だけ**を表示する動的なセクションに変更（`calculate_crash_strategy`
    のループ計算をやめ、既に計算済みの`strategy`をそのまま使うだけに
    簡素化）
  - 月次チェックリストの5項目のうち4項目（資産残高の最新化・実行して
    FIRE判定を確認した・今月の推奨行動を確認した・実際に使った金額を
    記録した）を、実際のsession_state・保存データから自動検出して
    チェック済みにするようにした（NISA/iDeCoの枠確認のみ引き続き手動）。
    自動検出の判定材料：CSV取り込み実行の有無
    （`_asset_import_processed_id`）、シミュレーション実行の有無
    （`if run:`内で立てる`_simulation_run_this_session`フラグ）、
    当月分の実績記録の有無（`load_actual_spending`の結果を当月と照合）。
    自動検出された項目はラベルに「（自動検出）」と表示し、手動で外す
    こともできる
  - 入力セクションを、旧「0, 1, 2, 3, 3.5, 3.6, 3.7, 3.8」の8分割から
    「1. 資産（現金・投資・NISA・iDeCo）」「2. 収支・シミュレーション
    条件」「3. 保険料・税金・将来予定」の3ブロックに再編。
    - 1：証券会社CSV取り込み・現在の総金融資産・現金・預金・NISA/
      課税口座/iDeCoの内訳
    - 2：現在年齢・終了年齢・年間生活費・年間副収入・想定利回り・
      インフレ率・安全余裕率・最低現金バッファ・現在の市場環境
    - 3：年金受給開始年齢・年金見込額・社会保険料/住民税の概算・
      今月以降の大型支出予定
    - 各ウィジェットの`key=`・計算ロジックは一切変更せず、配置と
      見出しのみ変更。入力ブロックのexpanderタイトルも
      「（0〜3.8）」→「（1〜3）」に更新
    - 結果セクションは従来通り4から始まるため、1・2・3（入力）→
      4以降（結果）で番号が自然に連続する
    - `run_tax_optimization`呼び出し時の「内訳は「3.7. 社会保険料・
      住民税」で」という文言中の古い番号参照を「3. 保険料・税金・
      将来予定」に修正

設計:
- fire_engine.py／action_engine.py／crash_strategy.py／
  tax_optimization.py／ai_advisor.py／monthly_budget_engine.py／
  withdrawal_engine.py／social_insurance_engine.py／
  resident_tax_engine.py等の計算ロジックは一切変更しない
- checklist_state.py自体（保存ファイルの形式）は変更していない。
  自動検出ロジックはapp.py側にとどめ、checklist_state.pyは
  「チェック状態を保存・読込する」という元の役割のまま

テスト:
未実行（要対応。入力セクションの大規模な再配置のため、
`streamlit run app.py`での目視確認を特に念入りに行うこと）

## Sprint 25追記：pages/9・10のsimple_mode判定バグ修正
きたの報告により、詳細モードに切り替えたあとも「シミュレーション比較」
「ログ・監視」ページで簡易モード用の案内文が表示され続ける不具合が
判明。

原因：
`st.session_state.get("simple_mode", True)`をpages/9・10側で直接
参照していたが、環境によってはmultipage app間でのsession_stateの
反映タイミングにズレが生じ、最新の値が読めていなかった。

対応：
- pages/9_📊_シミュレーション比較.py／
  pages/10_📋_ログ・監視.py：
  - `services.checklist_state.load_checklist_state`をインポートし、
    `CHECKLIST_PATH`定数を追加
  - simple_modeの判定を`st.session_state.get(...)`から
    `load_checklist_state(path=CHECKLIST_PATH)["simple_mode"]`
    （＝永続化ファイルを直接読む）に変更。app.py側のトグルは
    `on_change=_persist_checklist_state`で切り替えるたびに即座に
    ファイルへ書き込んでいるため、session_stateの伝播に依存せず
    確実に最新のモードを反映できる

設計:
- app.py側のsimple_modeトグル・checklist_state.pyのファイル形式は
  変更していない

テスト:
未実行（要確認。きたの環境で「詳細モードに切り替えた状態で
シミュレーション比較・ログ監視ページを開くと、案内文ではなく
本来の内容が表示されるか」を確認すること）

## Sprint 26完了
主要機能:
重大バグ修正（実行後に結果が消える問題）＋ 外部レビュー（PDF提出＋忖度なし
評価）から採用した6件の対応。

背景:
- きたが、外部の別レビュー（実行前のスクリーンショットに基づくPDF評価）を
  提示。レビュー内容を精査した結果、レビューの指摘とは別に、より重大な
  自前のバグを発見した

**🚨重大バグ（最優先で修正）**：
`if run: [セクション4〜12] else: [「このアプリで分かること」]`という
構造で、計算結果がsession_stateにキャッシュされていなかった。
`st.button()`は押した直後の1回しかTrueを返さない仕様のため、実行後に
チェックリストへチェックを入れる等、無関係な操作をしただけで`run`が
再びFalseに戻り、結果セクション（4〜12）がまるごと消えて
「このアプリで分かること」の説明文に差し替わってしまっていた。

**外部レビューの採否判定**（コードで実際に検証したもののみ採用）：
- 採用：①年間生活費と社会保険料・税金の二重計上リスク（検証の結果、
  真のリスクと確認）、②前年所得0円のまま警告がない、③総資産と資産内訳
  の不一致チェックがない、④想定運用利回りが単一値にしか見えない
  （実際は12.シナリオ結果で標準/悲観/楽観の3ケースを既に算出している
  ため、事実誤認ではあるが説明不足だった点のみ対応）、⑤年金の年額/月額
  誤入力リスク、⑥実行ボタンの赤色
- 却下・事実誤認：「利回りが単一値のみ」（12.で3シナリオ算出済み）、
  「サイドバーに公開/ログが常時見える」（Sprint23で非公開モード時は
  案内文のみに縮小済み）
- 保留（規模が大きいため）：結果を画面最上部に配置する大幅レイアウト
  変更、「12.5」「13」等の番号を利用者向けに完全に隠す、履歴・ログ管理
  機能のさらなる整理縮小

追加・変更:
- app.py：
  - `_RUN_SNAPSHOT_KEYS`（実行時に固定する22個の入力値のキー一覧）を
    新設。`run`が押された瞬間の入力値をsession_stateの
    `_last_run_inputs`にスナップショット保存し、`run`が押されていない
    再実行時（チェックリスト操作等）は、このスナップショットから値を
    復元して同じ計算・表示コードをそのまま再利用する形に変更
    （`if run:` → `if run or _has_cached_run:`）。結果は「直前に実行
    した時点の入力値」を反映し続け、入力を変えても再度実行ボタンを
    押すまで結果には反映されない（従来の意図通りの挙動）
  - スナップショットから復元して表示している場合は
    「🔁 直前に「実行」した時点の入力値で、以下の結果を表示しています」
    という案内キャプションを追加
  - 「年間生活費」のラベルを「年間生活費（税・社会保険料を除く）（万円）」
    に変更し、ヘルプテキストで二重計上を明記。「この金額に税・社会保険料
    をすでに含めている」チェックボックスを追加し、チェック時は警告を表示
    （計算ロジック自体は変更せず、入力の手引きと警告のみ）
  - 前年の年間所得目安が0円の場合、初年度の負担を過小評価する可能性が
    ある旨の警告を追加
  - 「1. 資産」ブロックの末尾に、内訳合計（現金＋課税口座＋NISA＋
    iDeCo）と「現在の総金融資産」との差額を常時表示するキャプションを
    追加。差が10万円を超える場合は警告を表示（総資産は内訳から自動
    算出はしない。他の資産を保有している場合の入力を妨げないため）
  - 「想定運用利回り」のヘルプテキストに、実行後は自動的に±2%の悲観・
    楽観ケースも同時にシミュレーションする旨を追記
  - 「65歳時点の年金見込額」の下に、月額換算のキャプションを追加
  - 実行ボタン（`type="primary"`）の色を、Streamlitデフォルトの赤系から
    青系（`#2563eb`）にCSSで上書き。プロジェクト内で`type="primary"`の
    ボタンはこの1つのみのため、他のボタンへの影響はない

設計:
- fire_engine.py／monthly_budget_engine.py／social_insurance_engine.py／
  resident_tax_engine.py等の計算ロジックは一切変更しない
- 二重計上チェックボックスは、計算結果を自動補正するものではなく、
  あくまで警告表示のみ（利用者自身に入力の修正を促す設計。計算ロジックを
  変えるとAI/Python分離の原則に関わる判断が必要になるため、今回は
  入力ガイドの範囲にとどめた）

テスト:
未実行（要対応。特にキャッシュ機構の変更のため、
「実行→チェックリストにチェック→結果が消えないか」を重点的に確認する
こと）

## Sprint 27候補（未着手）
- 履歴・ログのCSV/検索/フィルタ機能の実利用頻度計測、および凍結・縮小の
  再検討（Sprint17レビューで指摘、Sprint23では判断保留）
- app.py自体への軽量な統合テスト導入（Streamlitの`AppTest`等）の検討
  （Sprint17レビューで指摘）
- 大型支出の分散計上機能（3.、旧3.5）を、資産寿命・取り崩し判断の本流
  から切り離した独立オプション機能として明確に位置づけ直すか検討
  （Sprint17レビューで指摘、Sprint25では見送り）
- セクション0（Sprint25で「1. 資産」内の任意項目に格下げ）の
  「保有ファンドのバランス総評」（Sprint29、`generate_portfolio_commentary`）
  が、取り崩し判断という本来のゴールとは別軸の資産配分アドバイスであり、
  CSVアップロードのたびに追加のGemini API呼び出しが発生する点をどう
  扱うか（今回のレビューで指摘、優先度高だが未着手）
- ローカル状態ファイルが6つ（history/events.log/large_expenses/
  judgment_trend/actual_spending/checklist）に増えている点の整理・
  統合検討（今回のレビューで指摘）
- simple_modeの出し分けがapp.py内複数箇所とpages/2ファイルに分散して
  おり、新セクション追加のたびに個別対応が必要な保守コストをどう
  減らすか（今回のレビューで指摘）
- 実行後、結果（今月使える額・残す現金・売却額・行動）を画面最上部に
  配置する大幅なレイアウト変更（外部レビューで指摘。Streamlitの線形
  レンダリング上、入力欄より上に結果を出すには構造変更が必要）
- 「12.5」「13」等のセクション番号を利用者向け画面から完全に隠し、
  目的別の名称（今月の実績、保存したプラン等）のみを表示する
  （外部レビューで指摘。13箇所超のサブヘッダーと相互参照の文言変更が
  必要なため範囲が大きい）
- 履歴・ログ管理機能のUIをさらに折りたたむ・管理者向けメニューへ分離
  するか（外部レビューでも指摘。Sprint17由来の論点と同じ）
  ## Sprint 27：simple_modeガード処理の一元化＋トグル表示ズレバグ修正

### 1. simple_modeガード処理の分散解消
pages/9・10で`if load_checklist_state(...)["simple_mode"]: st.info(...); st.stop()`
という同一パターンがコピペされており、CHECKLIST_PATHの組み立ても
app.py・pages/9・pages/10の3箇所で重複していた。新しいページを
追加するたびに書き忘れるリスクが保守コストになっていた。

対応：
- 新規`services/ui_mode.py`を追加
  - `default_checklist_path()`：プロジェクト直下の既定チェックリスト
    ファイルパスを返す（BASE_DIR算出をこの1箇所に統合）
  - `require_advanced_mode(feature_label, path=None)`：簡易モード中は
    案内文＋`st.stop()`、詳細モードなら何もせず戻る
- pages/9_📊_シミュレーション比較.py／pages/10_📋_ログ・監視.py：
  独自のCHECKLIST_PATH定義とif分岐を削除し、
  `require_advanced_mode("この比較機能")`
  `require_advanced_mode("このログ・監視機能")`の1行呼び出しに置換
- `checklist_state.py`自体は「UI副作用なしの純粋な状態I/O層」という
  性格を保つため変更していない（st.info/st.stopを伴う処理は
  ui_mode.py側に閉じた）
- `tests/test_ui_mode.py`新規追加（4件）

### 2. トグル・チェックリストの表示ズレバグ修正
きたの報告により、簡易モードをONにした状態で「比較」「ログ・監視」
ページへ移動してから「app」ページに戻ると、実際は`simple_mode=true`
のまま（ファイルも正しい）にもかかわらず、トグルスイッチの見た目が
OFFになる不具合が判明。

原因：
`if not st.session_state.get("_checklist_state_loaded"):`という
「セッション中1回だけ」ファイルから`simple_mode`・`checklist_*`を
`session_state`へ読み込むガードが存在していた。simple_mode・
checklist_*の値は`key=`付きウィジェット（`st.toggle`/`st.checkbox`）
に紐づくsession_state値であり、そのウィジェットを描画しないページ
（pages/9・10）を経由するとStreamlit側で値が破棄されることがある。
しかし`_checklist_state_loaded`フラグ自体はウィジェットに紐づかない
ただの真偽値なので破棄されず、appページに戻ってきてもTrueのまま
残る→再読込ブロックがスキップされる→トグルが値なし（デフォルト
False）で描画される、という流れだった。ファイル自体は
`on_change=_persist_checklist_state`が発火しないため書き換わらず、
「ファイルはtrueのままなのに画面だけFalseに見える」という報告と
一致した。同じ理屈でチェックリストの各チェック状態も影響を受ける
可能性がある。

対応：
- app.py内、`_checklist_state_loaded`によるガードを撤廃し、
  `load_checklist_state`の読み込み＋`setdefault`によるsession_state
  反映を、ガードなしで毎回（スクリプト実行のたびに）行うように変更
  - `setdefault`は「まだ値がない場合だけ書き込む」ため、操作中の
    値を上書きする心配はない。JSON読み込みも軽量なので毎回呼んでも
    コスト上の問題はない

設計:
- checklist_state.pyのファイル形式・app.py側のトグル/チェックボックス
  自体のkey構成は変更していない

テスト:
python -m pytest -q 実行結果：287 passed, 1 warning（deprecation、無害）
きた本人による動作確認済み（簡易モードON→比較/ログ画面→app往復で
トグル・チェック状態が正しく維持されることを確認）