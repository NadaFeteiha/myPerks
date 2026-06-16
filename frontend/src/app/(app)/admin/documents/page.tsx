"use client";

import { useCallback, useEffect, useState } from "react";

import { DocumentListSection } from "@/components/upload/document-list-section";
import { UploadSection } from "@/components/upload/upload-section";
import { useApi } from "@/lib/api.client";

type Document = {
  department: string;
  extraction_status: null | string;
  filename: string;
  id: number;
  uploaded_at: string;
};

export default function AdminDocumentsPage() {
  const api = useApi();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<null | string>(null);

  const fetchDocuments = useCallback(async () => {
    try {
      setError(null);
      const data = await api.getDocuments();
      setDocuments(data.documents);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load documents.",
      );
    } finally {
      setLoading(false);
    }
  }, [api]);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        setError(null);
        const data = await api.getDocuments();
        if (!cancelled) setDocuments(data.documents);
      } catch (err) {
        if (!cancelled)
          setError(
            err instanceof Error ? err.message : "Failed to load documents.",
          );
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, [api]);

  return (
    <div className="mx-auto max-w-2xl space-y-8 p-6">
      <div>
        <h1 className="text-lg font-semibold text-foreground">
          Document Management
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Upload HR documents and assign them to a department for RAG retrieval.
        </p>
      </div>

      <section>
        <h2 className="mb-3 text-[13px] font-semibold text-foreground">
          Upload Document
        </h2>
        <UploadSection onUploadComplete={() => void fetchDocuments()} />
      </section>

      <section>
        <h2 className="mb-3 text-[13px] font-semibold text-foreground">
          Uploaded Documents
        </h2>
        {loading ? (
          <p className="text-[12px] text-muted-foreground">Loading...</p>
        ) : error ? (
          <p className="text-[12px] text-red-500">{error}</p>
        ) : (
          <DocumentListSection documents={documents} />
        )}
      </section>
    </div>
  );
}
