// ESLint flat config for the Interestingifier frontend.
// Lints the browser code in static/ and the Node test files in tests/.

import js from "@eslint/js";
import globals from "globals";

export default [
  js.configs.recommended,
  {
    files: ["static/**/*.js"],
    languageOptions: {
      globals: globals.browser,
    },
  },
  {
    files: ["tests/**/*.js"],
    languageOptions: {
      globals: globals.node,
    },
  },
];