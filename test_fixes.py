"""
Smoke-test for data_loader.py and feature_eng.py fixes.
Run from the project root:
    python test_fixes.py
"""
import sys, os

sys.path.insert(0, r"c:\Users\tnshp\.gemini\antigravity\playground\Ml-Honeypot-Framework")

from src.data_loader import load_data, DB_PATH
from src.feature_eng import FeatureEngineer
import pandas as pd

PASS = 0
FAIL = 0

def check(desc, condition):
    global PASS, FAIL
    if condition:
        print(f"  PASS: {desc}")
        PASS += 1
    else:
        print(f"  FAIL: {desc}")
        FAIL += 1

# -- Test 1: data_loader.py --
print("\n=== TEST 1: data_loader.py ===")
try:
    df = load_data(DB_PATH)
    check("Returns a DataFrame", isinstance(df, pd.DataFrame))
    check("Has 8 columns", len(df.columns) == 8)
    expected_cols = {'duration','orig_bytes','resp_bytes','orig_pkts','resp_pkts','proto','conn_state','history'}
    check("Has correct column names", set(df.columns) == expected_cols)
    check("orig_bytes is int32", df['orig_bytes'].dtype == 'int32')
    check("resp_bytes is int32", df['resp_bytes'].dtype == 'int32')
    check("orig_pkts  is int16", df['orig_pkts'].dtype  == 'int16')
    check("resp_pkts  is int16", df['resp_pkts'].dtype  == 'int16')
    check("Row count > 0", len(df) > 0)
except Exception as e:
    print(f"  FAIL: data_loader failed: {e}")
    FAIL += 1

# -- Test 2: feature_eng leakage fix --
print("\n=== TEST 2: feature_eng.py - leakage fix ===")
try:
    fe = FeatureEngineer(df.head(1000))
    X, y = fe.get_processed_data()
    check("bytes_per_session NOT in X", 'bytes_per_session' not in X.columns)
    conn_state_cols = [c for c in X.columns if c.startswith('conn_state')]
    check("No conn_state_* columns in X", len(conn_state_cols) == 0)
    proto_cols = [c for c in X.columns if c.startswith('proto_')]
    check("proto_* columns present in X", len(proto_cols) > 0)
    check("Target has 0 and 1 values", set(y.unique()).issubset({0, 1}))
except Exception as e:
    print(f"  FAIL: feature_eng leakage test failed: {e}")
    FAIL += 1

# -- Test 3: get_inference_features --
print("\n=== TEST 3: feature_eng.py - get_inference_features() ===")
try:
    fe2 = FeatureEngineer(df.head(100))
    X_inf = fe2.get_inference_features()
    check("Returns a DataFrame (not tuple)", isinstance(X_inf, pd.DataFrame))
    check("bytes_per_session NOT in inference X", 'bytes_per_session' not in X_inf.columns)
    conn_state_inf = [c for c in X_inf.columns if c.startswith('conn_state')]
    check("No conn_state_* in inference X", len(conn_state_inf) == 0)
except Exception as e:
    print(f"  FAIL: get_inference_features test failed: {e}")
    FAIL += 1

# -- Summary --
print(f"\n{'='*40}")
print(f"Results: {PASS} passed, {FAIL} failed")
if FAIL == 0:
    print("All tests passed!")
else:
    print("Some tests failed")
    sys.exit(1)
