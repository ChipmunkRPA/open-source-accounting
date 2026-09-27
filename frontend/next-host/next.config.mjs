const backend = process.env.BACKEND_ORIGIN || 'http://127.0.0.1:8000';
export default {
  output: 'standalone',
  webpack(config) {
    // The shared UI uses browser-compatible .js import specifiers in TypeScript.
    config.resolve.extensionAlias = { ...(config.resolve.extensionAlias || {}), '.js': ['.ts', '.tsx', '.js'] };
    return config;
  },
  async rewrites() { return [{source: '/api/:path*', destination: `${backend}/api/:path*`}]; }
};
