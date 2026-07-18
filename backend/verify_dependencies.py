import json
import importlib.metadata
import sys

def verify_dependencies():
    report = {
        "python_version": sys.version,
        "imports_successful": True,
        "packages": {},
        "conflicts": [],
        "duplicate_langchain": []
    }

    # 1. Import every package to ensure they load
    try:
        import fastapi
        import uvicorn
        import pydantic
        import sqlalchemy
        import celery
        import redis
        import chromadb
        import pdfplumber
        import ragas
        import deepeval
        import langchain
        import langchain_community
        import langchain_core
        import xgboost
        import optuna
        import tenacity
        import diskcache
    except ImportError as e:
        report["imports_successful"] = False
        report["conflicts"].append(f"Import Error: {e}")

    # 2. Verify versions
    required_versions = {
        "fastapi": "0.109.2",
        "ragas": "0.1.1",
        "deepeval": "0.20.14",
        "langchain": "0.1.13",
        "langchain-community": "0.0.29",
        "chromadb": "0.4.24",
        "xgboost": "2.0.3"
    }

    for pkg, expected in required_versions.items():
        try:
            actual = importlib.metadata.version(pkg)
            report["packages"][pkg] = {"expected": expected, "actual": actual, "match": actual == expected}
            if actual != expected:
                report["conflicts"].append(f"Version mismatch for {pkg}. Expected {expected}, got {actual}.")
        except importlib.metadata.PackageNotFoundError:
            report["packages"][pkg] = {"expected": expected, "actual": "NOT_FOUND", "match": False}
            report["conflicts"].append(f"Package {pkg} is missing.")

    # 3. Detect duplicate/conflicting LangChain packages
    try:
        lc_core_ver = importlib.metadata.version("langchain-core")
        report["packages"]["langchain-core"] = {"actual": lc_core_ver}
        # langchain 0.1.13 requires langchain-core < 0.2.0
        if lc_core_ver.startswith("0.2") or lc_core_ver.startswith("0.3"):
            report["conflicts"].append(f"langchain-core is {lc_core_ver}, which conflicts with langchain==0.1.13")
    except importlib.metadata.PackageNotFoundError:
        pass

    try:
        importlib.metadata.version("langchain-ollama")
        report["duplicate_langchain"].append("langchain-ollama (SHOULD BE REMOVED)")
    except importlib.metadata.PackageNotFoundError:
        pass

    try:
        importlib.metadata.version("google-generativeai")
        report["conflicts"].append("google-generativeai is still installed")
    except importlib.metadata.PackageNotFoundError:
        pass

    with open("dependency_health_report.json", "w") as f:
        json.dump(report, f, indent=4)
        
    print(json.dumps(report, indent=4))
    
    if report["conflicts"] or report["duplicate_langchain"]:
        sys.exit(1)
    
if __name__ == "__main__":
    verify_dependencies()
