/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // 계산·문장은 전부 서버(API)에 있다. 클라이언트로 내리지 않는다.
  env: {
    NEXT_PUBLIC_API_BASE: process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000",
  },
};
export default nextConfig;
