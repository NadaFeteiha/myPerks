import markdown from "@eslint/markdown";
import vitest from "@vitest/eslint-plugin";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";
import prettier from "eslint-config-prettier";
import boundaries from "eslint-plugin-boundaries";
import checkFile from "eslint-plugin-check-file";
import githubAction from "eslint-plugin-github-action";
import importPlugin from "eslint-plugin-import";
import perfectionist from "eslint-plugin-perfectionist";
import security from "eslint-plugin-security";
import yml from "eslint-plugin-yml";
import { defineConfig, globalIgnores } from "eslint/config";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  ...githubAction.configs.recommended,
  ...yml.configs.recommended,
  {
    ...perfectionist.configs["recommended-natural"],
    files: ["**/*.{js,cjs,mjs,jsx,ts,cts,mts,tsx}"],
  },
  security.configs.recommended,
  {
    extends: ["markdown/recommended"],
    files: ["**/*.md"],
    plugins: { markdown },
  },
  {
    files: [
      "**/*.{test,spec}.{js,jsx,ts,tsx}",
      "**/__tests__/**/*.{js,jsx,ts,tsx}",
    ],
    ...vitest.configs.recommended,
  },
  {
    plugins: { import: importPlugin },
    rules: {
      "import/no-duplicates": "error",
    },
  },
  {
    files: ["**/*.{ts,cts,mts,tsx}"],
    rules: {
      "@typescript-eslint/no-unused-vars": [
        "error",
        {
          argsIgnorePattern: "^_",
          caughtErrorsIgnorePattern: "^_",
          destructuredArrayIgnorePattern: "^_",
          ignoreRestSiblings: true,
          varsIgnorePattern: "^_",
        },
      ],
      "no-unused-vars": "off",
    },
  },
  {
    plugins: { "check-file": checkFile },
    rules: {
      "check-file/filename-naming-convention": [
        "error",
        { "**/*.{js,jsx,mjs,ts,tsx}": "KEBAB_CASE" },
        { ignoreMiddleExtensions: true },
      ],
      "check-file/folder-naming-convention": [
        "error",
        { "src/**/!(__tests__)": "KEBAB_CASE" },
      ],
    },
  },
  /*
   * Unidirectional architecture:
   * app → features → shared (one direction only)
   * features cannot import from other features
   */
  {
    plugins: { boundaries },
    rules: {
      ...boundaries.configs.recommended.rules,
      "boundaries/dependencies": [
        "error",
        {
          default: "disallow",
          rules: [
            {
              allow: {
                to: [
                  { type: "app" },
                  { type: "feature" },
                  { type: "shared" },
                  { type: "test" },
                ],
              },
              from: { type: "app" },
            },
            {
              allow: {
                to: [
                  {
                    captured: {
                      elementName: "{{ from.captured.elementName }}",
                    },
                    type: "feature",
                  },
                  { type: "shared" },
                  { type: "test" },
                ],
              },
              from: { type: "feature" },
              message:
                "Features are isolated — import from the same feature or shared only.",
            },
            {
              allow: { to: [{ type: "shared" }] },
              from: { type: "shared" },
            },
          ],
        },
      ],
      "boundaries/element-types": "off",
      "boundaries/entry-point": "off",
    },
    settings: {
      ...boundaries.configs.recommended.settings,
      "boundaries/elements": [
        { mode: "file", pattern: "src/app/**", type: "app" },
        {
          capture: ["elementName"],
          pattern: "src/features/*",
          type: "feature",
        },
        { pattern: "src/test/**", type: "test" },
        {
          capture: ["elementName"],
          pattern: "src/!(app|features)",
          type: "shared",
        },
      ],
    },
  },
  prettier,
  globalIgnores([".next/**", "out/**", "build/**", "next-env.d.ts"]),
]);

export default eslintConfig;
