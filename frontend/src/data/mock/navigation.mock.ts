// TODO: Delete when documents API is ready

export type PolicyFile = {
  id: string;
  name: string;
  updatedAt: string;
};

export const MOCK_POLICY_FILES: PolicyFile[] = [
  { id: "1", name: "PTO Policy 2024", updatedAt: "Updated May 14" },
  { id: "2", name: "Parental Leave", updatedAt: "Updated May 15" },
  { id: "3", name: "Wellness Reimbursement", updatedAt: "Updated May 16" },
];
