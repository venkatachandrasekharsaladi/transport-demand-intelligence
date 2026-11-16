/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        navy: "#10233f",
        ink: "#17243a",
        mist: "#f6f8fb",
        line: "#e5eaf1",
        accent: "#2563eb",
      },
      boxShadow: {
        panel: "0 8px 26px rgba(16, 35, 63, 0.06)",
      },
    },
  },
  plugins: [],
};
