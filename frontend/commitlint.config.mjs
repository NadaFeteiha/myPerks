export default {
  extends: ["@commitlint/config-conventional"],
  plugins: ["commitlint-plugin-tense"],
  rules: {
    "subject-case": [2, "always", "sentence-case"],
    "tense/subject": [2, "always", "imperative-present"],
  },
};
