<template>
  <div class="dashboard-container">
    <div class="dashboard-header">
      <div class="header-content">
        <div class="welcome-section">
          <h1 class="dashboard-title">仪表板</h1>
          <p class="welcome-text">欢迎回来, <span class="username">{{ userProfile.username }}</span></p>
        </div>
        <div class="header-actions">
          <el-button type="primary" @click="refreshData" :loading="loading" class="refresh-btn">
            <el-icon><Refresh /></el-icon>
            刷新数据
          </el-button>
        </div>
      </div>
    </div>

    <!-- 关键指标卡片 -->
    <div class="stats-section">
      <div class="stats-grid">
        <div class="stat-card primary-card">
          <div class="stat-icon">
            <el-icon size="24" color="#409eff"><Key /></el-icon>
          </div>
          <div class="stat-info">
            <h3 class="stat-label">总密钥数</h3>
            <p class="stat-value">{{ statistics.total_api_keys !== undefined ? statistics.total_api_keys : '∞' }}</p>
          </div>
        </div>
        
        <div class="stat-card info-card">
          <div class="stat-icon">
            <el-icon size="24" color="#909399"><DataLine /></el-icon>
          </div>
          <div class="stat-info">
            <h3 class="stat-label">总调用</h3>
            <p class="stat-value">{{ Math.max(0, statistics.summary?.total_calls || 0) }}</p>
          </div>
        </div>
        
        <div class="stat-card warning-card">
          <div class="stat-icon">
            <el-icon size="24" color="#e6a23c"><Clock /></el-icon>
          </div>
          <div class="stat-info">
            <h3 class="stat-label">今日调用</h3>
            <p class="stat-value">{{ todayCalls }}</p>
          </div>
        </div>
        
        <div class="stat-card success-card">
          <div class="stat-icon">
            <el-icon size="24" color="#67c23a"><Medal /></el-icon>
          </div>
          <div class="stat-info">
            <h3 class="stat-label">剩余配额</h3>
            <p class="stat-value">∞</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="charts-section">
      <el-row :gutter="20">
        <el-col :span="16">
          <div class="chart-card">
            <div class="card-header">
              <h3 class="chart-title">最近7天调用统计</h3>
            </div>
            <div class="chart-container">
              <div ref="chartRef" class="chart-wrapper"></div>
            </div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="chart-card">
            <div class="card-header">
              <h3 class="chart-title">调用成功/失败</h3>
            </div>
            <div class="chart-container">
              <div ref="successFailChartRef" class="chart-wrapper"></div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- API调用类型统计 -->
    <div class="charts-section">
      <el-row :gutter="20">
        <el-col :span="12">
          <div class="chart-card">
            <div class="card-header">
              <h3 class="chart-title">API调用类型统计</h3>
            </div>
            <div class="chart-container">
              <div ref="apiTypeChartRef" class="chart-wrapper"></div>
            </div>
          </div>
        </el-col>
        <el-col :span="12">
          <div class="chart-card">
            <div class="card-header">
              <h3 class="chart-title">情感分析 vs 文本分词</h3>
            </div>
            <div class="chart-container">
              <div ref="barChartRef" class="chart-wrapper"></div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import * as echarts from 'echarts'
import type { ECharts } from 'echarts'
import { getUserStatistics, getUserProfile } from '@/api/user'
import type { UserProfile } from '@/api/user'
import { ElMessage } from 'element-plus'
import { 
  Key, 
  DataLine, 
  Medal, 
  Clock,
  Refresh
} from '@element-plus/icons-vue'
import { getBeijingToday } from '@/utils/date'

// 定义数据接口
interface DailyCall {
  date: string
  count: number
}

interface EndpointUsage {
  endpoint: string
  count: number
}

interface StatisticsData {
  period: string
  date_range: {
    start_date: string
    end_date: string
  }
  summary: {
    total_calls: number
    successful_calls: number
    failed_calls: number
    avg_response_time: number
  }
  daily_calls: DailyCall[]
  endpoint_usage: EndpointUsage[]
  total_api_keys?: number
}

const authStore = useAuthStore()
const loading = ref(false)

// 用户基本信息
const userProfile = ref<UserProfile>({
  id: 0,
  username: '',
  email: '',
  created_at: '',
  last_login: null,
  is_active: true,
  email_verified: false
})

