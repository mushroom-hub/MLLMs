import React, { useState } from 'react';
import { 
  Bot, 
  User, 
  ChevronDown, 
  ChevronUp, 
  ExternalLink, 
  CheckCircle2,
  FileText,
  Info
} from 'lucide-react';
import { cn } from '../lib/utils';
import { Message } from './ChatInterface';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';  // KaTeX 公式渲染样式

interface MessageItemProps {
  message: Message;
  onOpenSource: () => void;
}

const MessageItem: React.FC<MessageItemProps> = ({ message, onOpenSource }) => {
  const [showReasoning, setShowReasoning] = useState(true);
  const isAI = message.role === 'ai';

  return (
    <div className={cn("flex w-full gap-4", !isAI && "flex-row-reverse")}>
      {/* 头像 */}
      <div className={cn(
        "flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-white shadow-md",
        isAI ? "bg-indigo-600" : "bg-slate-700"
      )}>
        {isAI ? <Bot className="h-6 w-6" /> : <User className="h-6 w-6" />}
      </div>

      <div className={cn("flex max-w-[85%] flex-col gap-2", !isAI && "items-end")}>
        {/* 元信息 */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm font-bold text-slate-900">
            {isAI ? 'EduBrain AI' : '您'}
          </span>
          <span className="text-[10px] text-slate-400 font-medium">{message.timestamp}</span>
          {isAI && message.subject && (
            <Badge variant="outline" className="h-5 rounded px-1.5 text-[10px] font-semibold uppercase text-indigo-500 border-indigo-200">
              {message.subject}
            </Badge>
          )}
          {/* 置信度徽标（Qwen 评估） */}
          {isAI && message.answerConfidence && typeof message.answerConfidence.score === 'number' && (
            <Badge
              className={cn(
                "h-5 rounded px-1.5 text-[10px] font-bold border-0",
                message.answerConfidence.score >= 0.8
                  ? "bg-emerald-50 text-emerald-700"
                  : message.answerConfidence.score >= 0.5
                    ? "bg-amber-50 text-amber-700"
                    : "bg-red-50 text-red-700",
              )}
              title={message.answerConfidence.summary}
            >
              置信度 {Math.round(message.answerConfidence.score * 100)}%
            </Badge>
          )}
        </div>

        {/* 消息正文 */}
        <div className={cn(
          "rounded-2xl px-5 py-4 text-sm leading-relaxed shadow-sm ring-1",
          isAI 
            ? "bg-white text-slate-800 ring-slate-200" 
            : "bg-indigo-600 text-white ring-indigo-500"
        )}>
          <div className="markdown-content">
            <ReactMarkdown
              remarkPlugins={[remarkGfm, remarkMath]}
              rehypePlugins={[rehypeKatex]}
              components={{
              p: ({ children }) => <p className="mb-3 leading-relaxed">{children}</p>,
              h1: ({ children }) => <h1 className="text-lg font-bold mb-3 mt-2 text-indigo-700">{children}</h1>,
              h2: ({ children }) => <h2 className="text-base font-bold mb-2 mt-3 text-indigo-600">{children}</h2>,
              h3: ({ children }) => <h3 className="text-sm font-bold mb-2 mt-2 text-slate-700">{children}</h3>,
              ul: ({ children }) => <ul className="list-disc list-inside mb-3 space-y-1.5 pl-2">{children}</ul>,
              ol: ({ children }) => <ol className="list-decimal list-inside mb-3 space-y-1.5 pl-2">{children}</ol>,
              li: ({ children }) => <li className="leading-relaxed">{children}</li>,
              strong: ({ children }) => <strong className="font-semibold text-slate-900">{children}</strong>,
              em: ({ children }) => <em className="italic text-slate-700">{children}</em>,
              code: ({ className, children }) => (
                <code className={cn(
                  "px-1.5 py-0.5 rounded text-xs font-mono bg-slate-100 text-slate-700",
                  className
                )}>{children}</code>
              ),
              pre: ({ children }) => (
                <pre className="my-3 p-3 rounded-lg bg-slate-50 text-slate-700 text-xs overflow-x-auto border border-slate-200">{children}</pre>
              ),
              blockquote: ({ children }) => (
                <blockquote className="my-3 pl-4 border-l-2 border-indigo-400 italic text-slate-600 bg-indigo-50/50 py-2">
                  {children}
                </blockquote>
              ),
              hr: () => <hr className="my-4 border-slate-200" />,
              a: ({ href, children }) => (
                <a href={href} className="text-indigo-600 hover:text-indigo-700 underline hover:no-underline">
                  {children}
                </a>
              ),
              table: ({ children }) => (
                <div className="my-3 overflow-x-auto rounded-lg border border-slate-200">
                  <table className="w-full text-xs">{children}</table>
                </div>
              ),
              th: ({ children }) => (
                <th className="px-3 py-2 bg-slate-100 text-left font-semibold text-slate-700 border-b">
                  {children}
                </th>
              ),
              td: ({ children }) => (
                <td className="px-3 py-2 border-b border-slate-100">{children}</td>
              ),
            }}>
              {message.content}
            </ReactMarkdown>
          </div>
          
          {/* 附件展示 */}
          {message.attachments && message.attachments.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {message.attachments.map((file, i) => (
                <div key={i} className="flex items-center gap-2 rounded-lg bg-indigo-500/10 px-3 py-1.5 ring-1 ring-white/20">
                  <FileText className="h-3 w-3 text-white" />
                  <span className="text-xs text-white">{file.name}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* AI 特有模块：推理过程与溯源 */}
        {isAI && (
          <div className="mt-2 space-y-2">
            {/* 推理过程 */}
            {message.reasoningSteps && (
              <div className="overflow-hidden rounded-xl border bg-slate-50/50">
                <button
                  onClick={() => setShowReasoning(!showReasoning)}
                  className="flex w-full items-center justify-between px-4 py-2 text-xs font-semibold text-slate-500 hover:bg-slate-100/50 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
                    <span>查看推理路径</span>
                  </div>
                  {showReasoning ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
                </button>
                <AnimatePresence>
                  {showReasoning && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="px-4 pb-3"
                    >
                      <div className="space-y-2 border-l-2 border-slate-200 ml-1.5 pl-4 pt-1">
                        {message.reasoningSteps.map((step, idx) => (
                          <div key={idx} className="relative flex items-center gap-2 text-[11px] text-slate-500">
                            <div className="absolute -left-[21px] h-2 w-2 rounded-full border-2 border-white bg-slate-300" />
                            {step}
                          </div>
                        ))}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            )}

            {/* 溯源按钮 */}
            <Button
              variant="outline"
              size="sm"
              onClick={onOpenSource}
              className="h-8 w-fit gap-2 rounded-lg bg-white px-3 text-xs font-semibold text-indigo-600 hover:bg-indigo-50 border-indigo-100"
            >
              <Info className="h-3.5 w-3.5" />
              查看知识源与置信度
              <ExternalLink className="h-3 w-3" />
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};

export default MessageItem;