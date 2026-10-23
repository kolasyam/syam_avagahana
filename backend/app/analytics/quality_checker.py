"""
Data Quality Profiler and Ingestion Pipeline
Validates datasets, profiles schemas, identifies anomalies, and generates an issue ledger.
"""

from typing import Dict, Any, List
import pandas as pd
import io

def profile_dataset(file_content: bytes, filename: str) -> Dict[str, Any]:
    """Profiles an uploaded CSV or XLSX dataset."""
    try:
        if filename.endswith(".csv") or filename.endswith(".tsv"):
            sep = "\t" if filename.endswith(".tsv") else ","
            df = pd.read_csv(io.BytesIO(file_content), sep=sep)
        elif filename.endswith(".xlsx") or filename.endswith(".xls"):
            df = pd.read_excel(io.BytesIO(file_content))
        else:
            return {
                "valid": False,
                "error": f"Unsupported format: {filename}. Supported formats: CSV, TSV, XLSX."
            }
    except Exception as e:
        return {
            "valid": False,
            "error": f"Failed to parse file: {str(e)}"
        }

    issues: List[Dict[str, Any]] = []
    total_rows = len(df)
    total_cols = len(df.columns)
    
    # 1. Null check per column
    col_profiles = {}
    date_col = None
    price_col = None
    arrivals_col = None
    
    for col in df.columns:
        col_lower = str(col).lower()
        null_count = int(df[col].isnull().sum())
        null_pct = round((null_count / total_rows) * 100, 2) if total_rows > 0 else 0
        
        col_type = str(df[col].dtype)
        col_profiles[str(col)] = {
            "dtype": col_type,
            "null_count": null_count,
            "null_pct": null_pct,
            "unique_values": int(df[col].nunique())
        }
        
        if null_pct > 20.0:
            issues.append({
                "severity": "WARNING",
                "column": str(col),
                "issue_type": "HIGH_NULL_RATE",
                "message": f"Column '{col}' has {null_pct}% missing values."
            })
            
        # Detect target date column
        if any(k in col_lower for k in ["date", "time", "day", "dt"]) and date_col is None:
            date_col = str(col)
            
        # Detect modal or price column
        if any(k in col_lower for k in ["modal", "price", "rate", "cost"]) and price_col is None:
            price_col = str(col)
            
        # Detect arrival column
        if any(k in col_lower for k in ["arrival", "quantity", "volume", "qty"]) and arrivals_col is None:
            arrivals_col = str(col)

    # 2. Check for missing dates if date column detected
    if date_col:
        try:
            parsed_dates = pd.to_datetime(df[date_col], errors="coerce").dropna()
            if len(parsed_dates) > 1:
                parsed_dates = parsed_dates.sort_values()
                date_diffs = parsed_dates.diff().dt.days
                gaps = date_diffs[date_diffs > 1]
                if len(gaps) > 0:
                    issues.append({
                        "severity": "INFO",
                        "column": date_col,
                        "issue_type": "TIME_GAPS",
                        "message": f"Detected {len(gaps)} non-consecutive date gaps (mandi closures or weekend holidays)."
                    })
        except Exception:
            pass
            
    # 3. Check for price negative or zero values
    if price_col and pd.api.types.is_numeric_dtype(df[price_col]):
        invalid_prices = int((df[price_col] <= 0).sum())
        if invalid_prices > 0:
            issues.append({
                "severity": "CRITICAL",
                "column": price_col,
                "issue_type": "NON_POSITIVE_PRICE",
                "message": f"Found {invalid_prices} rows with price <= 0."
            })

    quality_score = max(round(1.0 - (len(issues) * 0.08), 2), 0.50)

    return {
        "valid": True,
        "filename": filename,
        "total_rows": total_rows,
        "total_columns": total_cols,
        "detected_date_column": date_col,
        "detected_price_column": price_col,
        "detected_arrivals_column": arrivals_col,
        "column_profiles": col_profiles,
        "quality_score": quality_score,
        "issue_ledger": issues,
        "preview_rows": df.head(5).to_dict(orient="records")
    }
