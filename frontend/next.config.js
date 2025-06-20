/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  output: 'standalone',
  transpilePackages: [
    // antd & deps
    "@ant-design",
    "@rc-component", 
    "antd",
    "rc-cascader",
    "rc-checkbox",
    "rc-collapse",
    "rc-dialog",
    "rc-drawer",
    "rc-dropdown",
    "rc-field-form",
    "rc-image",
    "rc-input",
    "rc-input-number",
    "rc-mentions",
    "rc-menu",
    "rc-motion",
    "rc-notification",
    "rc-pagination",
    "rc-picker",
    "rc-progress",
    "rc-rate",
    "rc-resize-observer",
    "rc-segmented",
    "rc-select",
    "rc-slider",
    "rc-steps",
    "rc-switch",
    "rc-table",
    "rc-tabs",
    "rc-textarea",
    "rc-tooltip",
    "rc-tree",
    "rc-tree-select",
    "rc-upload",
    "rc-util"
  ],
  experimental: {
    esmExternals: 'loose'
  },
  async rewrites() {
    const apiUrl = process.env.NODE_ENV === 'production' 
      ? 'http://backend:8000/api/:path*'  // Docker环境中使用服务名
      : 'http://localhost:8000/api/:path*'  // 开发环境使用localhost
    
    return [
      {
        source: '/api/:path*',
        destination: apiUrl
      }
    ]
  }
}

module.exports = nextConfig 