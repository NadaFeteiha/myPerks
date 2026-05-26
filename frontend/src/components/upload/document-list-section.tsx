"use client"

import { DocumentRow } from "./document-row";

type Document = {
    id: number;
    filename: string;
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
                    key={doc.id}
                    filename={doc.filename}
                    uploaded_at={doc.uploaded_at}
                />
            ))}
        </div>
    );
}
