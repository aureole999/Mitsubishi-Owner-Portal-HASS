# Mitsubishi Owner Portal for Home Assistant

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)
[![hacs][hacsbadge]][hacs]

Home Assistant用の三菱オーナーポータル（日本）カスタム統合。

この統合により、公式の[三菱オーナーポータル](https://connect.mitsubishi-motors.co.jp/) APIを通じて三菱電気自動車を監視できます。

[English Documentation](README.md) | [简体中文文档](README_CN.md)

## 機能

- バッテリー残量の監視
- 充電状態
- 充電モード
- プラグ接続状態
- 充電準備完了
- フル充電までの時間
- イグニッション状態
- イベントタイムスタンプの追跡
- 航続距離（電気・ガソリン・総合）
- 位置情報追跡
- 走行距離計
- ドアステータス
- セキュリティアラーム
- 車両温度

## インストール

### HACS（推奨）

1. Home AssistanceインスタンスでHACSを開く
2. 「統合」をクリック
3. 右上の三点メニューをクリック
4. 「カスタムリポジトリ」を選択
5. このリポジトリのURLを追加：`https://github.com/aureole999/Mitsubishi-Owner-Portal-HASS`
6. カテゴリとして「統合」を選択
7. 「追加」をクリック
8. リストから「Mitsubishi Owner Portal」を見つけて「ダウンロード」をクリック
9. Home Assistantを再起動

### 手動インストール

1. [リリースページ][releases]から最新リリースをダウンロード
2. `custom_components/mitsubishi_owner_portal` フォルダを展開
3. Home Assistantの `custom_components` ディレクトリにコピー
4. Home Assistantを再起動

## 設定

この統合はUIを通じて設定されます：

1. 設定 → デバイスとサービスに移動
2. 「+ 統合を追加」をクリック
3. 「Mitsubishi Owner Portal」を検索
4. 三菱オーナーポータルの認証情報（メールアドレスとパスワード）を入力
5. 「送信」をクリック

車両は自動的に検出され、Home Assistantに追加されます。

### SSL証明書の検証

デフォルトでは、統合はSSL証明書を検証します。証明書エラーが発生した場合：

1. 統合設定で「SSL証明書を検証」オプションを無効にできます
2. または、統合オプションで設定を変更できます

**注意：** セキュリティ上の理由から、SSL検証を無効にすることは推奨されません。

## 対応センサー

この統合は各車両に対して以下のセンサーを作成します：

### バッテリーと充電

| センサー | 説明 | 単位 |
|---------|------|-----|
| 現在のバッテリー残量 | バッテリーの充電状態 | % |
| 充電状態 | 現在の充電状態 | - |
| 充電プラグ状態 | プラグ接続状態 | - |
| 充電モード | 充電モード | - |
| 充電準備完了 | 充電準備状態 | - |
| フル充電までの時間 | フル充電までの残り時間 | 分 |
| 最終更新時刻 | 最後の更新タイムスタンプ | - |

### 航続距離情報

| センサー | 説明 | 単位 |
|---------|------|-----|
| 総航続距離 | 総合航続距離 | km |
| ガソリン航続距離 | ガソリン航続距離 | km |
| 電気航続距離 | 電気（EV）航続距離 | km |

### 車両状態

| センサー | 説明 | 単位 |
|---------|------|-----|
| イグニッション状態 | 車両イグニッション状態 | - |
| イグニッション状態時刻 | イグニッション状態変更時刻 | - |
| 走行距離計 | 走行距離 | km |
| 走行距離計更新時刻 | 走行距離計最終更新時刻 | - |

### 位置情報

| センサー | 説明 | 単位 |
|---------|------|-----|
| 位置（緯度） | 車両の緯度座標 | - |
| 位置（経度） | 車両の経度座標 | - |
| 位置更新時刻 | 位置情報最終更新時刻 | - |

### セキュリティとステータス

| センサー | 説明 | 単位 |
|---------|------|-----|
| 盗難警報 | 盗難警報状態 | - |
| 盗難警報タイプ | 盗難警報の種類 | - |
| プライバシーモード | プライバシーモード状態 | - |
| 車両温度 | 車内温度 | °C |
| 車両アクセス可能 | 車両アクセス可否 | - |
| ドア状態 | ドアの状態 | - |
| 診断状態 | 診断ステータス | - |

## 要件

- Home Assistant 2024.1.0以降
- 有効な[三菱オーナーポータル](https://connect.mitsubishi-motors.co.jp/)アカウント（日本）
- アカウントに登録された三菱電気自動車

## 動作確認済み車両

この統合は以下の車両でテストされています：
- **三菱アウトランダーPHEV（2022年以降）**

**注意：** 他の三菱車両との互換性は保証されません。三菱オーナーポータルに対応している他の車両でも動作する可能性がありますが、車両モデルや年式によって機能やセンサーが異なる場合があります。

## トラブルシューティング

### 認証に失敗する

- 認証情報が正しいことを確認してください
- アカウントが公式の三菱オーナーポータルウェブサイトで機能することを確認してください
- 車両がアカウントに適切に登録されていることを確認してください

### センサーが更新されない

- インターネット接続を確認してください
- 三菱オーナーポータルに車両の最新データがあることを確認してください
- Home Assistantのログでエラーメッセージを確認してください

### SSL証明書エラー

SSL証明書エラーが発生した場合：

1. システムのCA証明書が最新であることを確認してください
2. ネットワーク接続とファイアウォール設定を確認してください
3. 統合設定で「SSL証明書を検証」を無効にすることができます（推奨されません）
4. 問題が解決しない場合は、三菱のテクニカルサポートに連絡してください

統合は自動的に修復問題と通知を作成し、SSL証明書エラーについて通知します。

## 認証情報の更新

組み込みの再設定フローを使用してください：

1. 統合設定に移動
2. 「再設定」をクリック
3. 新しい認証情報を入力
4. 統合が自動的にリロードされます

または、統合オプションでパスワードとSSL設定を更新できます。

## サポート

問題が発生した場合や質問がある場合：

1. [既存の問題][issues]を確認してください
2. 問題に関する詳細情報を含む新しい問題を作成してください
3. Home Assistantからの関連ログを含めてください

## 貢献

貢献を歓迎します！プルリクエストをお気軽に提出してください。

## ライセンス

このプロジェクトはMITライセンスの下でライセンスされています - 詳細については[LICENSE](LICENSE)ファイルを参照してください。

## クレジット

この統合は三菱自動車工業株式会社と提携または承認されていません。

---

[releases-shield]: https://img.shields.io/github/release/aureole999/Mitsubishi-Owner-Portal-HASS.svg?style=for-the-badge
[releases]: https://github.com/aureole999/Mitsubishi-Owner-Portal-HASS/releases
[commits-shield]: https://img.shields.io/github/commit-activity/y/aureole999/Mitsubishi-Owner-Portal-HASS.svg?style=for-the-badge
[commits]: https://github.com/aureole999/Mitsubishi-Owner-Portal-HASS/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/aureole999/Mitsubishi-Owner-Portal-HASS.svg?style=for-the-badge
[issues]: https://github.com/aureole999/Mitsubishi-Owner-Portal-HASS/issues
