import path from "node:path";
import { fileURLToPath } from "node:url";

const frontendDir = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.join(frontendDir, "..");

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // В монорепо зависимости лежат в корневом node_modules.
  // Без этого Vercel зависает или падает на "Collecting build traces".
  outputFileTracingRoot: repoRoot,
};

if (!process.env.VERCEL) {
  nextConfig.output = "standalone";
}

export default nextConfig;
