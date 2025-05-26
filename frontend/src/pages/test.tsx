import React from 'react'
import { Button, Card, Typography } from 'antd'

const { Title, Text } = Typography

export default function TestPage() {
  return (
    <div style={{ padding: '24px', maxWidth: '800px', margin: '0 auto' }}>
      <Card>
        <Title level={2}>微博AI内容管理器 - 测试页面</Title>
        <Text>如果你能看到这个页面，说明前端基础功能正常。</Text>
        <br />
        <br />
        <Button type="primary">测试按钮</Button>
      </Card>
    </div>
  )
} 