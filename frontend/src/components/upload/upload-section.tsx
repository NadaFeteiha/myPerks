"use client";

import { useAuth } from "@clerk/nextjs";
import { UploadCloud } from "lucide-react";
import React, { useEffect, useState } from "react";

import { useUploadThing } from "@/lib/uploadthing";

const DEPARTMENTS = [
  "all",
  "engineering",
  "finance",
  "hr",
  "marketing",
  "operations",
  "other",
  "sales",
] as const;

type Department = (typeof DEPARTMENTS)[number];

type UploadSectionProps = {
  onUploadComplete: () => void;
};

type UploadState = "idle" | "processing" | "uploading";

export function UploadSection({ onUploadComplete }: UploadSectionProps) {
  const { getToken } = useAuth();
  const [uploadState, setUploadState] = useState<UploadState>("idle");
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<null | string>(null);
  const [department, setDepartment] = useState<Department>("engineering");

  const isBusy = uploadState !== "idle";

  useEffect(() => {
    if (!isBusy) return;
    const handle = (e: BeforeUnloadEvent) => {
      e.preventDefault();
    };
    window.addEventListener("beforeunload", handle);
    return () => window.removeEventListener("beforeunload", handle);
  }, [isBusy]);

  const { startUpload } = useUploadThing("pdfUploader", {
    onClientUploadComplete: (files) => {
      const f = files[0];
      if (!f) {
        setError("Upload returned no file data.");
        setUploadState("idle");
        setProgress(0);
        return;
      }

      setUploadState("processing");
      setProgress(0);

      async function ingest() {
        try {
          const token = await getToken();
          const res = await fetch("/api/backend/upload/callback", {
            body: JSON.stringify({
              department,
              files: [
                {
                  key: f.key,
                  name: f.name,
                  size: f.size,
                  url: f.ufsUrl ?? f.url,
                },
              ],
            }),
            headers: {
              Authorization: `Bearer ${token}`,
              "Content-Type": "application/json",
            },
            method: "POST",
          });

          if (!res.ok) {
            const body = await res.json().catch(() => ({}));
            throw new Error(
              (body as { detail?: string }).detail ??
                "Failed to process document.",
            );
          }

          onUploadComplete();
        } catch (err) {
          setError(err instanceof Error ? err.message : "Upload failed.");
        } finally {
          setUploadState("idle");
        }
      }

      void ingest();
    },
    onUploadError: (err) => {
      setError(err.message);
      setUploadState("idle");
      setProgress(0);
    },
    onUploadProgress: (p) => setProgress(p),
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadState("uploading");
    setError(null);
    void startUpload([file]);
  };

  return (
    <div className="rounded-xl border border-border bg-white p-4 dark:bg-card">
      {/* Department selector */}
      <div className="mb-3">
        <label
          className="mb-1 block text-[12px] font-medium text-muted-foreground"
          htmlFor="department-select"
        >
          Department
        </label>
        <select
          className="w-full rounded-lg border border-border bg-background px-3 py-1.5 text-[13px] text-foreground focus:outline-none focus:ring-2 focus:ring-brand-purple-400 disabled:opacity-50"
          disabled={isBusy}
          id="department-select"
          onChange={(e) => setDepartment(e.target.value as Department)}
          value={department}
        >
          {DEPARTMENTS.map((d) => (
            <option key={d} value={d}>
              {departmentLabel(d)}
            </option>
          ))}
        </select>
      </div>

      {/* Drop zone */}
      <label
        className="flex cursor-pointer flex-col items-center rounded-lg border border-dashed border-border bg-background px-4 py-6 text-center transition-colors hover:bg-brand-purple-50 dark:hover:bg-brand-purple-900/30"
        htmlFor="pdf-upload-input"
      >
        <UploadCloud className="mb-2 h-6 w-6 text-muted-foreground" />
        <p className="text-[13px] font-medium text-foreground">
          {stateLabel(uploadState)}
        </p>
        <p className="mt-0.5 text-[11px] text-muted-foreground">
          PDF only · max 16 MB
        </p>
        <input
          accept=".pdf"
          className="hidden"
          disabled={isBusy}
          id="pdf-upload-input"
          onChange={handleChange}
          type="file"
        />
      </label>

      {uploadState === "uploading" && (
        <div className="mt-3 h-1 overflow-hidden rounded-full bg-surface-3">
          <div
            className="h-full rounded-full bg-brand-teal-400 transition-all"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}

      {error && <p className="mt-3 text-[12px] text-red-500">{error}</p>}
    </div>
  );
}

// "all" is the company-wide tier (T39); the rest capitalise from the value.
function departmentLabel(d: Department): string {
  if (d === "all") return "All departments";
  return d.charAt(0).toUpperCase() + d.slice(1);
}

function stateLabel(state: UploadState): string {
  if (state === "uploading") return "Uploading...";
  if (state === "processing") return "Processing...";
  return "Click to upload a PDF";
}