// 统计数据
const statistics = ref<StatisticsData>({
  period: 'week',
  date_range: {
    start_date: '',
    end_date: ''
  },
  summary: {
    total_calls: 0,
    successful_calls: 0,
    failed_calls: 0,
    avg_response_time: 0
  },
  daily_calls: [],
  endpoint_usage: [],
  total_api_keys: 0
})

// 计算今日调用次数 - 修复逻辑确保正确显示
const todayCalls = computed(() => {
  // 获取今天的日期字符串 (YYYY-MM-DD) - 使用北京时间
  const today = getBeijingToday()
  
  // 在daily_calls中查找今天的记录
  const todayData = statistics.value.daily_calls.find(item => item.date === today)
  
  // 添加调试信息
  console.log('Today date (Beijing):', today)
  console.log('Daily calls:', statistics.value.daily_calls)
  console.log('Today data:', todayData)
  
  // 如果找到今天的记录，返回调用次数；否则返回0
  return todayData ? Math.max(0, todayData.count) : 0
})

// 图表引用
const chartRef = ref<HTMLDivElement | null>(null)
const apiTypeChartRef = ref<HTMLDivElement | null>(null)
const barChartRef = ref<HTMLDivElement | null>(null)
const successFailChartRef = ref<HTMLDivElement | null>(null)
let chartInstance: ECharts | null = null
let apiTypeChartInstance: ECharts | null = null
let barChartInstance: ECharts | null = null
let successFailChartInstance: ECharts | null = null

// 刷新数据
const refreshData = async () => {
  loading.value = true
  try {
    await Promise.all([
      loadUserProfile(),
      loadStatistics()
    ])
    ElMessage.success('数据刷新成功')
  } catch (error) {
    ElMessage.error('数据刷新失败')
  } finally {
    loading.value = false
  }
}

// 初始化图表
const initChart = () => {
  if (chartRef.value) {
    chartInstance = echarts.init(chartRef.value)
  }
  if (apiTypeChartRef.value) {
    apiTypeChartInstance = echarts.init(apiTypeChartRef.value)
  }
  if (barChartRef.value) {
    barChartInstance = echarts.init(barChartRef.value)
  }
  if (successFailChartRef.value) {
    successFailChartInstance = echarts.init(successFailChartRef.value)
  }
  updateChart()
  updateApiTypeChart()
  updateBarChart()
  updateSuccessFailChart()
}

// 更新主图表（最近7天调用统计）
const updateChart = () => {
  if (chartInstance && statistics.value.daily_calls.length > 0) {
    const dates = statistics.value.daily_calls.map((item: DailyCall) => item.date)
    // 确保数量是自然整数
    const counts = statistics.value.daily_calls.map((item: DailyCall) => Math.max(0, Math.floor(item.count)))
    
    // 计算Y轴的最大值，增加10%的顶部边距以改善视觉效果
    const maxValue = Math.max(...counts, 0)
    const yAxisMax = maxValue > 0 ? Math.ceil(maxValue * 1.1) : 10
    
    // 当最大值较小时，使用更合适的间隔
    let interval = null
    if (yAxisMax <= 10) {
      interval = 1
    } else if (yAxisMax <= 50) {
      interval = 5
    } else if (yAxisMax <= 100) {
      interval = 10
    } else {
      interval = Math.ceil(yAxisMax / 10)
    }
    
    // 为不同的日期生成颜色渐变
    const colors = [
      '#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', 
      '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc'
    ]
    
    // 创建数据项数组，每个数据项包含值和颜色
    const dataItems = counts.map((count: number, index: number) => ({
      value: count,
      itemStyle: {
        color: colors[index % colors.length]
      }
    }))
    
    const option = {
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(15, 26, 48, 0.9)',
        borderColor: 'rgba(64, 158, 255, 0.5)',
        textStyle: {
          color: '#fff'
        },
        formatter: (params: any) => {
          return `${params.name}<br/>调用次数: ${params.value}`
        }
      },
      xAxis: {
        type: 'category',
        data: dates,
        axisLabel: {
          color: '#a0c3ff',
          rotate: 45
        },
        axisLine: {
          lineStyle: {
            color: 'rgba(255, 255, 255, 0.1)'
          }
        }
      },
      yAxis: {
        type: 'value',
        min: 0,
        max: yAxisMax,
        interval: interval,
        axisLabel: {
          color: '#a0c3ff',
          formatter: (value: number) => {
            const intValue = Math.max(0, Math.floor(value))
            return intValue.toString()
          }
        },
        splitLine: {
          show: true,
          lineStyle: {
            color: 'rgba(255, 255, 255, 0.05)'
          }
        }
      },
      series: [{
        data: dataItems,
        type: 'bar',
        barWidth: '60%',
        label: {
          show: true,
          position: 'top',
          color: '#fff',
          formatter: (params: any) => {
            return Math.max(0, Math.floor(params.value)).toString()
          }
        },
        itemStyle: {
          borderRadius: [4, 4, 0, 0],
          color: (params: any) => {
            return colors[params.dataIndex % colors.length]
          }
        }
      }],
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%',
        top: '10%',
        containLabel: true
      }
    }
    
    chartInstance.setOption(option)
  }
}

