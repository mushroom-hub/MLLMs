/**
 * API 配置和 HTTP 客户端
 * 与后端服务通信
 */

// API 基础 URL（通过 Vite 代理转发到后端）
const API_BASE_URL = '/api';

// API 端点
export const API_ENDPOINTS = {
  chat: {
    send: `${API_BASE_URL}/chat/send`,
    history: `${API_BASE_URL}/chat/history`,
    source: `${API_BASE_URL}/chat/source`,
    clear: `${API_BASE_URL}/chat/clear`,
  },
  subjects: `${API_BASE_URL}/subjects`,
  stats: `${API_BASE_URL}/stats`,
  health: `${API_BASE_URL}/health`,
  // 知识库管理
  knowledge: {
    upload: `${API_BASE_URL}/knowledge/upload`,
    documents: `${API_BASE_URL}/knowledge/documents`,
    clear: `${API_BASE_URL}/knowledge/clear`,
  },
};

// HTTP 请求工具
export class APIClient {
  /**
   * 发送消息
   */
  static async sendMessage(params: {
    sessionId?: string;
    message: string;
    subject: string;
    files?: File[];
  }): Promise<any> {
    const formData = new FormData();
    
    if (params.sessionId) {
      formData.append('session_id', params.sessionId);
    }
    formData.append('message', params.message);
    formData.append('subject', params.subject);
    
    if (params.files && params.files.length > 0) {
      params.files.forEach((file, index) => {
        formData.append('files', file);
        console.log(`添加文件 ${index + 1}:`, file.name, file.type);
      });
      console.log('FormData 文件数量:', formData.getAll('files').length);
    } else {
      console.log('没有文件要上传');
    }

    const response = await fetch(API_ENDPOINTS.chat.send, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`API 错误: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * 获取对话历史
   */
  static async getHistory(sessionId: string, limit?: number): Promise<any> {
    const params = new URLSearchParams({ session_id: sessionId });
    if (limit) {
      params.append('limit', limit.toString());
    }

    const response = await fetch(
      `${API_ENDPOINTS.chat.history}?${params}`,
      { method: 'GET' }
    );

    if (!response.ok) {
      throw new Error(`获取历史失败: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * 获取消息源文档
   */
  static async getMessageSource(messageId: string, sessionId: string): Promise<any> {
    const params = new URLSearchParams({ session_id: sessionId });
    
    const response = await fetch(
      `${API_ENDPOINTS.chat.source}/${messageId}?${params}`,
      { method: 'GET' }
    );

    if (!response.ok) {
      throw new Error(`获取源文档失败: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * 清空会话
   */
  static async clearSession(sessionId: string): Promise<any> {
    const response = await fetch(API_ENDPOINTS.chat.clear, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId }),
    });

    if (!response.ok) {
      throw new Error(`清空会话失败: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * 获取学科列表
   */
  static async getSubjects(): Promise<any> {
    const response = await fetch(API_ENDPOINTS.subjects, { method: 'GET' });

    if (!response.ok) {
      throw new Error(`获取学科失败: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * 获取系统统计
   */
  static async getStats(): Promise<any> {
    const response = await fetch(API_ENDPOINTS.stats, { method: 'GET' });

    if (!response.ok) {
      throw new Error(`获取统计失败: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * 健康检查
   */
  static async health(): Promise<boolean> {
    try {
      const response = await fetch(API_ENDPOINTS.health, { method: 'GET' });
      return response.ok;
    } catch {
      return false;
    }
  }
  // ================ 知识库管理 ================
  /**
   * 上传文档到指定学科的知识库
   */
  static async uploadKnowledge(params: {
    subject: string;
    files: File[];
  }): Promise<any> {
    const formData = new FormData();
    formData.append('subject', params.subject);
    params.files.forEach(file => formData.append('files', file));
    const response = await fetch(API_ENDPOINTS.knowledge.upload, {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) {
      throw new Error(`上传失败: ${response.statusText}`);
    }
    return response.json();
  }
  /**
   * 列出知识库文档
   */
  static async listKnowledge(
    subject?: string,
    limit: number = 100,
  ): Promise<any> {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (subject) {
      params.append('subject', subject);
    }
    const response = await fetch(
      `${API_ENDPOINTS.knowledge.documents}?${params}`,
      { method: 'GET' },
    );
    if (!response.ok) {
      throw new Error(`获取文档列表失败: ${response.statusText}`);
    }
    return response.json();
  }
  /**
   * 清空指定学科的知识库
   */
  static async clearKnowledge(subject: string): Promise<any> {
    const response = await fetch(API_ENDPOINTS.knowledge.clear, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ subject }),
    });
    if (!response.ok) {
      throw new Error(`清空知识库失败: ${response.statusText}`);
    }
    return response.json();
  }
}

// 导出 API 端点和客户端
export default APIClient;