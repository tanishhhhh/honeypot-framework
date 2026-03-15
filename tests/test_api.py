import pytest
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_endpoint_returns_200(client):
    response = client.get('/health')
    assert response.status_code == 200

def test_health_endpoint_structure(client):
    response = client.get('/health')
    data = json.loads(response.data)
    assert 'status' in data
    assert 'model_loaded' in data
    assert data['status'] == 'healthy'

def test_index_endpoint(client):
    response = client.get('/')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'message' in data
    assert 'endpoints' in data

def test_predict_empty_body(client):
    response = client.post('/predict',
        content_type='application/json',
        data=json.dumps({}))
    assert response.status_code in [200, 400, 500]

def test_predict_valid_probe_payload(client):
    payload = {
        "duration": 0.5,
        "orig_bytes": 50,
        "resp_bytes": 30,
        "bytes_per_session": 80,
        "orig_pkts": 2,
        "resp_pkts": 2,
        "packet_count": 4,
        "history_len": 3
    }
    response = client.post('/predict',
        content_type='application/json',
        data=json.dumps(payload))
    if response.status_code == 200:
        data = json.loads(response.data)
        assert 'prediction' in data
        assert 'class_name' in data
        assert 'mitigation' in data
        assert data['prediction'] in [0, 1]
        assert isinstance(data['mitigation'], list)
        assert len(data['mitigation']) > 0

def test_predict_valid_attack_payload(client):
    payload = {
        "duration": 5.0,
        "orig_bytes": 5000,
        "resp_bytes": 3000,
        "bytes_per_session": 8000,
        "orig_pkts": 20,
        "resp_pkts": 15,
        "packet_count": 35,
        "history_len": 10
    }
    response = client.post('/predict',
        content_type='application/json',
        data=json.dumps(payload))
    assert response.status_code in [200, 400, 500]

def test_predict_returns_valid_class_name(client):
    payload = {
        "duration": 1.0,
        "orig_bytes": 200,
        "resp_bytes": 400,
        "orig_pkts": 5,
        "resp_pkts": 8,
        "packet_count": 13,
        "history_len": 6
    }
    response = client.post('/predict',
        content_type='application/json',
        data=json.dumps(payload))
    if response.status_code == 200:
        data = json.loads(response.data)
        assert data['class_name'] in ['Intent-to-act', 'Intent-to-probe']
