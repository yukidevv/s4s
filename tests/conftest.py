import os
import sys

import pytest

# プロジェクトルートを import パスに追加（db / util / api を解決するため）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.db import StartsDB


@pytest.fixture
def db(tmp_path):
  """テストごとに隔離した一時ファイル DB を返す。"""
  db_path = str(tmp_path / "test.db")
  database = StartsDB(db_path=db_path)
  yield database
  database.conn.close()
