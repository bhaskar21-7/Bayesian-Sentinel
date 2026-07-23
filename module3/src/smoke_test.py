"""
smoke_test.py
-------------
Minimal smoke test that catches ImportErrors and function-call failures in
dashboard_common.py before a human notices them live.

Usage:
    cd module3/src && python smoke_test.py

Prerequisites:
    Module 1 + Module 2 must be trained, and build_dataset.py must have
    been run, so that module3/data/unified_threat_data.csv and the
    surrogate model exist.

Exit code 0 = PASS, 1 = FAIL.
"""

import os
import sys
import traceback
from pathlib import Path

# Ensure sys.path includes module3/src
SRC_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC_DIR))

PASS = True
results = []


def run_check(name, fn):
    """Run fn(), record PASS/FAIL, print immediately without unicode issues."""
    global PASS
    try:
        res = fn()
        results.append((name, "PASS", None))
        print(f"  [PASS] {name}")
        return res
    except Exception as e:
        PASS = False
        tb = traceback.format_exc()
        results.append((name, "FAIL", str(e)))
        print(f"  [FAIL] {name}: {e}")
        return None


def main():
    global PASS
    print("\n=== Smoke Test: Module 3 Dashboard ===\n")

    # 1. Dataset file check
    data_path = SRC_DIR.parent / "data" / "unified_threat_data.csv"
    def check_file():
        if not data_path.exists():
            raise FileNotFoundError(f"Dataset not found at {data_path}. Run build_dataset.py first.")
        return True

    run_check("Dataset file exists", check_file)

    # 2. Import dashboard_common
    dc = run_check("Import dashboard_common", lambda: __import__("dashboard_common"))
    if dc is None:
        print("\n[FAIL] Could not import dashboard_common.py. Aborting.")
        sys.exit(1)

    # 3. Load dataset via get_dataset()
    def check_get_dataset():
        df = dc.get_dataset()
        if df.empty:
            raise ValueError("get_dataset() returned an empty DataFrame.")
        return df

    df = run_check("get_dataset() returns non-empty DataFrame", check_get_dataset)
    if df is None:
        print("\n[FAIL] Dataset loading failed. Aborting remaining tests.")
        sys.exit(1)
    print(f"         Loaded {len(df)} threat rows.")

    # 4. Import xai_engine
    xe = run_check("Import xai_engine", lambda: __import__("xai_engine"))
    if xe is None:
        print("\n[FAIL] Could not import xai_engine.py. Aborting remaining tests.")
        sys.exit(1)

    # 5. Call each cached_* function once against real built dataset
    run_check("cached_global_feature_importance()", dc.cached_global_feature_importance)
    run_check("cached_local_shap(row_index=0)", lambda: dc.cached_local_shap(0))
    
    # Use first valid feature name from SHAP global importance
    imp_df = dc.cached_global_feature_importance()
    feat_name = imp_df["feature"].iloc[0] if (imp_df is not None and not imp_df.empty) else "burst_score"
    run_check(f"cached_dependence_data('{feat_name}')", lambda: dc.cached_dependence_data(feat_name))

    run_check("shap_base_value()", dc.shap_base_value)

    # Check LIME explanation
    run_check("cached_lime_explanation(row_index=0)", lambda: dc.cached_lime_explanation(0))

    # Summary
    print(f"\n{'=' * 42}")
    passed_count = sum(1 for _, s, _ in results if s == "PASS")
    failed_count = sum(1 for _, s, _ in results if s == "FAIL")
    print(f"Results: {passed_count} passed, {failed_count} failed")

    if PASS:
        print("\n[PASS] ALL SMOKE TESTS PASSED CLEANLY.")
        sys.exit(0)
    else:
        print("\n[FAIL] SMOKE TEST FAILED.")
        sys.exit(1)


if __name__ == "__main__":
    main()
