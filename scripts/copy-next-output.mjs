import { cpSync, existsSync, rmSync } from "node:fs";
import { resolve } from "node:path";

const src = resolve("frontend/.next");
if (!existsSync(src)) {
  throw new Error(`Next.js output not found at ${src}`);
}

// Vercel ищет .next в корне проекта или в Root Directory (часто ошибочно backend/).
for (const dest of [resolve(".next"), resolve("backend/.next")]) {
  rmSync(dest, { recursive: true, force: true });
  cpSync(src, dest, { recursive: true });
  console.log(`Copied Next.js output to ${dest}`);
}
