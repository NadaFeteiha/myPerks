"use client";

import React, { useState } from "react";
import { UploadCloud } from "lucide-react";
import { useUploadThing } from "@/lib/uploadthing";

type UploadSectionProps = {
    onUploadComplete: () => void;
}

export function UploadSection({ onUploadComplete }: UploadSectionProps) {
    const [progress, setProgress] = useState(0);
    const [error, setError] = useState<string | null>(null);
    const [isUploading, setIsUploading] = useState(false);

    const { startUpload } = useUploadThing("pdfUploader", {
        onUploadProgress: (p) => setProgress(p),
        onClientUploadComplete: () => {
            setIsUploading(false);
            setProgress(0);
            setError(null);
            onUploadComplete();
        },
        onUploadError: (err) => {
            setIsUploading(false);
            setProgress(0);
            setError(err.message);
        }
    });

    const handleChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;
        setIsUploading(true);
        setError(null);
        await startUpload([file]);
    };

    return (
        <div className="rounded-xl border border-border bg-white p-4 dark: bg-card">
            <label
                className="flex cursor-pointer flex-col items-center rounded-lg border border-dashed border-border bg-background px-4 py-6 text-center transition-colors hover:bg-brand-purple-50 dark:hover:bg-brand-purple-900/30"
                htmlFor="pdf-upload-input"
            >
                <UploadCloud className="mb-2 h-6 w-6 text-muted-foreground" />
                <p className="text-[13px] font-medium text-foreground">
                    {isUploading ? "Uploading..." : "Click to upload a PDF"}
                </p>
                <p className="mt-0.5 text-[11px] text-muted-foreground">
                    PDF only · max 16MB
                </p>
                <input
                    accept=".pdf"
                    className="hidden"
                    disabled={isUploading}
                    id="pdf-upload-input"
                    onChange={handleChange}
                    type="file"
                />
            </label>

            {isUploading && (
                <div className="mt-3 h-1 overflow-hidden rounded-full bg-surface-3">
                    <div
                        className='h-full rounded-full bg-brand-teal-400 transition-all'
                        style={{ width: `${progress}%` }}
                    />
                </div>
            )}

            {error && (
                <p className="mt-3 text-[12px] text-red-500">{error}</p>
            )}
        </div>
    );
}
