import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'cdn-thumbnails.huggingface.co',
        port: '',
        pathname: '/social-thumbnails/papers/**',
      },
    ],
  },
};

export default nextConfig;