/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        base: "#1e1e2e",
        mantle: "#181825",
        crust: "#11111b",
        surface0: "#313244",
        surface1: "#45475a",
        surface2: "#585b70",
        overlay0: "#6c7086",
        overlay1: "#7f849c",
        text: "#cdd6f4",
        subtext0: "#a6adc8",
        subtext1: "#bac2de",
        blue: "#89b4fa",
        lavender: "#b4befe",
        sapphire: "#74c7ec",
        green: "#a6e3a1",
        peach: "#fab387",
        red: "#f38ba8",
        mauve: "#cba6f7",
        yellow: "#f9e2af",
      },
    },
  },
  plugins: [],
};
