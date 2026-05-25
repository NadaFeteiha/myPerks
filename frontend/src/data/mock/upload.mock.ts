// TODO: Delete when GET /upload/documents API is ready

export type MockDocument = {
  id: number;
  filename: string;
  uploaded_at: string;
};

export const MOCK_DOCUMENTS: MockDocument[] = [
  { id: 1, filename: "benefits-guide-2024.pdf", uploaded_at: "May 14, 2026" },
  { id: 2, filename: "parental-leave-policy.pdf", uploaded_at: "May 15, 2026" },
  { id: 3, filename: "wellness-reimbursement.pdf", uploaded_at: "May 16, 2026" },
];
