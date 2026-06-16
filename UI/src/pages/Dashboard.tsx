import React, { useState, useEffect, useRef } from 'react';
import Sidebar from '../components/Sidebar';
import ChatInterface, { Message } from '../components/ChatInterface';
import SourceDetails from '../components/SourceDetails';
import { AnimatePresence, motion } from 'framer-motion';
import { Database, Upload, Trash2, Loader2, X } from 'lucide-react';
import { APIClient } from '../lib/api';

export type Subject = '数据结构' | '计算机组成原理' | '计算机网络' | '操作系统' | '全部学科';

// ===== 对话历史结构 =====
export interface Conversation {
  id: string;                     // 唯一 ID（时间戳）
  title: string;                  // 标题（用户第一条问题的前 30 字）
  subject: Subject;               // 对话所属学科
  messages: Message[];            // 对话消息
  createdAt: number;              // 创建时间
}

const STORAGE_KEY = 'edubrain_conversations_v1';

// 初始欢迎消息（每个新对话的起点）
const buildWelcomeMessage = (subject: Subject): Message => ({
  id: `welcome-${Date.now()}`,
  role: 'ai',
  content: subject === '全部学科'
    ? `您好！我是 EduBrain AI，您的专业学科知识助手。我会自动判断您的问题属于哪个学科（数据结构、计算机网络、操作系统、计算机组成原理等），并使用对应的学科知识为您解答。欢迎提问！`
    : `您好！我是 EduBrain AI，当前学科：${subject}。您可以上传文档、图片，或直接向我提问。`,
  timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
  subject,
});

