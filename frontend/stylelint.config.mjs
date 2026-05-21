const stylelintConfig = {
  extends: ["stylelint-config-standard"],
  rules: {
    "at-rule-no-unknown": [
      true,
      {
        ignoreAtRules: [
          "tailwind",
          "apply",
          "variants",
          "responsive",
          "screen",
          "layer",
          "theme",
          "utility",
          "source",
          "plugin",
          "custom-variant",
        ],
      },
    ],
    "import-notation": "string", // allow bare string imports, required for Tailwind v4
  },
};

export default stylelintConfig;
