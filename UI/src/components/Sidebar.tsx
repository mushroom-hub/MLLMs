import React from 'react';
import { 
  BookOpen, 
  Cpu, 
  Brain, 
  Layers, 
  History, 
  PlusCircle, 
  Database,
  FileText,
  Trash2,
} from 'lucide-react';
import { Button } from './ui/button';
import { Conversation } from '../pages/Dashboard';
import { cn } from '../lib/utils';
import { Subject } from '../pages/Dashboard';

interface SidebarProps {
  activeSubject: Subject;
  onSelectSubject: (subject: Subject) => void;
  // 对话历史相关
  conversations: Conversation[];
  activeConversationId: string | null;
  onNewConversation: () => void;
  onSelectConversation: (id: string) => void;
  onDeleteConversation: (id: string) => void;
}

const Sidebar: React.FC<SidebarProps> = ({
  activeSubject,
  onSelectSubject,
  conversations,
  activeConversationId,
  onNewConversation,
  onSelectConversation,
  onDeleteConversation,
}) => {
  // ---------------- 学科配置 ----------------
const subjects = [
  { name: '全部学科' as Subject, icon: <Database className="h-4 w-4" />, color: 'bg-slate-100 text-slate-700' },
  { name: '数据结构' as Subject, icon: <Layers className="h-4 w-4" />, color: 'bg-blue-50 text-blue-600' },
  { name: '计算机组成原理' as Subject, icon: <Cpu className="h-4 w-4" />, color: 'bg-amber-50 text-amber-600' },
  { name: '计算机网络' as Subject, icon: <Brain className="h-4 w-4" />, color: 'bg-purple-50 text-purple-600' },
  { name: '操作系统' as Subject, icon: <BookOpen className="h-4 w-4" />, color: 'bg-emerald-50 text-emerald-600' },
];
 

  // ---------- 对话卡片渲染 ---------- 对话卡片渲染（供按学科分组和单学科列表复用） ----------
  const renderConversationItem = (
    conv: Conversation,
  ) => {
    const isActive = conv.id === activeConversationId;
    const timeStr = new Date(conv.createdAt).toLocaleDateString();
    return (
      <div key={conv.id} className="group relative">
        <button
          onClick={() => onSelectConversation(conv.id)}
          className={
            'flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left transition-all ' +
            (isActive
              ? 'bg-white text-indigo-600 shadow-sm ring-1 ring-indigo-100'
              : 'text-slate-600 hover:bg-white hover:text-slate-900 hover:shadow-sm')
          }
        >
          <div className={cn('h-1.5 w-1.5 rounded-full shrink-0', isActive ? 'bg-indigo-500' : 'bg-slate-300')} />
          <div className="flex-1 min-w-0">
            <div className="truncate text-xs font-medium">
              {conv.title || '新对话'}
            </div>
            <div className="truncate text-[10px] text-slate-400">
              {timeStr} · {conv.subject} · {conv.messages.length} 条
            </div>
          </div>
        </button>
        {/* 删除按钮 - hover 出现 */}
        <button
          onClick={(e) => {
            e.stopPropagation();
            if (confirm(`删除对话「${conv.title || '新对话'}」？`)) {
              onDeleteConversation(conv.id);
            }
          }}
          className="absolute right-2 top-1/2 -translate-y-1/2 rounded p-1 opacity-0 group-hover:opacity-100 text-slate-400 hover:bg-red-50 hover:text-red-600 transition-all"
          title="删除此对话"
        >
          <Trash2 className="h-3 w-3" />
        </button>
      </div>
    );
  };

  return (
    <aside className="flex h-full w-72 flex-col border-r bg-slate-50/50 p-4">
      {/* 顶部 Logo */}
      <div className="mb-6 flex items-center justify-between px-2">
        <div className="flex items-center gap-2 font-bold text-slate-900">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 text-white shadow-lg shadow-indigo-200">
            <Brain className="h-5 w-5" />
          </div>
          <span className="text-lg">EduBrain AI</span>
        </div>
      </div>

      <Button
        className="mb-6 w-full gap-2 shadow-md shadow-indigo-100"
        size="lg"
        onClick={onNewConversation}
      >
        <PlusCircle className="h-4 w-4" />
        新对话
      </Button>

      {/* 学科分类 —— 按学科筛选对话（点击只显示该学科下的历史对话） */}
      <div className="mb-4">
        <h3 className="mb-2 px-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
          学科分类
        </h3>
        <div className="space-y-1">
          {subjects.map((s) => {
            // 该学科下的对话数（"全部学科"显示总数）
            const convCount = s.name === '全部学科'
              ? conversations.length
              : conversations.filter((c) => c.subject === s.name).length;
            const isActive = activeSubject === s.name;
            return (
              <button
                key={s.name}
                onClick={() => onSelectSubject(s.name)}
                className={cn(
                  "flex w-full items-center justify-between rounded-lg px-3 py-2 text-sm transition-all hover:bg-white hover:shadow-sm",
                  isActive ? "bg-white text-indigo-600 shadow-sm ring-1 ring-indigo-100" : "text-slate-600"
                )}
              >
                <div className="flex items-center gap-3">
                  <span className={cn("p-1.5 rounded-md", s.color)}>{s.icon}</span>
                  <span className="font-medium">{s.name}</span>
                </div>
                <span className={cn(
                  "rounded-full px-2 py-0.5 text-[10px] font-semibold",
                  convCount > 0 ? "bg-indigo-50 text-indigo-600" : "bg-slate-100 text-slate-400"
                )}>
                  {convCount}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* 按学科分组的对话列表 */}
      {/* - activeSubject === '全部学科'：按学科分组显示所有对话
          - activeSubject 为具体学科：只显示该学科下的对话 */}
      <div className="flex-1 overflow-hidden flex flex-col min-h-[100px]">
        <h3 className="mb-2 px-2 text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-2">
          <History className="h-3 w-3" />
          {activeSubject === '全部学科' ? '按学科分组对话' : `${activeSubject} · 对话`}
          <span className="ml-auto text-[10px] font-normal text-slate-400">
            {activeSubject === '全部学科'
              ? conversations.length
              : conversations.filter((c) => c.subject === activeSubject).length}
          </span>
        </h3>
        <div className="flex-1 space-y-3 overflow-y-auto pr-2 custom-scrollbar">
          {/* ===== 场景 1：选中了具体学科，只显示该学科下的对话 ===== */}
          {activeSubject !== '全部学科' && (() => {
            const list = conversations.filter((c) => c.subject === activeSubject);
            if (list.length === 0) {
              return (
                <div className="px-3 py-4 text-center text-xs text-slate-400">
                  暂无「{activeSubject}」的对话。
                </div>
              );
            }
            return (
              <div className="space-y-1">
                {list.map((conv) => renderConversationItem(conv))}
              </div>
            );
          })()}

          {/* ===== 场景 2：全部学科 —— 按学科分组显示 ===== */}
          {activeSubject === '全部学科' && (() => {
            // 用 SUBJECT_BASE 中定义的学科顺序来枚举（不含"全部学科"）
            const groups = subjects.filter((s) => s.name !== '全部学科');
            const hasAny = groups.some((s) => conversations.some((c) => c.subject === s.name));
            if (conversations.length === 0 || !hasAny) {
              return (
                <div className="px-3 py-4 text-center text-xs text-slate-400">
                  暂无对话。开始提问吧！
                </div>
              );
            }
            return groups.map((subject) => {
              const list = conversations.filter((c) => c.subject === subject.name);
              if (list.length === 0) return null;
              return (
                <div key={subject.name} className="space-y-1">
                  <div className="flex items-center gap-2 px-2 py-1">
                    <span className={cn("p-1 rounded-md", subject.color)}>{subject.icon}</span>
                    <span className="text-[11px] font-semibold text-slate-700">{subject.name}</span>
                    <span className="text-[10px] text-slate-400">{list.length} 条</span>
                  </div>
                  <div className="space-y-1 pl-2">
                    {list.map((conv) => renderConversationItem(conv))}
                  </div>
                </div>
              );
            });
          })()}
        </div>
      </div>

      {/* 底部用户信息 */}
      <div className="mt-2 border-t pt-3">
        <div className="flex items-center gap-3 rounded-xl bg-white p-3 shadow-sm border border-slate-100">
          <div className="h-10 w-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center text-white font-bold text-xs shadow-inner">
            JD
          </div>
          <div className="flex-1 overflow-hidden">
            <p className="text-sm font-semibold text-slate-900 truncate">Jane Doe</p>
            <p className="text-xs text-slate-500">专业版用户</p>
          </div>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;