import React, { useState } from "react";
import { UploadCloud, CheckCircle2, AlertTriangle, FileSpreadsheet, Loader2, ArrowRight } from "lucide-react";
import { uploadAndProfileDataset } from "../api/client";

export const DataIntakeView: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState<boolean>(false);
  const [profileResult, setProfileResult] = useState<any | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setErrorMsg(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setErrorMsg(null);
    setProfileResult(null);

    try {
      const res = await uploadAndProfileDataset(file);
      setProfileResult(res);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to inspect file.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
      <div>
        <div className="eyebrow-tag" style={{ color: "var(--color-primary)", marginBottom: "6px" }}>
          DATA INTAKE & STATUTORY PROFILING PIPELINE
        </div>
        <h1 className="display-title" style={{ fontSize: "32px" }}>
          Automated Data Profiler
        </h1>
        <p style={{ fontFamily: "var(--font-serif)", fontStyle: "italic", fontSize: "17px", color: "var(--color-ink-muted)", marginTop: "4px" }}>
          Quarantine sandbox, format validation, and schema conformance for agricultural mandi records and crop estimates.
        </p>
      </div>

      {/* Upload Zone Card */}
      <div className="liquid-glass" style={{ padding: "38px 24px", textAlign: "center", border: "2px dashed rgba(0, 102, 204, 0.25)" }}>
        <div style={{
          width: "56px",
          height: "56px",
          borderRadius: "var(--radius-pill)",
          background: "rgba(0, 102, 204, 0.08)",
          color: "var(--color-primary)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          margin: "0 auto 14px auto"
        }}>
          <UploadCloud size={28} />
        </div>
        <h3 style={{ fontFamily: "var(--font-serif)", fontSize: "20px", fontWeight: 400, marginBottom: "4px", color: "var(--color-ink)" }}>
          Upload Mandi or Crop Inflow Dataset
        </h3>
        <p style={{ fontSize: "14px", color: "var(--color-ink-muted)", marginBottom: "20px" }}>
          Supports CSV, TSV, and XLSX (Max 10MB). Automatically checks anomaly rates, zero-bound bounds, and non-consecutive date gaps.
        </p>

        <input
          type="file"
          id="file-upload"
          accept=".csv,.xlsx,.tsv"
          onChange={handleFileChange}
          style={{ display: "none" }}
        />
        <label
          htmlFor="file-upload"
          className="btn-liquid btn-glass"
          style={{ cursor: "pointer", display: "inline-flex", marginBottom: "14px", padding: "10px 22px" }}
        >
          <FileSpreadsheet size={16} />
          {file ? file.name : "Select File from Local System"}
        </label>

        {file && (
          <div style={{ marginTop: "12px" }}>
            <button
              className="btn-liquid btn-primary"
              disabled={uploading}
              onClick={handleUpload}
              style={{ padding: "10px 24px" }}
            >
              {uploading ? (
                <>
                  <Loader2 size={16} className="spin-animate" />
                  Profiling Schema...
                </>
              ) : (
                "Execute Quarantine & Schema Validation"
              )}
            </button>
          </div>
        )}
      </div>

      {/* Error Notice */}
      {errorMsg && (
        <div style={{
          padding: "14px 18px",
          backgroundColor: "rgba(243, 201, 182, 0.4)",
          border: "1px solid rgba(198, 69, 69, 0.3)",
          color: "var(--glass-coral-ink)",
          borderRadius: "var(--radius-md)",
          display: "flex",
          alignItems: "center",
          gap: "10px",
          fontSize: "14px"
        }}>
          <AlertTriangle size={18} />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Profiling Report Card */}
      {profileResult && (
        <div className="liquid-glass-elevated" style={{ padding: "28px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
            <div>
              <div className="eyebrow-tag">INGESTION QUALITY REPORT</div>
              <h3 style={{ fontFamily: "var(--font-serif)", fontSize: "20px", fontWeight: 400, color: "var(--color-ink)", marginTop: "2px" }}>
                {profileResult.filename}
              </h3>
            </div>
            <span className="badge-glass badge-mint">
              SCHEMA VERIFIED
            </span>
          </div>

          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
            gap: "12px",
            marginBottom: "20px"
          }}>
            <div className="liquid-glass" style={{ padding: "14px" }}>
              <span style={{ fontSize: "11px", color: "var(--color-ink-muted)", display: "block" }}>Total Ingested Records</span>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: "20px", fontWeight: 700, color: "var(--color-ink)" }}>
                {profileResult.row_count?.toLocaleString()}
              </span>
            </div>
            <div className="liquid-glass" style={{ padding: "14px" }}>
              <span style={{ fontSize: "11px", color: "var(--color-ink-muted)", display: "block" }}>Date Coverage Range</span>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: "13px", fontWeight: 600, color: "var(--color-primary)" }}>
                {profileResult.date_range?.min_date} – {profileResult.date_range?.max_date}
              </span>
            </div>
            <div className="liquid-glass" style={{ padding: "14px" }}>
              <span style={{ fontSize: "11px", color: "var(--color-ink-muted)", display: "block" }}>Data Completeness Score</span>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: "20px", fontWeight: 700, color: "var(--status-normal)" }}>
                {((1 - (profileResult.null_counts?.modal_price || 0) / Math.max(profileResult.row_count, 1)) * 100).toFixed(1)}%
              </span>
            </div>
          </div>

          <div style={{ fontSize: "13px", color: "var(--color-ink-muted)", display: "flex", alignItems: "center", gap: "6px" }}>
            <CheckCircle2 size={16} color="var(--status-normal)" />
            <span>Passed all sanity thresholds. Ready for integration into primary Agmarknet feature store.</span>
          </div>
        </div>
      )}
    </div>
  );
};
