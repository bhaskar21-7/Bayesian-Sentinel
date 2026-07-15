"""
module_bridge.py
------------------
Calls Module 1, Module 2, and Module 3's real, shipped functions in isolated
subprocesses. Same rationale as Module 3's module_bridge.py: module1/src,
module2/src, module3/src, and module4/src all define files named utils.py
(and 1/2 also share predict.py) — importing more than one into the same
interpreter silently corrupts whichever module's utils/predict "loses" the
sys.modules race. Subprocess isolation, with data exchanged via temp JSON
files, sidesteps this entirely.

Enhanced with detailed error diagnostics to aid debugging when subprocess
calls fail.
"""

import json
import os
import subprocess
import sys
import tempfile
import time

import pandas as pd

from utils import get_logger

logger = get_logger("module_bridge")

MODULE1_SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "module1", "src"))
MODULE2_SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "module2", "src"))
MODULE3_SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "module3", "src"))


def _run_isolated(module_name: str, module_src: str, runner_body: str, args: list, timeout: int = 300):
    """
    Execute a runner script in an isolated subprocess.
    
    Args:
        module_name: Display name (e.g., "Module 1")
        module_src: Path to the module's src directory
        runner_body: Python code to execute in subprocess
        args: Arguments passed to the runner script
        timeout: Subprocess timeout in seconds
    
    Returns:
        None on success.
    
    Raises:
        RuntimeError: on subprocess failure, with detailed diagnostics.
    """
    if not os.path.isdir(module_src):
        raise FileNotFoundError(
            f"[{module_name}] {module_src} not found. This bridge expects module1/, module2/, module3/, and "
            f"module4/ to sit side by side in the same parent directory."
        )
    
    cmd = [sys.executable, "-c", runner_body, module_src] + args
    start_time = time.time()
    
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=timeout, cwd=module_src
        )
        elapsed = time.time() - start_time
        
        if proc.returncode == 0:
            logger.debug(f"[{module_name}] Subprocess succeeded in {elapsed:.2f}s")
            return
        
        # Non-zero exit code: construct detailed error message
        error_lines = [
            f"[{module_name}] Subprocess exited with code {proc.returncode} (after {elapsed:.2f}s)",
            f"Working directory: {module_src}",
        ]
        
        if proc.stderr:
            # Try to identify the failure type from stderr
            if "FileNotFoundError" in proc.stderr or "ModuleNotFoundError" in proc.stderr:
                error_lines.append("Failure type: Missing file or module")
            elif "JSON" in proc.stderr:
                error_lines.append("Failure type: JSON parsing error")
            elif "AttributeError" in proc.stderr or "KeyError" in proc.stderr:
                error_lines.append("Failure type: Missing data or attribute")
            
            stderr_lines = proc.stderr.strip().split("\n")
            # Show last N lines of stderr (most recent/relevant)
            max_lines = 15
            if len(stderr_lines) > max_lines:
                error_lines.append(f"Stderr (last {max_lines} lines):")
                error_lines.extend(stderr_lines[-max_lines:])
            else:
                error_lines.append("Stderr:")
                error_lines.extend(stderr_lines)
        
        if proc.stdout:
            stdout_lines = proc.stdout.strip().split("\n")
            # Show first part of stdout (may contain useful debug info)
            max_lines = 5
            if len(stdout_lines) > max_lines:
                error_lines.append(f"Stdout (first {max_lines} lines):")
                error_lines.extend(stdout_lines[:max_lines])
                error_lines.append("...")
            else:
                error_lines.append("Stdout:")
                error_lines.extend(stdout_lines)
        
        error_msg = "\n".join(error_lines)
        raise RuntimeError(error_msg)
    
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        raise RuntimeError(
            f"[{module_name}] Subprocess timeout after {elapsed:.1f}s (limit: {timeout}s)\n"
            f"Working directory: {module_src}\n"
            f"The module may be computationally expensive or stuck in an infinite loop."
        )
    except Exception as e:
        elapsed = time.time() - start_time
        raise RuntimeError(
            f"[{module_name}] Subprocess execution failed after {elapsed:.2f}s: {type(e).__name__}: {e}\n"
            f"Working directory: {module_src}"
        ) from e


