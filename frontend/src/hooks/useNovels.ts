import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { novelsApi, chaptersApi, stylesApi } from '../api/novels';
import { CreateNovelRequest } from '../types';

// 获取所有小说
export const useNovels = () => {
  return useQuery({
    queryKey: ['novels'],
    queryFn: novelsApi.getAll,
    refetchInterval: 5000, // 每5秒自动刷新
  });
};

// 获取小说详情
export const useNovel = (id: string) => {
  return useQuery({
    queryKey: ['novel', id],
    queryFn: () => novelsApi.getById(id),
    enabled: !!id,
  });
};

// 创建小说
export const useCreateNovel = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateNovelRequest) => novelsApi.create(data),
    onSuccess: () => {
      // 创建成功后刷新列表
      queryClient.invalidateQueries({ queryKey: ['novels'] });
    },
  });
};

// 删除小说
export const useDeleteNovel = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => novelsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['novels'] });
    },
  });
};

// 获取章节内容
export const useChapter = (novelId: string, chapterNumber: number) => {
  return useQuery({
    queryKey: ['chapter', novelId, chapterNumber],
    queryFn: () => chaptersApi.getChapter(novelId, chapterNumber),
    enabled: !!novelId && chapterNumber > 0,
  });
};

// 写作章节
export const useWriteChapter = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ novelId, chapterNumber }: { novelId: string; chapterNumber: number }) =>
      chaptersApi.writeChapter(novelId, chapterNumber),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['novel', variables.novelId] });
      queryClient.invalidateQueries({ queryKey: ['chapter', variables.novelId, variables.chapterNumber] });
    },
  });
};

// 润色章节
export const usePolishChapter = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ novelId, chapterNumber, focus }: { novelId: string; chapterNumber: number; focus?: string }) =>
      chaptersApi.polishChapter(novelId, chapterNumber, focus),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['chapter', variables.novelId, variables.chapterNumber] });
    },
  });
};

// 评审章节
export const useReviewChapter = () => {
  return useMutation({
    mutationFn: ({ novelId, chapterNumber }: { novelId: string; chapterNumber: number }) =>
      chaptersApi.reviewChapter(novelId, chapterNumber),
  });
};

// 获取所有风格
export const useStyles = () => {
  return useQuery({
    queryKey: ['styles'],
    queryFn: stylesApi.getAll,
    staleTime: Infinity, // 风格数据不会变化
  });
};
