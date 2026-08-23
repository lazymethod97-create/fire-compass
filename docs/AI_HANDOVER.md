# AI HANDOVER

## 現在地
FIRE Compass Sprint 10 実装。

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

## Sprint 15候補（未着手）
- docs/ROADMAP.mdなど各ドキュメントの表記統一・軽微な整理
- JSONファイル保存方式（履歴・ログ）の運用限界の見直し（件数増加時の性能・移行含む）
- ★次回レビュー（Sprint 17）まで、Sprint 10〜13で積み上がったログ関連の
  機能拡張は一旦停止し、ユーザー向け価値（履歴・レポート・比較系）を
  優先する
