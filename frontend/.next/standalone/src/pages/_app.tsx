import type { AppProps } from 'next/app'
import { AntdRegistry } from '@ant-design/nextjs-registry'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import '../styles/globals.css'

export default function App({ Component, pageProps }: AppProps) {
  return (
    <AntdRegistry>
      <ConfigProvider locale={zhCN}>
        <Component {...pageProps} />
      </ConfigProvider>
    </AntdRegistry>
  )
} 