// 更新API调用类型统计图表
const updateApiTypeChart = () => {
  if (apiTypeChartInstance && statistics.value.endpoint_usage.length > 0) {
    // 按端点分组统计
    const endpointData = statistics.value.endpoint_usage.map((item: EndpointUsage) => ({
      name: item.endpoint,
      value: item.count
    }))
    
    // 颜色方案
    const colors = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452']
    
    const option = {
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(15, 26, 48, 0.9)',
        borderColor: 'rgba(64, 158, 255, 0.5)',
        textStyle: {
          color: '#fff'
        },
        formatter: '{a} <br/>{b}: {c} ({d}%)'
      },
      legend: {
        bottom: '5%',
        left: 'center',
        textStyle: {
          color: '#a0c3ff'
        }
      },
      series: [{
        name: '调用类型',
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['50%', '45%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 6,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: '16',
            fontWeight: 'bold',
            formatter: '{b}\n{d}%'
          }
        },
        labelLine: {
          show: false
        },
        data: endpointData,
        color: colors
      }]
    }
    
    apiTypeChartInstance.setOption(option)
  }
}

// 更新柱状图（情感分析 vs 文本分词）
const updateBarChart = () => {
  if (barChartInstance && statistics.value.endpoint_usage.length > 0) {
    // 分别统计情感分析和文本分词的调用次数
    let emotionCount = 0
    let segmentCount = 0
    
    statistics.value.endpoint_usage.forEach((item: EndpointUsage) => {
      if (item.endpoint.includes('analyze')) {
        emotionCount += item.count
      } else if (item.endpoint.includes('segment')) {
        segmentCount += item.count
      }
    })
    
    const data = [
      { name: '情感分析', value: emotionCount },
      { name: '文本分词', value: segmentCount }
    ]
    
    const option = {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        },
        backgroundColor: 'rgba(15, 26, 48, 0.9)',
        borderColor: 'rgba(64, 158, 255, 0.5)',
        textStyle: {
          color: '#fff'
        },
        formatter: (params: any) => {
          return `${params[0].name}<br/>调用次数: ${params[0].value}`
        }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%',
        top: '10%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: data.map(item => item.name),
        axisLabel: {
          color: '#a0c3ff'
        },
        axisLine: {
          lineStyle: {
            color: 'rgba(255, 255, 255, 0.1)'
          }
        }
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          color: '#a0c3ff'
        },
        splitLine: {
          show: true,
          lineStyle: {
            color: 'rgba(255, 255, 255, 0.05)'
          }
        }
      },
      series: [{
        data: data.map(item => item.value),
        type: 'bar',
        barWidth: '50%',
        itemStyle: {
          borderRadius: [4, 4, 0, 0],
          color: (params: any) => {
            const colors = ['#5470c6', '#91cc75']
            return colors[params.dataIndex]
          }
        },
        label: {
          show: true,
          position: 'top',
          color: '#fff',
          formatter: (params: any) => {
            return Math.max(0, Math.floor(params.value)).toString()
          }
        }
      }]
    }
    
    barChartInstance.setOption(option)
  }
}

// 更新成功/失败图表
const updateSuccessFailChart = () => {
  if (successFailChartInstance) {
    const successCount = statistics.value.summary?.successful_calls || 0
    const failCount = statistics.value.summary?.failed_calls || 0
    
    const data = [
      { name: '成功', value: successCount },
      { name: '失败', value: failCount }
    ]
    
    const option = {
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(15, 26, 48, 0.9)',
        borderColor: 'rgba(64, 158, 255, 0.5)',
        textStyle: {
          color: '#fff'
        },
        formatter: '{a} <br/>{b}: {c} ({d}%)'
      },
      legend: {
        bottom: '5%',
        left: 'center',
        textStyle: {
          color: '#a0c3ff'
        }
      },
      series: [{
        name: '调用结果',
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['50%', '45%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 6,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: '16',
            fontWeight: 'bold',
            formatter: '{b}\n{d}%'
          }
        },
        labelLine: {
          show: false
        },
        data: data,
        color: ['#67c23a', '#f56c6c']
      }]
    }
    
    successFailChartInstance.setOption(option)
  }
}