const Dashboard: React.FC = () => {
  const [activeSubject, setActiveSubject] = useState<Subject>('全部学科');
  const [showSource, setShowSource] = useState(false);
  const [selectedMessageId, setSelectedMessageId] = useState<string | null>(null);

  // ===== 对话历史状态 =====
  const [conversations, setConversations] = useState<Conversation[]>(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) return JSON.parse(raw) as Conversation[];
    } catch {
      // ignore
    }
    return [];
  });
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);

  // 持久化到 localStorage
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations));
    } catch {
      // ignore quota issues
    }
  }, [conversations]);

  // ===== 操作：开始新对话 =====
  const handleNewConversation = () => {
    const conv: Conversation = {
      id: `conv-${Date.now()}`,
      title: '新对话',
      subject: activeSubject,
      messages: [buildWelcomeMessage(activeSubject)],
      createdAt: Date.now(),
    };
    setConversations((prev) => [conv, ...prev]);
    setActiveConversationId(conv.id);
  };

  // 如果没有任何对话，自动建一个初始空对话
  useEffect(() => {
    if (conversations.length === 0) {
      handleNewConversation();
    } else if (!activeConversationId) {
      setActiveConversationId(conversations[0].id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ===== 操作：切换到某条历史对话 =====
  const handleSelectConversation = (id: string) => {
    setActiveConversationId(id);
    const conv = conversations.find((c) => c.id === id);
    if (conv && conv.subject !== activeSubject) {
      setActiveSubject(conv.subject);
    }
  };

  // ===== 操作：保存一对 (userMsg, aiMsg) 到当前对话 =====
  // subjectOverride: 若后端自动识别了学科，则覆盖对话原来的学科（用于归档到正确的分组）
  const handleSaveMessagePair = (userMsg: Message, aiMsg: Message, subjectOverride?: Subject) => {
    setConversations((prev) => {
      let list = [...prev];
      const idx = list.findIndex((c) => c.id === activeConversationId);

      // 用后端识别的学科（优先）或用户当前选择的学科
      const finalSubject = subjectOverride || activeSubject;

      // 如果没有活跃对话，创建一条（兜底）
      if (idx === -1) {
        const conv: Conversation = {
          id: `conv-${Date.now()}`,
          title: (userMsg.content || '新对话').slice(0, 30),
          subject: finalSubject,
          messages: [buildWelcomeMessage(finalSubject), userMsg, aiMsg],
          createdAt: Date.now(),
        };
        setActiveConversationId(conv.id);
        return [conv, ...list];
      }

      // 更新现有对话：追加消息 + 用第一条用户消息做标题
      const current = { ...list[idx] };
      current.messages = [...current.messages, userMsg, aiMsg];
      if (current.title === '新对话' || current.title === '') {
        current.title = (userMsg.content || '新对话').slice(0, 30);
      }
      current.subject = finalSubject;  // 归档到后端识别的学科分组
      // 把更新后的对话移到最前面（最近活跃）
      list.splice(idx, 1);
      list = [current, ...list];
      return list;
    });
  };

  // ===== 操作：后端自动识别到了学科 → 切换 Sidebar 活跃学科分组 =====
  const handleSubjectChanged = (subject: Subject) => {
    setActiveSubject(subject);
  };

  // ===== 操作：删除单条历史对话 =====
  const handleDeleteConversation = (id: string) => {
    setConversations((prev) => prev.filter((c) => c.id !== id));
    if (activeConversationId === id) {
      const remaining = conversations.filter((c) => c.id !== id);
      setActiveConversationId(remaining.length > 0 ? remaining[0].id : null);
    }
  };

  // ============= 知识库管理面板 =============
  const [showKnowledgePanel, setShowKnowledgePanel] = useState(false);
  const [knowledgeSubject, setKnowledgeSubject] = useState<string>('全部学科');
  const [knowledgeDocs, setKnowledgeDocs] = useState<any[]>([]);
  const [knowledgeLoading, setKnowledgeLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadKnowledgeDocs = async (subject?: string) => {
    setKnowledgeLoading(true);
    try {
      const res = await APIClient.listKnowledge(
        subject && subject !== '全部学科' ? subject : undefined,
        200,
      );
      setKnowledgeDocs(res.documents || []);
    } catch (e: any) {
      console.error('加载知识库失败:', e);
      setKnowledgeDocs([]);
    } finally {
      setKnowledgeLoading(false);
    }
  };

  // 打开面板时刷新
  useEffect(() => {
    if (showKnowledgePanel) {
      loadKnowledgeDocs(knowledgeSubject);
    }
  }, [showKnowledgePanel, knowledgeSubject]);

  const handleSelectFiles = () => fileInputRef.current?.click();

  const handleFilesChosen = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length === 0) return;
    setUploading(true);
    setUploadMsg(null);
    try {
      const res = await APIClient.uploadKnowledge({ subject: knowledgeSubject, files });
      setUploadMsg(`✓ ${res.message}`);
      loadKnowledgeDocs(knowledgeSubject);
    } catch (err: any) {
      setUploadMsg(`✗ ${err.message || '上传失败'}`);
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleClearKnowledge = async () => {
    if (!confirm(`确定要清空 "${knowledgeSubject}" 的所有知识库内容吗？此操作不可恢复。`)) return;
    try {
      await APIClient.clearKnowledge(knowledgeSubject);
      setUploadMsg(`✓ 已清空 ${knowledgeSubject} 知识库`);
      loadKnowledgeDocs(knowledgeSubject);
    } catch (err: any) {
      setUploadMsg(`✗ ${err.message || '清空失败'}`);
    }
  };

  // 取得当前活跃对话
  const activeConversation = conversations.find((c) => c.id === activeConversationId) || null;

  const handleOpenSource = (messageId: string) => {
    setSelectedMessageId(messageId);
    setShowSource(true);
  };

  // ========== 溯源与置信度：根据 messageId 取出消息对象 ==========
  const sourceMessage = (() => {
    if (!selectedMessageId || !activeConversation) return null;
    // activeConversation.messages 是 ChatInterface 的 Message[]
    const found = (activeConversation as { messages?: Array<{ id?: string }> }).messages?.find(
      (m) => (m as { id?: string }).id === selectedMessageId
    );
    return found as any || null;
  })();

  return (
    <div className="flex h-screen w-full overflow-hidden bg-white">
      {/* 侧边栏 */}
      <Sidebar
        activeSubject={activeSubject}
        onSelectSubject={setActiveSubject}
        conversations={conversations}
        activeConversationId={activeConversationId}
        onNewConversation={handleNewConversation}
        onSelectConversation={handleSelectConversation}
        onDeleteConversation={handleDeleteConversation}
      />

      {/* 主对话区 */}
      <main className="relative flex flex-1 flex-col overflow-hidden bg-slate-50/50">
        <ChatInterface
          activeSubject={activeSubject}
          onOpenSource={handleOpenSource}
          conversation={activeConversation}
          onSaveMessagePair={handleSaveMessagePair}
          onNewConversation={handleNewConversation}
          onSubjectChanged={handleSubjectChanged}
          onOpenKnowledgeBase={() => setShowKnowledgePanel(true)}
        />
      </main>

      {/* 溯源详情侧拉面板 */}
      <AnimatePresence>
        {showSource && (
          <motion.aside
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="absolute right-0 top-0 z-50 h-full w-[400px] border-l bg-white shadow-2xl md:relative"
          >
            <SourceDetails
              messageId={selectedMessageId}
              message={sourceMessage}
              onClose={() => setShowSource(false)}
            />
          </motion.aside>
        )}
      </AnimatePresence>

      {/* ===== 知识库管理面板 ===== */}
      <AnimatePresence>
        {showKnowledgePanel && (
          <motion.aside
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="absolute right-0 top-0 z-50 h-full w-[440px] border-l bg-white shadow-2xl"
          >
            <div className="flex h-full flex-col">
              {/* 面板头部 */}
              <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
                <div className="flex items-center gap-2">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-50">
                    <Database className="h-4 w-4 text-indigo-600" />
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-slate-900">知识库管理</h2>
                    <p className="text-[11px] text-slate-500">上传文档让 AI 基于知识库回答</p>
                  </div>
                </div>
                <button
                  onClick={() => setShowKnowledgePanel(false)}
                  className="rounded-lg p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-colors"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              {/* 操作区 */}
              <div className="border-b border-slate-200 p-5 space-y-4">
                {/* 目标学科 */}
                <div>
                  <label className="mb-1.5 block text-xs font-semibold text-slate-700">目标学科</label>
                  <select
                    value={knowledgeSubject}
                    onChange={(e) => setKnowledgeSubject(e.target.value)}
                    className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  >
                    <option value="全部学科">全部学科</option>
                    <option value="数据结构">数据结构</option>
                    <option value="计算机组成原理">计算机组成原理</option>
                    <option value="计算机网络">计算机网络</option>
                    <option value="操作系统">操作系统</option>
                  </select>
                </div>

                {/* 上传/清空按钮 */}
                <div className="flex gap-2">
                  <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    accept=".pdf,.txt,.md"
                    onChange={handleFilesChosen}
                    className="hidden"
                  />
                  <button
                    onClick={handleSelectFiles}
                    disabled={uploading}
                    className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50 transition-colors shadow-sm"
                  >
                    {uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
                    {uploading ? '上传中...' : '上传文档'}
                  </button>
                  <button
                    onClick={handleClearKnowledge}
                    className="flex items-center justify-center gap-2 rounded-lg border border-red-200 bg-white px-4 py-2.5 text-sm font-medium text-red-600 hover:bg-red-50 transition-colors"
                    title="清空该学科的知识库"
                  >
                    <Trash2 className="h-4 w-4" />
                    清空
                  </button>
                </div>

                {/* 消息提示 */}
                {uploadMsg && (
                  <div className={`rounded-lg px-3 py-2 text-xs font-medium ${
                    uploadMsg.startsWith('✓')
                      ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                      : 'bg-red-50 text-red-700 border border-red-200'
                  }`}>
                    {uploadMsg}
                  </div>
                )}
              </div>

              {/* 文档列表 */}
              <div className="flex-1 overflow-hidden flex flex-col">
                <div className="flex items-center justify-between px-5 py-3 border-b border-slate-100 bg-slate-50/50">
                  <span className="text-sm font-semibold text-slate-700">
                    文档列表 · {knowledgeDocs.length} 条
                  </span>
                  {knowledgeLoading && <Loader2 className="h-3.5 w-3.5 animate-spin text-slate-400" />}
                </div>
                <div className="flex-1 overflow-y-auto">
                  {knowledgeDocs.length === 0 && !knowledgeLoading && (
                    <div className="px-5 py-16 text-center">
                      <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-slate-100">
                        <Database className="h-6 w-6 text-slate-400" />
                      </div>
                      <p className="text-sm text-slate-500">暂无文档</p>
                      <p className="mt-1 text-xs text-slate-400">上传 PDF / TXT / MD 文件，AI 会基于它们回答问题</p>
                    </div>
                  )}
                  {knowledgeDocs.slice(0, 50).map((doc: any, i: number) => (
                    <div
                      key={i}
                      className="mx-5 my-2 flex items-start gap-3 rounded-lg px-3 py-2.5 hover:bg-slate-50 transition-colors"
                    >
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-indigo-50">
                        <Database className="h-4 w-4 text-indigo-500" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="truncate text-sm font-medium text-slate-800">
                            {doc.source || '未命名文档'}
                          </span>
                          {doc.page && <span className="text-[11px] text-slate-400 shrink-0">第 {doc.page} 页</span>}
                        </div>
                        <p className="mt-0.5 truncate text-xs text-slate-500">{doc.preview || ''}</p>
                      </div>
                      <span className="text-[10px] text-indigo-600 font-medium shrink-0 bg-indigo-50 px-2 py-1 rounded">
                        {doc.subject}
                      </span>
                    </div>
                  ))}
                  {knowledgeDocs.length > 50 && (
                    <div className="px-5 py-3 text-center text-xs text-slate-400">
                      ...还有 {knowledgeDocs.length - 50} 条记录
                    </div>
                  )}
                </div>
              </div>
            </div>
          </motion.aside>
        )}
      </AnimatePresence>
    </div>
  );
};

export default Dashboard;