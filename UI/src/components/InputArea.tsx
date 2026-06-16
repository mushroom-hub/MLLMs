import React, { useState, useRef } from 'react';
import { 
  Paperclip, 
  Image as ImageIcon, 
  Send, 
  X, 
  Mic,
  Smile
} from 'lucide-react';
import { Button } from './ui/button';
import { cn } from '../lib/utils';

interface InputAreaProps {
  onSend: (text: string, files: any[]) => void;
}

const InputArea: React.FC<InputAreaProps> = ({ onSend }) => {
  const [inputText, setInputText] = useState('');
  const [attachedFiles, setAttachedFiles] = useState<File[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const newFiles = Array.from(e.target.files);
      setAttachedFiles(prev => [...prev, ...newFiles]);
    }
  };

  const removeFile = (index: number) => {
    setAttachedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleSend = () => {
    if (inputText.trim() || attachedFiles.length > 0) {
      onSend(inputText, attachedFiles);
      setInputText('');
      setAttachedFiles([]);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col gap-3">
      {/* 待上传文件预览 */}
      {attachedFiles.length > 0 && (
        <div className="flex flex-wrap gap-2 px-1">
          {attachedFiles.map((file, i) => (
            <div key={i} className="group relative flex items-center gap-2 rounded-lg bg-slate-100 px-3 py-1.5 ring-1 ring-slate-200">
              <span className="text-xs font-medium text-slate-700 truncate max-w-[150px]">{file.name}</span>
              <button 
                onClick={() => removeFile(i)}
                className="h-4 w-4 rounded-full bg-slate-200 p-0.5 text-slate-500 hover:bg-rose-100 hover:text-rose-600 transition-colors"
              >
                <X className="h-full w-full" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* 输入框容器 */}
      <div className="relative flex items-end gap-2 rounded-2xl border border-slate-200 bg-slate-50/50 p-2 shadow-sm transition-all focus-within:border-indigo-500/50 focus-within:ring-4 focus-within:ring-indigo-500/5 focus-within:bg-white">
        {/* 工具栏 */}
        <div className="flex flex-col gap-1 pb-1">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            multiple
            className="hidden"
          />
          <input
            type="file"
            ref={imageInputRef}
            onChange={handleFileChange}
            multiple
            accept="image/*"
            className="hidden"
          />
          <Button 
            variant="ghost" 
            size="icon" 
            className="h-9 w-9 rounded-xl text-slate-500 hover:bg-white hover:text-indigo-600"
            onClick={() => fileInputRef.current?.click()}
            title="上传文件"
          >
            <Paperclip className="h-5 w-5" />
          </Button>
          <Button 
            variant="ghost" 
            size="icon" 
            className="h-9 w-9 rounded-xl text-slate-500 hover:bg-white hover:text-indigo-600"
            onClick={() => imageInputRef.current?.click()}
            title="上传图片"
          >
            <ImageIcon className="h-5 w-5" />
          </Button>
        </div>

        {/* 文本区域 */}
        <textarea
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="提问或描述您的学术需求..."
          className="flex-1 resize-none bg-transparent px-2 py-3 text-sm outline-none placeholder:text-slate-400 min-h-[48px] max-h-[200px]"
          rows={1}
        />

        {/* 右侧动作 */}
        <div className="flex gap-1 pb-1">
           <Button 
            variant="ghost" 
            size="icon" 
            className="h-9 w-9 rounded-xl text-slate-400 hover:text-slate-600"
          >
            <Mic className="h-5 w-5" />
          </Button>
          <Button 
            onClick={handleSend}
            disabled={!inputText.trim() && attachedFiles.length === 0}
            className={cn(
              "h-9 w-9 rounded-xl shadow-lg transition-all",
              inputText.trim() || attachedFiles.length > 0
                ? "bg-indigo-600 text-white shadow-indigo-200"
                : "bg-slate-200 text-slate-400 shadow-none pointer-events-none"
            )}
            size="icon"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
};

export default InputArea;