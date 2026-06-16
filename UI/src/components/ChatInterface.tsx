import React, { useState, useEffect, useRef } from 'react';
import { 
  Sparkles, 
  Send, 
  Paperclip, 
  Image as ImageIcon, 
  FileText,
  PlusCircle,
  MoreVertical,
  Database,
  ChevronDown
} from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { ScrollArea } from './ui/scroll-area';
import MessageItem from './MessageItem';
import InputArea from './InputArea';
import { Subject } from '../pages/Dashboard';
import { APIClient } from '../lib/api';

interface ChatInterfaceProps {
  activeSubject: Subject;
  onOpenSource: (messageId: string) => void;
  // 外部 conversation：若提供，则用它的 messages 作为当前对话内容
  conversation?: { id: string; title: string; subject: Subject; messages: Message[]; createdAt: number } | null;
  // 完成一次问答（userMsg + aiMsg）时回调，第三个参数是后端识别到的学科
  onSaveMessagePair?: (userMsg: Message, aiMsg: Message, subjectOverride?: Subject) => void;
  // 点击"新对话"按钮
  onNewConversation?: () => void;
  // 后端自动识别到学科后，通知父组件切换 Sidebar 活跃学科
  onSubjectChanged?: (subject: Subject) => void;
  // 打开知识库管理面板
  onOpenKnowledgeBase?: () => void;
};  // 打开知识库管理面板


export interface KnowledgeSource {
  id: string;
  title: string;
  source: string;
  page?: number;
  subject?: string;
  relevance: number;
  excerpt?: string;
  similarity?: number;
}

export interface AnswerConfidence {
  score: number;        // 0.0 - 1.0
  level: string;        // "高" / "中" / "低"
  summary: string;      // 中文一句话说明评分理由
}

export interface Message {
  id: string;
  role: 'user' | 'ai';
  content: string;
  timestamp: string;
  subject?: Subject;
  reasoningSteps?: string[];
  attachments?: { name: string; type: string }[];
  // 新增：Qwen 评估的回答置信度、RAG 检索的知识源（仅 AI 消息有）
  answerConfidence?: AnswerConfidence;
  knowledgeSources?: KnowledgeSource[];
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({
  activeSubject,
  onOpenSource,
  conversation,
  onSaveMessagePair,
  onNewConversation,
  onSubjectChanged,
  onOpenKnowledgeBase,
}) => {
  // 本地缓存：等待 AI 回复的临时消息（用户已发但 AI 还没回的时候）
  // 真正写入历史的消息由父组件管理（conversation.messages），这里只存"正在等回复"的消息。
  const [pendingMessages, setPendingMessages] = useState<Message[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);

  // 最终展示的消息 = 历史对话 + 本次待回复的消息
  const messages: Message[] = conversation
    ? [...conversation.messages, ...pendingMessages]
    : pendingMessages;

  useEffect(() => {
    // 消息变化时自动滚到底部
    if (scrollRef.current) {
      requestAnimationFrame(() => {
        scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
      });
    }
  }, [messages.length, conversation?.id]);

  // 切换对话时，清空临时缓存
  useEffect(() => {
    setPendingMessages([]);
  }, [conversation?.id]);

  const handleSendMessage = async (text: string, files: any[]) => {
    if (!text.trim() && files.length === 0) return;

    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const userMsg: Message = {
      id: `u-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: now,
      subject: activeSubject,
      attachments: files.map((f) => ({ name: f.name, type: f.type })),
    };

    // 1) 先把用户消息展示出来（放到 pending，给 UI 即时反馈）
    setPendingMessages((prev) => [...prev, userMsg]);

    // 2) 调用后端拿 AI 回复 —— subject 固定为"全部学科"（让后端自动识别）
    try {
      const response = await APIClient.sendMessage({
        message: text,
        subject: '全部学科',
        files: files,
      });

      // 用后端返回的 detected_subject 作为本条对话的学科
      const detected = response?.detected_subject;
      const detectedSubject: Subject = detected && detected !== '全部学科'
        ? (detected as Subject)
        : activeSubject;

      const aiMsg: Message = {
        id: `a-${Date.now()}`,
        role: 'ai',
        content: response.ai_message?.content || '获取回复失败',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        subject: detectedSubject,
        reasoningSteps: response.ai_message?.reasoning_steps || [],
        // 新增：后端返回的 Qwen 评估置信度 + RAG 知识源
        answerConfidence: response.answer_confidence ?? response.ai_message?.answer_confidence,
        knowledgeSources: response.knowledge_sources ?? response.ai_message?.knowledge_sources,
      };

      // 3) 如果后端自动识别了学科，通知父组件（Sidebar 会高亮对应学科分组）
      if (detected && detected !== activeSubject && detected !== '全部学科') {
        console.log('[ChatInterface] 自动切换学科:', detected);
        onSubjectChanged?.(detected as Subject);
      }

      // 4) 把 userMsg + aiMsg 写入历史 —— subjectOverride 用于在父组件中把对话归档到对应学科
      const subjectOverride: Subject | undefined = detected && detected !== '全部学科'
        ? (detected as Subject)
        : undefined;
      setPendingMessages([]);
      onSaveMessagePair?.(userMsg, aiMsg, subjectOverride);
    } catch (error) {
      // 出错也写入一条错误消息
      const errorMsg: Message = {
        id: `a-${Date.now()}`,
        role: 'ai',
        content: `发送消息失败: ${error instanceof Error ? error.message : '未知错误'}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        subject: activeSubject,
      };
      setPendingMessages([]);
      onSaveMessagePair?.(userMsg, errorMsg);
    }
  };

