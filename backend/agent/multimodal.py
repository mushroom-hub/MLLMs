"""
多模态输入处理模块
支持 PDF、图片、代码等多种格式
"""
import logging
import os
from typing import List, Dict, Optional
from pathlib import Path
import base64
import fitz  # PyMuPDF
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)


class MultimodalProcessor:
    """多模态内容处理器"""
    
    def __init__(self):
        """初始化处理器"""
        self.supported_image_formats = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}
        self.supported_doc_formats = {'.pdf'}
        self.supported_code_formats = {'.py', '.java', '.cpp', '.js', '.ts', '.html', '.css'}
    
    def process_pdf(self, pdf_path: str, max_pages: int = None) -> List[Dict]:
        """
        处理 PDF 文件
        
        Args:
            pdf_path: PDF 文件路径
            max_pages: 最多处理的页数
            
        Returns:
            文档列表
        """
        try:
            documents = []
            logger.info(f"处理 PDF 文件: {pdf_path}")
            
            pdf_document = fitz.open(pdf_path)
            
            for page_idx, page in enumerate(pdf_document):
                if max_pages and page_idx >= max_pages:
                    break
                
                # 提取文本
                text = page.get_text()
                
                # 提取元数据
                metadata = {
                    'source': os.path.basename(pdf_path),
                    'page': page_idx + 1,
                    'type': 'pdf'
                }
                
                documents.append({
                    'text': text,
                    'metadata': metadata
                })
            
            pdf_document.close()
            logger.info(f"PDF 处理完成，共提取 {len(documents)} 页")
            return documents
        except Exception as e:
            logger.error(f"PDF 处理失败: {e}")
            return []
    
    def process_image(self, image_path: str) -> Optional[Dict]:
        """
        处理图像文件（如截图）
        
        Args:
            image_path: 图像路径
            
        Returns:
            文档字典或 None
        """
        try:
            logger.info(f"处理图像: {image_path}")
            
            image = Image.open(image_path)
            
            # 转换为 RGB（去除 Alpha 通道）
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # 简化文本（实际应该使用 OCR）
            description = f"图像: {os.path.basename(image_path)}"
            
            metadata = {
                'source': os.path.basename(image_path),
                'type': 'image',
                'size': image.size
            }
            
            return {
                'text': description,
                'metadata': metadata,
                'image_path': image_path
            }
        except Exception as e:
            logger.error(f"图像处理失败: {e}")
            return None
    
    def process_code(self, code_content: str, language: str = 'python') -> Dict:
        """
        处理代码片段
        
        Args:
            code_content: 代码内容
            language: 编程语言
            
        Returns:
            文档字典
        """
        try:
            logger.info(f"处理 {language} 代码")
            
            metadata = {
                'type': 'code',
                'language': language
            }
            
            return {
                'text': code_content,
                'metadata': metadata
            }
        except Exception as e:
            logger.error(f"代码处理失败: {e}")
            return None
    
    def process_file(self, file_path: str) -> List[Dict]:
        """
        自动根据文件类型处理文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            文档列表
        """
        try:
            suffix = Path(file_path).suffix.lower()
            
            if suffix in self.supported_doc_formats:
                return self.process_pdf(file_path)
            elif suffix in self.supported_image_formats:
                doc = self.process_image(file_path)
                return [doc] if doc else []
            else:
                logger.warning(f"不支持的文件格式: {suffix}")
                return []
        except Exception as e:
            logger.error(f"文件处理失败: {e}")
            return []
    
    def extract_text_from_image(self, image_path: str) -> str:
        """
        从图像中提取文本（OCR）
        使用 PaddleOCR
        
        Args:
            image_path: 图像路径
            
        Returns:
            提取的文本
        """
        try:
            from paddleocr import PaddleOCR
            
            logger.info(f"使用 OCR 提取图像文本: {image_path}")
            
            ocr = PaddleOCR(use_angle_cls=True, lang='ch')
            result = ocr.ocr(image_path, cls=True)
            
            # 组织结果
            texts = []
            for line in result:
                for word_info in line:
                    text = word_info[1][0]
                    texts.append(text)
            
            extracted_text = ''.join(texts)
            logger.info(f"OCR 提取完成，长度: {len(extracted_text)}")
            return extracted_text
        except Exception as e:
            logger.error(f"OCR 提取失败: {e}")
            return ""
