// API 数据类型定义

export interface Novel {
  id: string;
  title: string;
  genre: string;
  theme: string;
  style: string;
  total_chapters: number;
  completed_chapters: number;
  status: string;
  created_at: string;
  updated_at: string;
  characters?: Character[];
  plot_points?: PlotPoint[];
  chapters?: Chapter[];
}

export interface NovelSummary {
  id: string;
  title: string;
  genre: string;
  style: string;
  total_chapters: number;
  completed_chapters: number;
  status: string;
  created_at: string;
  updated_at?: string;
}

export interface Character {
  name: string;
  role: string;
  personality: string;
  background: string;
}

export interface PlotPoint {
  name: string;
  description: string;
  chapter_range: string;
  importance: string;
}

export interface Chapter {
  number: number;
  title: string;
  summary: string;
  word_count: number;
  status: string;
}

export interface ChapterContent extends Chapter {
  novel_id: string;
  content: string;
  created_at: string;
}

export interface Style {
  name: string;
  description: string;
  characteristics: string[];
  suitable_genres: string[];
}

export interface CreateNovelRequest {
  title: string;
  genre: string;
  theme: string;
  style: string;
  chapters: number;
}

export interface WebSocketMessage {
  type: string;
  novel_id?: string;
  task_type?: string;
  progress?: number;
  message?: string;
  result?: any;
  error?: string;
  timestamp?: string;
}
