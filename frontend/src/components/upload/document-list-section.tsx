"use client";

import { DocumentRow } from "./document-row";

type Document = {
  department?: string; // make optional
  filename: string;
  id: number;
  uploaded_at: string;
};

type DocumentListSectionProps = {
  documents: Document[];
};

export function DocumentListSection({ documents }: DocumentListSectionProps) {
  if (documents.length === 0) {
    return (
      <p className="text-[12px] text-muted-foreground">
        No documents uploaded yet.
      </p>
    );
  }

  // Group by department, preserving insertion order of first appearance.
  const grouped = documents.reduce<Record<string, Document[]>>((acc, doc) => {
    const key = doc.department ?? "other";
    (acc[key] ??= []).push(doc);
    return acc;
  }, {});

  const sortedDepts = Object.keys(grouped).sort();

  return (
    <div className="flex flex-col gap-6">
      {sortedDepts.map((dept) => (
        <div key={dept}>
          <h3 className="mb-2 text-[12px] font-semibold uppercase tracking-wide text-muted-foreground">
            {dept}
          </h3>
          <div className="flex flex-col gap-2.5">
            {grouped[dept]!.map((doc) => (
              <DocumentRow
                department={doc.department}
                filename={doc.filename}
                key={doc.id}
                uploaded_at={doc.uploaded_at}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
