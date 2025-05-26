/**
 * 微博AI内容管理器主页面
 * 
 * 提供微博内容分析和删除的完整界面
 */
'use client'

import React, { useState, useEffect } from 'react'
import {
  Steps,
  Card,
  Form,
  DatePicker,
  Input,
  InputNumber,
  Button,
  Table,
  Progress,
  Alert,
  Space,
  Tag,
  Modal,
  message,
  Statistic,
  Row,
  Col,
  Typography,
  Tabs,
  Divider
} from 'antd'
import {
  SearchOutlined,
  DeleteOutlined,
  ExclamationCircleOutlined,
  ReloadOutlined,
  StopOutlined,
  LoginOutlined,
  UserOutlined,
  LogoutOutlined
} from '@ant-design/icons'
import dayjs from 'dayjs'
import api from '../services/api'
import type { AnalysisRequest, AnalysisResult, TaskStatus, LoginRequest } from '../services/api'

const { Step } = Steps
const { RangePicker } = DatePicker
const { TextArea } = Input
const { Title, Text } = Typography
const { confirm } = Modal
const { TabPane } = Tabs

interface WeiboManagerProps {}

const WeiboManager: React.FC<WeiboManagerProps> = () => {
  // 状态管理
  const [currentStep, setCurrentStep] = useState(0)
  const [form] = Form.useForm()
  const [loginForm] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [loginTask, setLoginTask] = useState<TaskStatus | null>(null)
  const [analysisTask, setAnalysisTask] = useState<TaskStatus | null>(null)
  const [deleteTask, setDeleteTask] = useState<TaskStatus | null>(null)
  const [analysisResults, setAnalysisResults] = useState<AnalysisResult[]>([])
  const [selectedPosts, setSelectedPosts] = useState<string[]>([])
  const [stats, setStats] = useState<any>(null)
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [userInfo, setUserInfo] = useState<any>(null)
  const [activeTab, setActiveTab] = useState('login')

  // 轮询任务状态
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null

    // 登录任务轮询
    if (loginTask?.task_id && loginTask.status === 'PROGRESS') {
      interval = setInterval(async () => {
        try {
          // 检查扫码登录状态
          const qrStatus = await api.checkQRLoginStatus(loginTask.task_id)
          setLoginTask({
            ...loginTask,
            message: qrStatus.message,
            progress: qrStatus.qr_status === 'confirmed' ? 100 : 
                     qrStatus.qr_status === 'scanned' ? 50 : 25
          })

          if (qrStatus.qr_status === 'confirmed') {
            setIsLoggedIn(true)
            setUserInfo(qrStatus.user_info)
            setActiveTab('analyze')
            message.success('扫码登录成功！')
            setLoginTask(null)
          } else if (qrStatus.qr_status === 'expired' || qrStatus.qr_status === 'error') {
            message.error(`登录失败: ${qrStatus.error || '二维码已过期'}`)
            setLoginTask(null)
          }
        } catch (error) {
          console.error('获取登录任务状态失败:', error)
          // 如果扫码状态检查失败，回退到普通任务状态检查
          try {
            const status = await api.getTaskStatus(loginTask.task_id)
            setLoginTask(status)

            if (status.status === 'SUCCESS') {
              setIsLoggedIn(true)
              setUserInfo(status.result?.user_info)
              setActiveTab('analyze')
              message.success('登录成功！')
            } else if (status.status === 'FAILURE') {
              message.error(`登录失败: ${status.error}`)
            }
          } catch (fallbackError) {
            console.error('获取任务状态失败:', fallbackError)
          }
        }
      }, 3000) // 扫码登录检查间隔稍长一些
    }

    // 分析任务轮询
    if (analysisTask?.task_id && analysisTask.status === 'PROGRESS') {
      interval = setInterval(async () => {
        try {
          const status = await api.getTaskStatus(analysisTask.task_id)
          setAnalysisTask(status)

          if (status.status === 'SUCCESS') {
            setAnalysisResults(status.result?.analyzed_posts || [])
            setCurrentStep(2)
            message.success('分析完成！')
          } else if (status.status === 'FAILURE') {
            message.error(`分析失败: ${status.error}`)
          }
        } catch (error) {
          console.error('获取分析任务状态失败:', error)
        }
      }, 2000)
    }

    // 删除任务轮询
    if (deleteTask?.task_id && deleteTask.status === 'PROGRESS') {
      interval = setInterval(async () => {
        try {
          const status = await api.getTaskStatus(deleteTask.task_id)
          setDeleteTask(status)

          if (status.status === 'SUCCESS') {
            setCurrentStep(3)
            message.success('删除完成！')
          } else if (status.status === 'FAILURE') {
            message.error(`删除失败: ${status.error}`)
          }
        } catch (error) {
          console.error('获取删除任务状态失败:', error)
        }
      }, 2000)
    }

    return () => {
      if (interval) clearInterval(interval)
    }
  }, [loginTask, analysisTask, deleteTask])

  // 获取系统统计信息
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const statsData = await api.getStats()
        setStats(statsData)
      } catch (error) {
        console.error('获取统计信息失败:', error)
      }
    }
    fetchStats()
  }, [])

  // 扫码登录微博
  const handleQRLogin = async () => {
    try {
      setLoading(true)
      const response = await api.loginWeibo()
      setLoginTask({
        task_id: response.task_id,
        status: 'PROGRESS',
        message: response.message
      })
      message.success('扫码登录任务已创建')
    } catch (error) {
      message.error('创建扫码登录任务失败')
    } finally {
      setLoading(false)
    }
  }

  // 密码登录微博
  const handlePasswordLogin = async (values: LoginRequest) => {
    try {
      setLoading(true)
      const response = await api.loginWeiboPassword(values)
      setLoginTask({
        task_id: response.task_id,
        status: 'PROGRESS',
        message: response.message
      })
      message.success('密码登录任务已创建')
    } catch (error) {
      message.error('创建密码登录任务失败')
    } finally {
      setLoading(false)
    }
  }

  // 登出
  const handleLogout = () => {
    setIsLoggedIn(false)
    setUserInfo(null)
    setActiveTab('login')
    setCurrentStep(0)
    setAnalysisTask(null)
    setDeleteTask(null)
    setAnalysisResults([])
    setSelectedPosts([])
    form.resetFields()
    loginForm.resetFields()
    message.success('已登出')
  }

  // 开始分析
  const handleAnalyze = async (values: any) => {
    if (!isLoggedIn) {
      message.warning('请先登录微博账号')
      return
    }

    try {
      setLoading(true)
      
      const request: AnalysisRequest = {
        time_range: values.dateRange ? {
          start_date: values.dateRange[0].format('YYYY-MM-DD'),
          end_date: values.dateRange[1].format('YYYY-MM-DD')
        } : undefined,
        keywords: values.keywords ? values.keywords.split('\n').filter(Boolean) : [],
        max_posts: values.maxPosts || 100
      }

      const response = await api.analyzeContent(request)
      setAnalysisTask({
        task_id: response.task_id,
        status: 'PROGRESS',
        message: response.message
      })
      setCurrentStep(1)
      message.success('分析任务已创建')
    } catch (error) {
      message.error('创建分析任务失败')
    } finally {
      setLoading(false)
    }
  }

  // 批量删除
  const handleBatchDelete = () => {
    if (selectedPosts.length === 0) {
      message.warning('请选择要删除的微博')
      return
    }

    confirm({
      title: '确认删除',
      icon: <ExclamationCircleOutlined />,
      content: `确定要删除选中的 ${selectedPosts.length} 条微博吗？此操作不可撤销。`,
      okText: '确认删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          setLoading(true)
          const response = await api.deletePosts({
            post_ids: selectedPosts,
            confirm: true
          })
          
          setDeleteTask({
            task_id: response.task_id,
            status: 'PROGRESS',
            message: response.message
          })
          message.success('删除任务已创建')
        } catch (error) {
          message.error('创建删除任务失败')
        } finally {
          setLoading(false)
        }
      }
    })
  }

  // 取消任务
  const handleCancelTask = async (taskId: string) => {
    try {
      await api.cancelTask(taskId)
      message.success('任务已取消')
      if (loginTask?.task_id === taskId) {
        setLoginTask(null)
      }
      if (analysisTask?.task_id === taskId) {
        setAnalysisTask(null)
      }
      if (deleteTask?.task_id === taskId) {
        setDeleteTask(null)
      }
    } catch (error) {
      message.error('取消任务失败')
    }
  }

  // 重新开始
  const handleRestart = () => {
    setCurrentStep(0)
    setAnalysisTask(null)
    setDeleteTask(null)
    setAnalysisResults([])
    setSelectedPosts([])
    form.resetFields()
  }

  // 获取风险等级标签
  const getRiskTag = (score: number) => {
    if (score >= 7) return <Tag color="red">高风险</Tag>
    if (score >= 4) return <Tag color="orange">中风险</Tag>
    return <Tag color="green">低风险</Tag>
  }

  // 表格列定义
  const columns = [
    {
      title: '微博ID',
      dataIndex: 'post_id',
      key: 'post_id',
      width: 120,
      ellipsis: true
    },
    {
      title: '内容摘要',
      dataIndex: 'content',
      key: 'content',
      ellipsis: true,
      render: (text: string) => (
        <Text ellipsis={{ tooltip: text }} style={{ maxWidth: 300 }}>
          {text}
        </Text>
      )
    },
    {
      title: '发布日期',
      dataIndex: 'date',
      key: 'date',
      width: 120
    },
    {
      title: '风险分数',
      dataIndex: 'risk_score',
      key: 'risk_score',
      width: 100,
      render: (score: number) => (
        <Space>
          <span>{score.toFixed(1)}</span>
          {getRiskTag(score)}
        </Space>
      ),
      sorter: (a: AnalysisResult, b: AnalysisResult) => b.risk_score - a.risk_score
    },
    {
      title: '风险原因',
      dataIndex: 'risk_reason',
      key: 'risk_reason',
      ellipsis: true
    },
    {
      title: '风险类别',
      dataIndex: 'risk_category',
      key: 'risk_category',
      width: 120,
      ellipsis: true
    },
    {
      title: '处理建议',
      dataIndex: 'suggestion',
      key: 'suggestion',
      ellipsis: true
    }
  ]

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <Title level={2}>微博AI内容管理器</Title>
        {isLoggedIn && userInfo && (
          <Space>
            <UserOutlined />
            <Text strong>{userInfo.nickname}</Text>
            <Button 
              type="link" 
              icon={<LogoutOutlined />} 
              onClick={handleLogout}
            >
              登出
            </Button>
          </Space>
        )}
      </div>
      
      {/* 系统统计 */}
      {stats && (
        <Row gutter={16} style={{ marginBottom: '24px' }}>
          <Col span={6}>
            <Card>
              <Statistic title="活跃任务" value={stats.active_tasks} />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic title="等待任务" value={stats.reserved_tasks} />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic title="每小时删除限制" value={stats.max_delete_per_hour} />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic 
                title="操作延迟" 
                value={stats.operation_delay_range} 
                formatter={(value) => <span>{value}</span>}
              />
            </Card>
          </Col>
        </Row>
      )}

      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        {/* 登录标签页 */}
        <TabPane tab="登录微博" key="login" disabled={isLoggedIn}>
          <Card title="登录微博账号">
            <Alert
              message="安全提示"
              description="请确保在安全的网络环境下使用，建议使用小号进行测试。登录信息仅用于自动化操作，不会被存储。"
              type="warning"
              style={{ marginBottom: '24px' }}
            />
            
            {loginTask?.status === 'PROGRESS' ? (
              <Space direction="vertical" style={{ width: '100%' }}>
                <Progress percent={loginTask.progress || 0} status="active" />
                <Text>{loginTask.message}</Text>
                <Button
                  danger
                  icon={<StopOutlined />}
                  onClick={() => handleCancelTask(loginTask.task_id)}
                >
                  取消登录
                </Button>
              </Space>
            ) : (
              <Tabs defaultActiveKey="qr" style={{ maxWidth: '500px' }}>
                <TabPane tab="扫码登录（推荐）" key="qr">
                  <Space direction="vertical" style={{ width: '100%', textAlign: 'center' }}>
                    <Alert
                      message="扫码登录"
                      description="使用微博APP扫描二维码登录，更安全便捷"
                      type="info"
                      style={{ marginBottom: '24px' }}
                    />
                    <Button
                      type="primary"
                      onClick={handleQRLogin}
                      loading={loading}
                      icon={<LoginOutlined />}
                      size="large"
                      block
                    >
                      生成登录二维码
                    </Button>
                  </Space>
                </TabPane>
                
                <TabPane tab="密码登录" key="password">
                  <Alert
                    message="密码登录"
                    description="注意：现在很多微博账号不支持密码登录，建议使用扫码登录"
                    type="warning"
                    style={{ marginBottom: '24px' }}
                  />
                  <Form
                    form={loginForm}
                    layout="vertical"
                    onFinish={handlePasswordLogin}
                  >
                    <Form.Item
                      name="username"
                      label="用户名/手机号/邮箱"
                      rules={[{ required: true, message: '请输入用户名' }]}
                    >
                      <Input 
                        prefix={<UserOutlined />}
                        placeholder="请输入微博用户名"
                        size="large"
                      />
                    </Form.Item>

                    <Form.Item
                      name="password"
                      label="密码"
                      rules={[{ required: true, message: '请输入密码' }]}
                    >
                      <Input.Password 
                        placeholder="请输入密码"
                        size="large"
                      />
                    </Form.Item>

                    <Form.Item>
                      <Button
                        type="primary"
                        htmlType="submit"
                        loading={loading}
                        icon={<LoginOutlined />}
                        size="large"
                        block
                      >
                        密码登录
                      </Button>
                    </Form.Item>
                  </Form>
                </TabPane>
              </Tabs>
            )}
          </Card>
        </TabPane>

        {/* 分析标签页 */}
        <TabPane tab="内容分析" key="analyze" disabled={!isLoggedIn}>
          {/* 步骤指示器 */}
          <Steps current={currentStep} style={{ marginBottom: '24px' }}>
            <Step title="设置条件" description="配置分析参数" />
            <Step title="分析进度" description="AI正在分析内容" />
            <Step title="查看结果" description="选择要删除的微博" />
            <Step title="删除完成" description="查看删除结果" />
          </Steps>

          {/* 步骤1: 条件设置 */}
          {currentStep === 0 && (
            <Card title="设置分析条件">
              <Form
                form={form}
                layout="vertical"
                onFinish={handleAnalyze}
              >
                <Form.Item
                  name="dateRange"
                  label="时间范围"
                  tooltip="选择要分析的微博发布时间范围，留空则分析所有微博"
                >
                  <RangePicker 
                    style={{ width: '100%' }}
                    placeholder={['开始日期', '结束日期']}
                  />
                </Form.Item>

                <Form.Item
                  name="keywords"
                  label="关键词过滤"
                  tooltip="每行一个关键词，留空则分析所有微博"
                >
                  <TextArea
                    rows={4}
                    placeholder="输入关键词，每行一个&#10;例如：&#10;政治&#10;敏感词&#10;个人信息"
                  />
                </Form.Item>

                <Form.Item
                  name="maxPosts"
                  label="最大分析数量"
                  initialValue={100}
                  tooltip="单次分析的微博数量上限"
                >
                  <InputNumber
                    min={1}
                    max={1000}
                    style={{ width: '100%' }}
                  />
                </Form.Item>

                <Form.Item>
                  <Button
                    type="primary"
                    htmlType="submit"
                    loading={loading}
                    icon={<SearchOutlined />}
                    size="large"
                  >
                    开始分析
                  </Button>
                </Form.Item>
              </Form>
            </Card>
          )}

          {/* 步骤2: 分析进度 */}
          {currentStep === 1 && analysisTask && (
            <Card title="分析进度">
              <Space direction="vertical" style={{ width: '100%' }}>
                <Progress
                  percent={analysisTask.progress || 0}
                  status={analysisTask.status === 'FAILURE' ? 'exception' : 'active'}
                />
                <Text>{analysisTask.message}</Text>
                {analysisTask.status === 'PROGRESS' && (
                  <Button
                    danger
                    icon={<StopOutlined />}
                    onClick={() => handleCancelTask(analysisTask.task_id)}
                  >
                    取消任务
                  </Button>
                )}
              </Space>
            </Card>
          )}

          {/* 步骤3: 查看结果 */}
          {currentStep === 2 && (
            <Card 
              title="分析结果"
              extra={
                <Space>
                  <Button icon={<ReloadOutlined />} onClick={handleRestart}>
                    重新分析
                  </Button>
                  <Button
                    type="primary"
                    danger
                    icon={<DeleteOutlined />}
                    onClick={handleBatchDelete}
                    disabled={selectedPosts.length === 0}
                    loading={loading}
                  >
                    删除选中 ({selectedPosts.length})
                  </Button>
                </Space>
              }
            >
              {analysisResults.length > 0 ? (
                <>
                  <Alert
                    message={`共分析 ${analysisResults.length} 条微博`}
                    description={`高风险: ${analysisResults.filter(p => p.risk_score >= 7).length} 条，中风险: ${analysisResults.filter(p => p.risk_score >= 4 && p.risk_score < 7).length} 条，低风险: ${analysisResults.filter(p => p.risk_score < 4).length} 条`}
                    type="info"
                    style={{ marginBottom: '16px' }}
                  />
                  <Table
                    columns={columns}
                    dataSource={analysisResults}
                    rowKey="post_id"
                    rowSelection={{
                      selectedRowKeys: selectedPosts,
                      onChange: (selectedRowKeys) => setSelectedPosts(selectedRowKeys as string[]),
                      getCheckboxProps: (record) => ({
                        name: record.post_id
                      })
                    }}
                    pagination={{
                      pageSize: 10,
                      showSizeChanger: true,
                      showQuickJumper: true,
                      showTotal: (total, range) => 
                        `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
                    }}
                  />
                </>
              ) : (
                <Alert
                  message="未找到符合条件的微博"
                  description="请调整分析条件后重试"
                  type="warning"
                />
              )}
            </Card>
          )}

          {/* 步骤4: 删除完成 */}
          {currentStep === 3 && deleteTask && (
            <Card title="删除结果">
              <Space direction="vertical" style={{ width: '100%' }}>
                {deleteTask.status === 'PROGRESS' && (
                  <>
                    <Progress
                      percent={deleteTask.progress || 0}
                      status="active"
                    />
                    <Text>{deleteTask.message}</Text>
                    <Button
                      danger
                      icon={<StopOutlined />}
                      onClick={() => handleCancelTask(deleteTask.task_id)}
                    >
                      取消删除
                    </Button>
                  </>
                )}
                
                {deleteTask.status === 'SUCCESS' && deleteTask.result && (
                  <>
                    <Alert
                      message="删除完成"
                      description={`成功删除 ${deleteTask.result.successful_count} 条，失败 ${deleteTask.result.failed_count} 条`}
                      type="success"
                    />
                    <Button type="primary" onClick={handleRestart}>
                      重新开始
                    </Button>
                  </>
                )}

                {deleteTask.status === 'FAILURE' && (
                  <>
                    <Alert
                      message="删除失败"
                      description={deleteTask.error}
                      type="error"
                    />
                    <Button onClick={handleRestart}>
                      重新开始
                    </Button>
                  </>
                )}
              </Space>
            </Card>
          )}
        </TabPane>
      </Tabs>
    </div>
  )
}

export default WeiboManager 