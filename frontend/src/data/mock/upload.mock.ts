// TODO: Delete when GET /upload/documents API is ready

export type MockDocument = {
  filename: string;
  id: number;
  uploaded_at: string;
};

export const MOCK_DOCUMENTS: MockDocument[] = [
  { filename: "benefits-guide-2024.pdf", id: 1, uploaded_at: "May 14, 2026" },
  { filename: "parental-leave-policy.pdf", id: 2, uploaded_at: "May 15, 2026" },
  {
    filename: "wellness-reimbursement.pdf",
    id: 3,
    uploaded_at: "May 16, 2026",
  },
];