# -------- Module 1: predict_network_anomaly(df) -> anomaly_score, risk_level, feature_vector --------
_MODULE1_RUNNER = r"""
import sys, json, pandas as pd
sys.path.insert(0, sys.argv[1])
from predict import predict_network_anomaly
with open(sys.argv[2]) as f:
    rows = pd.read_json(f, orient="records")
rows["timestamp"] = pd.to_datetime(rows["timestamp"])
result = predict_network_anomaly(rows)
if isinstance(result, dict):
    result = [result]
with open(sys.argv[3], "w") as f:
    json.dump(result, f)
"""


def call_module1_predict_network_anomaly(rows_df: pd.DataFrame) -> list:
    """Predict network anomalies for a batch of network logs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        in_path = os.path.join(tmpdir, "rows.json")
        out_path = os.path.join(tmpdir, "result.json")
        
        try:
            rows_df.to_json(in_path, orient="records", date_format="iso")
        except Exception as e:
            raise RuntimeError(f"[Module 1] Failed to serialize input DataFrame: {e}") from e
        
        _run_isolated("Module 1", MODULE1_SRC, _MODULE1_RUNNER, [in_path, out_path])
        
        try:
            with open(out_path) as f:
                result = json.load(f)
            return result
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"[Module 1] Output JSON is invalid: {e}\n"
                f"Output file: {out_path}\n"
                f"This usually means the subprocess crashed after writing partial data."
            ) from e
        except FileNotFoundError as e:
            raise RuntimeError(
                f"[Module 1] Output file not created: {out_path}\n"
                f"Subprocess may have exited before writing results."
            ) from e


# -------- Module 2: predict_phishing(texts) -> phishing_probability --------
_MODULE2_PHISHING_RUNNER = r"""
import sys, json
sys.path.insert(0, sys.argv[1])
from phishing_detector import predict_phishing
with open(sys.argv[2]) as f:
    texts = json.load(f)
result = predict_phishing(texts)
if isinstance(result, dict):
    result = [result]
with open(sys.argv[3], "w") as f:
    json.dump(result, f)
"""


def call_module2_predict_phishing(texts: list) -> list:
    """Classify texts for phishing content."""
    with tempfile.TemporaryDirectory() as tmpdir:
        in_path = os.path.join(tmpdir, "texts.json")
        out_path = os.path.join(tmpdir, "result.json")
        
        try:
            with open(in_path, "w") as f:
                json.dump(texts, f)
        except Exception as e:
            raise RuntimeError(f"[Module 2] Failed to serialize input texts: {e}") from e
        
        _run_isolated("Module 2 (Phishing)", MODULE2_SRC, _MODULE2_PHISHING_RUNNER, [in_path, out_path])
        
        try:
            with open(out_path) as f:
                result = json.load(f)
            return result
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"[Module 2] Output JSON is invalid: {e}\n"
                f"Output file: {out_path}\n"
                f"This usually means the subprocess crashed after writing partial data."
            ) from e
        except FileNotFoundError as e:
            raise RuntimeError(
                f"[Module 2] Output file not created: {out_path}\n"
                f"Subprocess may have exited before writing results."
            ) from e


# -------- Module 2: bayesian_risk_adjustment(...) -> final_risk_probability --------
_MODULE2_BAYES_RUNNER = r"""
import sys, json
sys.path.insert(0, sys.argv[1])
from bayesian_layer import bayesian_risk_adjustment, risk_category_from_probability
with open(sys.argv[2]) as f:
    payload = json.load(f)
final = bayesian_risk_adjustment(
    anomaly_score=payload["anomaly_score"],
    phishing_probability=payload["phishing_probability"],
    historical_attack_rate=payload["historical_attack_rate"],
    prior_probability=payload["prior_probability"],
)
category = risk_category_from_probability(final)
with open(sys.argv[3], "w") as f:
    json.dump({"final_risk_probability": final, "risk_category": category}, f)
