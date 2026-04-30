import createNextIntlPlugin from 'next-intl/plugin';

const withNextIntl = createNextIntlPlugin('./src/i18n/request.ts');

const repoBasePath = process.env.NEXT_PUBLIC_BASE_PATH ?? '/Dawri-AI';

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  basePath: repoBasePath,
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
  reactStrictMode: true,
};

export default withNextIntl(nextConfig);
