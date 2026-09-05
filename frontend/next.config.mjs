/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
};

// standalone нужен только для Docker. На Vercel Next 16.3 + adapter
// ломает сборку: ENOENT .next/next-server.js.nft.json
if (!process.env.VERCEL) {
  nextConfig.output = "standalone";
}

export default nextConfig;

