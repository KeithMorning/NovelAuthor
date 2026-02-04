import React from 'react';
import { ChakraProvider, Box } from '@chakra-ui/react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { WebSocketProvider } from './contexts/WebSocketContext';
import { HomePage } from './pages/HomePage';
import { NovelDetailPage } from './pages/NovelDetailPage';
import { ChapterPage } from './pages/ChapterPage';
import theme from './theme';

// 创建 QueryClient 实例
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ChakraProvider theme={theme}>
        <WebSocketProvider>
          <Router>
            <Box minH="100vh" bg="gray.50" _dark={{ bg: 'gray.900' }}>
              <Routes>
                <Route path="/" element={<HomePage />} />
                <Route path="/novel/:id" element={<NovelDetailPage />} />
                <Route path="/novel/:novelId/chapter/:chapterNumber" element={<ChapterPage />} />
              </Routes>
            </Box>
          </Router>
        </WebSocketProvider>
      </ChakraProvider>
    </QueryClientProvider>
  );
}

export default App;