  return (
    <div className="flex h-full flex-col">
      {/* 顶部标题栏 */}
      <header className="flex h-16 items-center justify-between border-b bg-white px-6 shadow-sm">
        <div className="flex items-center gap-4 min-w-0">
          <div className="flex items-center gap-2 min-w-0">
            <Sparkles className="h-5 w-5 text-indigo-600 shrink-0" />
            <div className="min-w-0">
              <h2 className="text-base font-bold text-slate-900 truncate max-w-[420px]">
                {conversation?.title || '新对话'}
              </h2>
              <p className="text-[11px] text-slate-400">{conversation?.subject || activeSubject} · {conversation?.messages.length || 0} 条消息</p>
            </div>
          </div>
          <div className="h-4 w-[1px] bg-slate-200" />
          <Badge variant="secondary" className="bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border-none">
            Qwen + RAG
          </Badge>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <Button variant="default" size="sm" onClick={onOpenKnowledgeBase} className="gap-1.5">
            <Database className="h-3.5 w-3.5" />
            知识库管理
          </Button>
          <Button variant="ghost" size="icon" className="h-8 w-8">
            <MoreVertical className="h-4 w-4" />
          </Button>
        </div>
      </header>

      {/* 消息滚动区 */}
      <ScrollArea className="flex-1 p-6">
        <div className="mx-auto max-w-4xl space-y-8 pb-32">
          {messages.map((msg) => (
            <MessageItem 
              key={msg.id} 
              message={msg} 
              onOpenSource={() => onOpenSource(msg.id)} 
            />
          ))}
          <div ref={scrollRef} />
        </div>
      </ScrollArea>

      {/* 底部输入区 */}
      <div className="border-t bg-white p-6 shadow-[0_-4px_12px_rgba(0,0,0,0.02)]">
        <div className="mx-auto max-w-4xl">
          <InputArea onSend={handleSendMessage} />
          <p className="mt-3 text-center text-[10px] text-slate-400">
            AI 助手可能产生偏见，请针对关键学术决策核对原文。基于 EduBrain 2026 核心引擎。
          </p>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;

function onSubjectChanged(subjectFromAI: string) {
  throw new Error('Function not implemented.');
}