"""


def call_module2_bayesian_risk_adjustment(anomaly_score: float, phishing_probability: float,
                                           historical_attack_rate: float, prior_probability: float) -> dict:
    """Fuse anomaly and phishing scores via Bayesian adjustment."""
    with tempfile.TemporaryDirectory() as tmpdir:
        in_path = os.path.join(tmpdir, "payload.json")
        out_path = os.path.join(tmpdir, "result.json")
        
        try:
            with open(in_path, "w") as f:
                json.dump({
                    "anomaly_score": anomaly_score,
                    "phishing_probability": phishing_probability,
                    "historical_attack_rate": historical_attack_rate,
                    "prior_probability": prior_probability,
                }, f)
        except Exception as e:
            raise RuntimeError(f"[Module 2] Failed to serialize Bayesian input: {e}") from e
        
        _run_isolated("Module 2 (Bayesian)", MODULE2_SRC, _MODULE2_BAYES_RUNNER, [in_path, out_path])
        
        try:
            with open(out_path) as f:
                result = json.load(f)
            return result
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"[Module 2] Output JSON is invalid: {e}\n"
                f"Output file: {out_path}\n"
                f"Expected keys: final_risk_probability, risk_category"
            ) from e
        except FileNotFoundError as e:
            raise RuntimeError(
                f"[Module 2] Output file not created: {out_path}\n"
                f"Subprocess may have exited before writing results."
            ) from e


# -------- Module 3: generate_xai_report(live_event=...) -> important_features, feature_contributions, risk_summary --------
_MODULE3_XAI_RUNNER = r"""
import sys, json
sys.path.insert(0, sys.argv[1])
from xai_engine import generate_xai_report
with open(sys.argv[2]) as f:
    live_event = json.load(f)
result = generate_xai_report(live_event=live_event)
with open(sys.argv[3], "w") as f:
    json.dump(result, f)
"""


def call_module3_generate_xai_report(live_event: dict) -> dict:
    """Generate SHAP explanations for a live event (or empty dict for graceful degradation)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        in_path = os.path.join(tmpdir, "live_event.json")
        out_path = os.path.join(tmpdir, "result.json")
        
        try:
            with open(in_path, "w") as f:
                json.dump(live_event, f)
        except Exception as e:
            raise RuntimeError(f"[Module 3] Failed to serialize live_event: {e}") from e
        
        _run_isolated("Module 3 (XAI)", MODULE3_SRC, _MODULE3_XAI_RUNNER, [in_path, out_path], timeout=180)
        
        try:
            with open(out_path) as f:
                result = json.load(f)
            return result
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"[Module 3] Output JSON is invalid: {e}\n"
                f"Output file: {out_path}\n"
                f"Expected keys: important_features, feature_contributions, risk_summary"
            ) from e
        except FileNotFoundError as e:
            raise RuntimeError(
                f"[Module 3] Output file not created: {out_path}\n"
                f"Subprocess may have exited before writing results."
            ) from e


if __name__ == "__main__":
    logger.info("Testing all four cross-module bridges (requires module1/module2/module3 trained)...")

    net_df = pd.read_csv(
        os.path.abspath(os.path.join(MODULE1_SRC, "..", "data", "synthetic_network_logs.csv")),
        parse_dates=["timestamp"],
    )
    sample = net_df.iloc[300:301].drop(columns=["is_attack"])

    r1 = call_module1_predict_network_anomaly(sample)
    assert "anomaly_score" in r1[0]
    logger.info(f"Module 1 bridge OK: anomaly_score={r1[0]['anomaly_score']:.2f}")

    r2 = call_module2_predict_phishing(["URGENT verify your account now at fake-login.tk"])
    assert "phishing_probability" in r2[0]
    logger.info(f"Module 2 phishing bridge OK: phishing_probability={r2[0]['phishing_probability']:.4f}")

    r3 = call_module2_bayesian_risk_adjustment(r1[0]["anomaly_score"], r2[0]["phishing_probability"], 0.10, 0.10)
    assert "final_risk_probability" in r3
    logger.info(f"Module 2 Bayesian bridge OK: final_risk_probability={r3['final_risk_probability']:.4f}")

    r4 = call_module3_generate_xai_report({
        "feature_vector": r1[0]["feature_vector"],
        "anomaly_score": r1[0]["anomaly_score"],
        "phishing_probability": r2[0]["phishing_probability"],
        "final_risk_probability": r3["final_risk_probability"],
        "risk_category": r3["risk_category"],
    })
    assert "important_features" in r4
    logger.info(f"Module 3 bridge OK: top features={r4['important_features'][:3]}")

    logger.info("module_bridge.py self-test passed — all four bridges functional.")
