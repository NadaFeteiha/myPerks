"use client"

import { DocumentRow } from "./document-row";

type Document = {
    filename: string;
    id: number;
    uploaded_at: string;
}

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

    return (
        <div className="flex flex-col gap-2.5">
            {documents.map((doc) => (
                <DocumentRow
                    filename={doc.filename}
                    key={doc.id}
                    uploaded_at={doc.uploaded_at}
                />
            ))}
        </div>
    );
}
