"use client";

import React, { useCallback, useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";

import { DocumentListSection } from "@/components/upload/document-list-section";
import { UploadSection } from "@/components/upload/upload-section";

type Document = {
    id: number;
    filename: string;
    uploaded_at: string;
};

export default function UploadPage() {
    const { getToken } = useAuth();
    const [documents, setDocuments] = useState<Document[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchDocuments = useCallback(async () => {
        try {
            const token = await getToken();
            const res = await fetch("/api/backend/upload/documents", {
                headers: { Authorization: `Bearer ${token}` },
            });
            if (!res.ok) throw new Error("Failed to fetch documents");
            const data = await res.json();
            setDocuments(data.documents);
        } catch (err) {
            setError("Could not load documents.");
        } finally {
            setIsLoading(false);
        }
    }, [getToken]);

    useEffect(() => {
        void fetchDocuments();
    }, [fetchDocuments]);

    return (
        <div className="flex-1 overflow-y-auto p-6">
            <p className="mb-3 text-[10px] font-semibold uppercase tracking-[0.07em] text-muted-foreground">
                Upload documents
            </p>
            <UploadSection onUploadComplete={fetchDocuments} />
            <p className="mb-3 mt-5 text-[10px] font-semibold uppercase tracking-[0.07em] text-muted-foreground">
                Uploaded documents
            </p>
            {isLoading && (
                <p className="text=[12px]  text-muted-foreground">Loading...</p>
            )}
            {error && (
                <p className="text-[12px] text-red-500">{error}</p>
            )}
            {!isLoading && !error && (
                <DocumentListSection documents={documents} />
            )}
        </div>
    );
}
