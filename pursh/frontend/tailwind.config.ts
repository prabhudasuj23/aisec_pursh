import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        pursh: {
          teal: "#00A79D",
          "teal-deep": "#008D84",
          aqua: "#62C9C2",
          mint: "#DDF5F2",
          silver: "#EEF2F2",
          graphite: "#31474B",
          charcoal: "#22363A",
          slate: "#4C5B5F",
          ink: "#12262A",
          white: "#FFFFFF",
          muted: "#6B7A7E",
          green: "#00A79D",
          "green-light": "#62C9C2",
          cream: "#EEF2F2",
          "cream-dark": "#DDF5F2",
          brown: "#12262A",
          "brown-mid": "#31474B",
          amber: "#00A79D",
          sand: "#DDF5F2",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
