# 前端开发指南

## 已完成的功能

### ✅ 基础架构
- React 18 + TypeScript 项目搭建
- Chakra UI 组件库集成
- React Query 数据管理
- React Router 路由管理
- WebSocket 实时通信

### ✅ API 集成
- 完整的 API 客户端（Axios）
- 小说 CRUD 操作
- 章节管理
- 风格管理
- 错误处理和拦截器

### ✅ 核心功能
- 小说列表页面
- 创建小说对话框
- 小说详情页面
- WebSocket 实时进度显示
- 自动数据刷新

## 项目结构

```
frontend/
├── public/               # 静态资源
├── src/
│   ├── api/             # API 客户端
│   │   ├── client.ts    # Axios 配置
│   │   └── novels.ts    # 小说 API
│   ├── components/      # React 组件
│   │   ├── NovelCard.tsx
│   │   ├── CreateNovelModal.tsx
│   │   └── ProgressMonitor.tsx
│   ├── contexts/        # Context
│   │   └── WebSocketContext.tsx
│   ├── hooks/           # 自定义 Hooks
│   │   ├── useNovels.ts
│   │   └── useWebSocket.ts
│   ├── pages/           # 页面组件
│   │   ├── HomePage.tsx
│   │   └── NovelDetailPage.tsx
│   ├── types/           # TypeScript 类型
│   │   └── index.ts
│   ├── App.tsx          # 主应用
│   ├── index.tsx        # 入口文件
│   └── index.css        # 全局样式
├── .env                 # 环境变量
├── package.json         # 依赖配置
├── tsconfig.json        # TypeScript 配置
└── README.md            # 使用说明
```

## 快速开始

### 1. 确保后端运行

```bash
# 在项目根目录
./start_api.sh
```

### 2. 启动前端

```bash
cd frontend
npm start
```

应用将在 http://localhost:3000 打开。

## 主要组件说明

### HomePage
- 显示所有小说列表
- 创建新小说按钮
- WebSocket 实时进度监控
- 删除小说功能

### NovelDetailPage
- 显示小说详细信息
- 角色列表
- 情节点列表
- 章节列表
- 写作章节功能

### NovelCard
- 小说卡片组件
- 显示标题、类型、风格
- 进度条
- 操作按钮

### CreateNovelModal
- 创建小说对话框
- 表单验证
- 风格选择
- 章节数量设置

### ProgressMonitor
- WebSocket 实时进度显示
- 进度条动画
- 任务状态提示

## 待开发功能

### 高优先级

1. **章节编辑器** (Task #12)
   - Monaco Editor 或 Slate.js
   - 自动保存
   - 字数统计
   - Markdown 支持

2. **章节操作** (Task #12)
   - 润色功能
   - 评审功能
   - 导出功能

3. **用户体验优化**
   - 加载状态优化
   - 错误提示优化
   - 空状态设计

### 中优先级

4. **高级功能**
   - 多章节批量操作
   - 版本历史
   - 搜索功能
   - 过滤和排序

5. **可视化**
   - 角色关系图
   - 情节时间线
   - 创作统计图表

### 低优先级

6. **其他功能**
   - 用户认证
   - 暗色模式
   - 多语言支持
   - 离线支持

## 开发技巧

### 添加新页面

```typescript
// 1. 创建页面组件
// src/pages/NewPage.tsx
export const NewPage: React.FC = () => {
  return <div>New Page</div>;
};

// 2. 添加路由
// src/App.tsx
<Route path="/new" element={<NewPage />} />
```

### 添加新 API

```typescript
// 1. 在 api/novels.ts 中添加
export const myApi = {
  getData: async (): Promise<Data> => {
    const response = await apiClient.get('/api/data');
    return response.data;
  },
};

// 2. 创建 Hook
// hooks/useMyData.ts
export const useMyData = () => {
  return useQuery({
    queryKey: ['myData'],
    queryFn: myApi.getData,
  });
};

// 3. 在组件中使用
const { data, isLoading } = useMyData();
```

### WebSocket 订阅

```typescript
import { useWebSocketContext } from '../contexts/WebSocketContext';

const { subscribe, unsubscribe, lastMessage } = useWebSocketContext();

useEffect(() => {
  subscribe(novelId);
  return () => unsubscribe(novelId);
}, [novelId]);

useEffect(() => {
  if (lastMessage?.type === 'progress') {
    console.log(lastMessage.progress);
  }
}, [lastMessage]);
```

## 调试技巧

### React Query DevTools

```bash
npm install @tanstack/react-query-devtools
```

```typescript
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

<QueryClientProvider client={queryClient}>
  <App />
  <ReactQueryDevtools initialIsOpen={false} />
</QueryClientProvider>
```

### WebSocket 调试

打开浏览器控制台 → Network → WS 标签页，查看 WebSocket 消息。

### API 调试

检查 Network 标签页的 XHR/Fetch 请求。

## 性能优化

1. **React.memo** - 避免不必要的重渲染
2. **useMemo/useCallback** - 缓存计算和函数
3. **代码分割** - React.lazy + Suspense
4. **虚拟滚动** - 大列表优化

## 常见问题

### Q: CORS 错误？
A: 确保后端 CORS 配置正确，或者使用 proxy。

### Q: WebSocket 连接失败？
A: 检查 .env 中的 REACT_APP_WS_URL 配置。

### Q: 样式不生效？
A: 确保 Chakra UI 的 ChakraProvider 包裹整个应用。

### Q: 类型错误？
A: 检查 src/types/index.ts 中的类型定义。

## 下一步计划

1. 完成章节编辑器
2. 实现润色和评审功能
3. 添加导出功能
4. 优化移动端体验
5. 添加单元测试

---

**开发者**: Claude Code
**创建时间**: 2026-02-02
**技术栈**: React 18 + TypeScript + Chakra UI
