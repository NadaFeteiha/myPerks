// TODO: Delete when user profile and benefits API are ready

export type BalanceItem = {
  iconType: "pto" | "sick";
  id: string;
  label: string;
  progress: number;
  progressColor: "blue" | "teal";
  sub: string;
  unit: string;
  value: number | string;
};

export type ProgressColor = BalanceItem["progressColor"];

export const MOCK_USER_PROFILE = {
  benefitsYearReset: "Jan 1",
  joinedDate: "Jan 2023",
};

export const MOCK_BALANCES: BalanceItem[] = [
  {
    iconType: "pto",
    id: "pto",
    label: "PTO",
    progress: 67,
    progressColor: "teal",
    sub: "18 total · 6 used this year",
    unit: "days",
    value: 12,
  },
  {
    iconType: "sick",
    id: "sick",
    label: "Sick Days",
    progress: 80,
    progressColor: "blue",
    sub: "10 total · 2 used this year",
    unit: "days",
    value: 8,
  },
];
