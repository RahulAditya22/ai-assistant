import io
import pytest
from app import app
from docagent.database import init_db
@pytest.fixture
def client(tmp_path,monkeypatch):
 db=tmp_path/"test.db";monkeypatch.setattr("docagent.database.DATABASE_PATH",str(db));monkeypatch.setattr("docagent.config.DATABASE_PATH",str(db));init_db();app.config.update(TESTING=True,MAX_CONTENT_LENGTH=2*1024*1024);return app.test_client()
def test_health(client):assert client.get('/health').status_code==200
def test_empty_upload(client):
 r=client.post('/api/upload',data={'file':(io.BytesIO(b''),'empty.txt')},content_type='multipart/form-data');assert r.status_code==422
def test_unsupported_upload(client):
 r=client.post('/api/upload',data={'file':(io.BytesIO(b'abc'),'x.exe')},content_type='multipart/form-data');assert r.status_code==415
def test_question_validation(client):assert client.post('/api/ask',json={'question':''}).status_code==400
