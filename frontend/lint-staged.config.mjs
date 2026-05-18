export default {
  "**/*.{js,cjs,mjs,jsx,ts,cts,mts,tsx}": [
    "eslint --fix",
    "prettier --write",
  ],
  "**/*.{css,scss}": ["stylelint --fix", "prettier --write"],
  "**/*.{json,md,yaml,yml}": ["prettier --write"],
};
