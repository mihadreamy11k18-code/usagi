"""JSON storage for local development or three existing Google Drive files."""
import io
import json
import os
import tempfile
from pathlib import Path

import streamlit as st


NAMES = {"rabbits.json", "foods.json", "meal_records.json"}


def _configuration():
    try:
        account = st.secrets.get("gcp_service_account")
        files = st.secrets.get("drive_files")
    except FileNotFoundError:
        account = files = None
    if bool(account) != bool(files):
        raise ValueError("Google Drive設定が不完全です。サービスアカウントと3つのファイルIDを確認してください。")
    if account:
        missing = NAMES.difference(files.keys())
        if missing:
            raise ValueError("Google DriveのファイルIDが不足しています：" + ", ".join(sorted(missing)))
    return account, files


def _service(account):
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    credentials = service_account.Credentials.from_service_account_info(
        dict(account), scopes=["https://www.googleapis.com/auth/drive"]
    )
    return build("drive", "v3", credentials=credentials, cache_discovery=False)


def read_list(path):
    path = Path(path)
    account, files = _configuration()
    if account:
        try:
            content = _service(account).files().get_media(fileId=files[path.name]).execute()
            value = json.loads(content.decode("utf-8-sig"))
        except Exception as exc:
            raise ValueError(f"Google Driveの {path.name} を読み込めませんでした：{exc}") from exc
    else:
        if not path.exists():
            raise ValueError(f"{path.name} が見つかりません。Google Drive設定またはローカルファイルを確認してください。")
        with path.open(encoding="utf-8") as file:
            value = json.load(file)
    if not isinstance(value, list):
        raise ValueError(f"{path.name} は配列形式で保存してください。")
    return value


def write_records(records, path):
    path = Path(path)
    account, files = _configuration()
    if account:
        from googleapiclient.http import MediaIoBaseUpload

        content = json.dumps(records, ensure_ascii=False, indent=4).encode("utf-8")
        media = MediaIoBaseUpload(io.BytesIO(content), mimetype="application/json", resumable=False)
        try:
            _service(account).files().update(
                fileId=files[path.name], media_body=media, fields="id"
            ).execute()
        except Exception as exc:
            raise ValueError(f"Google Driveの {path.name} を保存できませんでした：{exc}") from exc
        return
    descriptor, name = tempfile.mkstemp(prefix=".meal_records_", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as file:
            json.dump(records, file, ensure_ascii=False, indent=4)
            file.flush()
            os.fsync(file.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)
