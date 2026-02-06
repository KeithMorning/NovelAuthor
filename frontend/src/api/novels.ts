import apiClient from './client';
import { Novel, NovelSummary, CreateNovelRequest, ChapterContent } from '../types';

// 小说相关 API
export const novelsApi = {
  // 获取所有小说
  getAll: async (): Promise<NovelSummary[]> => {
    const response = await apiClient.get('/api/novels/');
    return response.data;
  },

  // 获取小说详情
  getById: async (id: string): Promise<Novel> => {
    const response = await apiClient.get(`/api/novels/${id}`);
    return response.data;
  },

  // 创建新小说
  create: async (data: CreateNovelRequest): Promise<{ success: boolean; message: string; data?: { novel_id: string } }> => {
    const response = await apiClient.post('/api/novels/', data);
    return response.data;
  },

  // 删除小说
  delete: async (id: string): Promise<{ success: boolean; message: string }> => {
    const response = await apiClient.delete(`/api/novels/${id}`);
    return response.data;
  },

  // 导出小说
  export: async (id: string, format: 'txt' | 'json' = 'txt'): Promise<any> => {
    const response = await apiClient.get(`/api/novels/${id}/export`, {
      params: { format },
    });
    return response.data;
  },
};

// 章节相关 API
export const chaptersApi = {
  // 获取章节内容
  getChapter: async (novelId: string, chapterNumber: number): Promise<ChapterContent> => {
    const response = await apiClient.get(`/api/chapters/${novelId}/${chapterNumber}`);
    return response.data;
  },

  // 写作章节
  writeChapter: async (novelId: string, chapterNumber: number): Promise<{ success: boolean; message: string }> => {
    const response = await apiClient.post('/api/chapters/write', {
      novel_id: novelId,
      chapter_number: chapterNumber,
    });
    return response.data;
  },

  // 润色章节
  polishChapter: async (novelId: string, chapterNumber: number, focus?: string): Promise<{ success: boolean; message: string }> => {
    const response = await apiClient.post('/api/chapters/polish', {
      novel_id: novelId,
      chapter_number: chapterNumber,
      focus,
    });
    return response.data;
  },

  // 评审章节
  reviewChapter: async (novelId: string, chapterNumber: number): Promise<any> => {
    const response = await apiClient.post('/api/chapters/review', {
      novel_id: novelId,
      chapter_number: chapterNumber,
    });
    return response.data;
  },
};

// 风格相关 API
export const stylesApi = {
  // 获取所有风格
  getAll: async (): Promise<any[]> => {
    const response = await apiClient.get('/api/styles/');
    return response.data;
  },

  // 获取风格详情
  getByName: async (name: string): Promise<any> => {
    const response = await apiClient.get(`/api/styles/${name}`);
    return response.data;
  },

  // 推荐风格
  recommend: async (genre: string): Promise<string[]> => {
    const response = await apiClient.get(`/api/styles/recommend/${genre}`);
    return response.data;
  },
};
