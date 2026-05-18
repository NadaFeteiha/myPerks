const config = {
  "**/*.{css,scss}": ["stylelint --fix", "prettier --write"],
  "**/*.{js,cjs,mjs,jsx,ts,cts,mts,tsx}": ["eslint --fix", "prettier --write"],
  "**/*.{json,md,yaml,yml}": ["prettier --write"],
};

export default config;
