import React from 'react';
import { 
  X, 
  ExternalLink, 
  BookMarked, 
  FileText, 
  ShieldCheck,
  TrendingUp,
  Hash,
  AlertCircle
} from 'lucide-react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { ScrollArea } from './ui/scroll-area';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';

// 松散类型：从 Dashboard 传进来的 message 对象，里面带 answerConfidence + knowledgeSources
interface SourceDetailsProps {
  messageId: string | null;
  message: any;  // 包含 answerConfidence、knowledgeSources
  onClose: () => void;
}

const SourceDetails: React.FC<SourceDetailsProps> = ({ message, onClose }) => {
  // === 从真实消息中提取数据 ===
  // 置信度（Qwen 评估）
  const confidence = message?.answerConfidence;
  const confidenceScore: number = typeof confidence?.score === 'number' ? confidence.score : 0;
  const confidencePct = Math.round(confidenceScore * 100);
  const confidenceLevel: string = confidence?.level || '';
  const confidenceSummary: string = confidence?.summary || '';

  // 知识源列表（RAG 检索）
  const knowledgeSources: Array<{
    id?: string;
    title?: string;
    source?: string;
    page?: number;
    relevance?: number;
    excerpt?: string;
    subject?: string;
    similarity?: number;
  }> = message?.knowledgeSources || [];

  const hasData = (knowledgeSources && knowledgeSources.length > 0) || (confidence && confidenceScore > 0);

  return (
    <div className="flex h-full flex-col bg-white">
      {/* 头部 */}
      <div className="flex h-16 items-center justify-between border-b px-6">
        <div className="flex items-center gap-2">
          <BookMarked className="h-5 w-5 text-indigo-600" />
          <h3 className="font-bold text-slate-900">知识源与置信度</h3>
        </div>
        <Button variant="ghost" size="icon" onClick={onClose} className="h-8 w-8 rounded-full">
          <X className="h-4 w-4" />
        </Button>
      </div>

      <ScrollArea className="flex-1 p-6">
        <div className="space-y-6">

          {/* ======= 置信度评分（Qwen 评估） ======= */}
          <div className="rounded-2xl bg-indigo-600 p-6 text-white shadow-lg shadow-indigo-100">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-indigo-100 opacity-80 uppercase tracking-widest">
                  {hasData ? 'Qwen 置信度评估' : '未获取评分'}
                </p>
                <h4 className="mt-1 text-3xl font-black">
                  {hasData ? `${confidencePct}%` : '—'}
                </h4>
                {confidenceLevel && (
                  <p className="mt-1 text-xs font-bold text-indigo-100">
                    等级：{confidenceLevel}
                  </p>
                )}
              </div>
              <ShieldCheck className="h-10 w-10 text-white opacity-40" />
            </div>
            <div className="mt-4 h-1.5 w-full rounded-full bg-white/20 overflow-hidden">
              <div
                className="h-full bg-white transition-all duration-500"
                style={{ width: hasData ? `${confidencePct}%` : '0%' }}
              />
            </div>
            <p className="mt-3 text-[11px] text-indigo-100/80 leading-relaxed">
              {confidenceSummary
                ? confidenceSummary
                : '尚未获取到模型对本次回答的置信度评估。'}
            </p>
          </div>

          {/* ======= 知识源列表（RAG 检索） ======= */}
          <div className="space-y-4">
            <h4 className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-400">
              <Hash className="h-3 w-3" />
              检索来源 (RAG Context) · 共 {knowledgeSources.length} 条
            </h4>

            {knowledgeSources.length === 0 ? (
              <div className="rounded-xl border border-dashed border-slate-200 p-6 text-center">
                <AlertCircle className="mx-auto mb-2 h-6 w-6 text-slate-400" />
                <p className="text-xs text-slate-500">本回答未匹配到知识库中的文档。</p>
                <p className="mt-1 text-[10px] text-slate-400">内容可能完全由大模型通用知识生成。</p>
              </div>
            ) : (
              knowledgeSources.map((source) => (
                <Card
                  key={source.id || source.title || Math.random()}
                  className="overflow-hidden border-slate-100 shadow-sm transition-hover hover:border-indigo-200"
                >
                  <CardHeader className="bg-slate-50/50 p-4">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <div className="flex h-7 w-7 items-center justify-center rounded bg-white shadow-sm ring-1 ring-slate-200">
                          <FileText className="h-4 w-4 text-indigo-600" />
                        </div>
                        <div className="min-w-0">
                          <CardTitle className="text-sm font-bold text-slate-900 truncate">
                            {source.title || source.source || '未命中文档'}
                          </CardTitle>
                          <p className="text-[10px] text-slate-500 truncate">
                            {source.source && source.source !== source.title
                              ? `来源：${source.source}`
                              : source.subject
                                ? `学科：${source.subject}`
                                : ''}
                          </p>
                        </div>
                      </div>
                      <Badge
                        variant="outline"
                        className={
                          'h-5 shrink-0 bg-white gap-1 text-[10px] font-bold border ' +
                          ((source.relevance ?? 0) >= 80
                            ? 'text-emerald-600 border-emerald-100'
                            : (source.relevance ?? 0) >= 50
                              ? 'text-amber-600 border-amber-100'
                              : 'text-slate-500 border-slate-200')
                        }
                      >
                        <TrendingUp className="h-3 w-3" />
                        {source.relevance ?? 0}% 相关
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="p-4 pt-2">
                    {source.excerpt ? (
                      <p className="text-xs italic leading-relaxed text-slate-600">
                        "{source.excerpt}"
                      </p>
                    ) : (
                      <p className="text-xs text-slate-400">（该匹配无摘要）</p>
                    )}
                    <div className="mt-4 flex items-center justify-between border-t border-slate-50 pt-3">
                      <span className="text-[10px] font-semibold text-slate-400">
                        {typeof source.page === 'number' && !Number.isNaN(source.page)
                          ? `第 ${source.page} 页`
                          : typeof source.similarity === 'number'
                            ? `相似度 ${(source.similarity * 100).toFixed(1)}%`
                            : '未知位置'}
                      </span>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 gap-1 px-2 text-[10px] font-bold text-indigo-600"
                        disabled={!source.source}
                        onClick={() => {
                          if (source.source) {
                            alert(`来源：${source.source}`);
                          }
                        }}
                      >
                        查看来源
                        <ExternalLink className="h-3 w-3" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>

          {/* ======= 系统元数据 ======= */}
          <div className="rounded-xl border border-dashed border-slate-200 p-4">
            <h4 className="mb-2 text-[10px] font-bold uppercase tracking-wider text-slate-400">
              处理详情
            </h4>
            <div className="grid grid-cols-2 gap-4 text-xs">
              <div>
                <p className="text-[10px] text-slate-400">模型</p>
                <p className="font-bold text-slate-700 font-mono">Qwen 系列</p>
              </div>
              <div>
                <p className="text-[10px] text-slate-400">匹配文档</p>
                <p className="font-bold text-slate-700 font-mono">{knowledgeSources.length} 篇</p>
              </div>
              <div>
                <p className="text-[10px] text-slate-400">置信度评估</p>
                <p className="font-bold text-slate-700 font-mono">
                  {hasData ? `${confidencePct}% / ${confidenceLevel || '—'}` : '未评估'}
                </p>
              </div>
              <div>
                <p className="text-[10px] text-slate-400">消息 ID</p>
                <p className="font-bold text-slate-700 font-mono truncate">
                  {message?.id?.toString().slice(-8) || '—'}
                </p>
              </div>
            </div>
          </div>
        </div>
      </ScrollArea>
    </div>
  );
};

export default SourceDetails;