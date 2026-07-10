import type { Config } from "tailwindcss";

/**
 * 悟典 - 中国风配色 Tailwind 配置
 * 墨色主调，朱砂点缀，米黄背景，竹青辅助
 */
const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // 墨色系（主调）
        ink: {
          50: "#f5f5f4",
          100: "#e7e5e4",
          200: "#d6d3d1",
          300: "#a8a29e",
          400: "#78716c",
          500: "#57534e",
          600: "#44403c",
          700: "#292524",
          800: "#1c1917",
          900: "#0c0a09",
          DEFAULT: "#1c1917",
        },
        // 朱砂系（点缀）
        cinnabar: {
          50: "#fef2f2",
          100: "#fee2e2",
          200: "#fecaca",
          300: "#fca5a5",
          400: "#f87171",
          500: "#dc2626",
          600: "#b91c1c",
          700: "#991b1b",
          800: "#7f1d1d",
          900: "#5b1313",
          DEFAULT: "#b91c1c",
        },
        // 米黄/宣纸系（背景）
        rice: {
          50: "#fdfbf7",
          100: "#faf6ed",
          200: "#f5edd9",
          300: "#efe3c2",
          400: "#e6d4a3",
          500: "#dcc080",
          600: "#c9a85e",
          700: "#a8854a",
          800: "#87663c",
          900: "#6b4f30",
          DEFAULT: "#faf6ed",
        },
        // 宣纸色系（更温润的背景）
        paper: {
          50: "#fdfcf8",
          100: "#f8f5ee",
          200: "#f3efe4",
          300: "#ebe5d4",
          400: "#ddd4bd",
          500: "#c9bda0",
          DEFAULT: "#f8f5ee",
        },
        // 竹青系（辅助点缀）
        bamboo: {
          50: "#f0f7f0",
          100: "#dbe9db",
          200: "#bdd6bd",
          300: "#9cc09c",
          400: "#7ba87b",
          500: "#5b8c5a",
          600: "#4a7349",
          700: "#3a5c39",
          800: "#2d452c",
          900: "#1f2f1f",
          DEFAULT: "#5b8c5a",
        },
        // 青铜系（辅助）
        bronze: {
          400: "#a8a06b",
          500: "#8a8050",
          600: "#6e663f",
          DEFAULT: "#8a8050",
        },
      },
      fontFamily: {
        sans: ['"Noto Sans SC"', '"PingFang SC"', '"Microsoft YaHei"', "system-ui", "sans-serif"],
        serif: ['"Noto Serif SC"', '"Songti SC"', '"SimSun"', '"STSong"', "serif"],
        kai: ['"Kaiti SC"', '"STKaiti"', '"KaiTi"', '"楷体"', "serif"],
      },
      fontSize: {
        "hero": ["3.5rem", { lineHeight: "1.1", letterSpacing: "0.15em" }],
        "hero-sm": ["2.5rem", { lineHeight: "1.15", letterSpacing: "0.12em" }],
      },
      boxShadow: {
        scroll: "0 2px 8px rgba(28, 25, 23, 0.08)",
        "scroll-soft": "0 1px 4px rgba(28, 25, 23, 0.06)",
        popup: "0 8px 30px rgba(28, 25, 23, 0.15)",
        "paper": "0 1px 3px rgba(139, 115, 63, 0.08)",
      },
      animation: {
        "fade-in": "fadeIn 0.3s ease-in-out",
        "slide-up": "slideUp 0.3s ease-out",
        "slow-fade": "fadeIn 0.8s ease-in-out",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { transform: "translateY(10px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
