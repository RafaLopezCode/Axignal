import { defineConfig } from "vite";

export default defineConfig({
  root: ".",
  server: { port: 5199, strictPort: true, host: "127.0.0.1" },
  preview: { port: 5199, strictPort: true, host: "127.0.0.1" },
  build: { target: "esnext", sourcemap: false },
});