// 加载用户统计数据
const loadStatistics = async () => {
  try {
    const response = await getUserStatistics()
    statistics.value = response
    
    // 更新所有图表
    updateChart()
    updateApiTypeChart()
    updateBarChart()
    updateSuccessFailChart()
  } catch (error) {
    console.error('加载统计数据失败:', error)
    ElMessage.error('加载统计数据失败')
  }
}

// 加载用户基本信息
const loadUserProfile = async () => {
  try {
    const response = await getUserProfile()
    userProfile.value = response
  } catch (error) {
    console.error('加载用户信息失败:', error)
    ElMessage.error('加载用户信息失败')
  }
}

// 组件挂载时加载数据
onMounted(async () => {
  await Promise.all([
    loadUserProfile(),
    loadStatistics()
  ])
  initChart()
  
  // 监听窗口大小变化，重新调整图表大小
  window.addEventListener('resize', () => {
    if (chartInstance) chartInstance.resize()
    if (apiTypeChartInstance) apiTypeChartInstance.resize()
    if (barChartInstance) barChartInstance.resize()
    if (successFailChartInstance) successFailChartInstance.resize()
  })
})

// 监听统计数据变化，更新图表
watch(() => statistics.value, () => {
  updateChart()
  updateApiTypeChart()
  updateBarChart()
  updateSuccessFailChart()
}, { deep: true })

// 组件卸载时销毁图表实例
// 注意：在Vue 3的setup语法中，需要手动处理组件卸载
</script>

<style scoped>
.dashboard-container {
  padding: 20px;
  background: linear-gradient(135deg, #0f1a30 0%, #1d2b4f 100%);
  min-height: calc(100vh - 60px);
  color: #fff;
}

.dashboard-header {
  margin-bottom: 30px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 20px;
}

.welcome-section h1 {
  font-size: 2rem;
  margin-bottom: 10px;
  color: #fff;
}

.welcome-text {
  font-size: 1.1rem;
  color: #a0c3ff;
}

.username {
  color: #409eff;
  font-weight: bold;
}

.refresh-btn {
  background: rgba(64, 158, 255, 0.1);
  border-color: rgba(64, 158, 255, 0.3);
  color: #409eff;
}

.refresh-btn:hover {
  background: rgba(64, 158, 255, 0.2);
  border-color: rgba(64, 158, 255, 0.5);
}

.stats-section {
  margin-bottom: 30px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
}

.stat-card {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 15px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 15px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
  border-color: rgba(64, 158, 255, 0.3);
}

.stat-icon {
  width: 50px;
  height: 50px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.1);
}

.primary-card .stat-icon {
  background: rgba(64, 158, 255, 0.1);
}

.info-card .stat-icon {
  background: rgba(144, 147, 153, 0.1);
}

.warning-card .stat-icon {
  background: rgba(230, 162, 60, 0.1);
}

.success-card .stat-icon {
  background: rgba(103, 194, 58, 0.1);
}

.stat-label {
  font-size: 0.9rem;
  color: #909399;
  margin: 0 0 5px 0;
}

.stat-value {
  font-size: 1.8rem;
  font-weight: 600;
  margin: 0;
  color: #fff;
}

.primary-card .stat-value {
  color: #409eff;
}

.info-card .stat-value {
  color: #909399;
}

.warning-card .stat-value {
  color: #e6a23c;
}

.success-card .stat-value {
  color: #67c23a;
}

.charts-section {
  margin-bottom: 30px;
}

.chart-card {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 15px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s ease;
  margin-bottom: 20px;
}

.chart-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
  border-color: rgba(64, 158, 255, 0.3);
}

.card-header {
  padding: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.chart-title {
  font-size: 1.3rem;
  font-weight: 600;
  margin: 0;
  color: #fff;
}

.chart-container {
  padding: 20px;
}

.chart-wrapper {
  width: 100%;
  height: 300px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .dashboard-container {
    padding: 15px;
  }
  
  .header-content {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .chart-wrapper {
    height: 250px;
  }
}
</style>