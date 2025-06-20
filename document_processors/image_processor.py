"""
图片文档处理器
使用OCR技术从图片中提取文本内容
"""

import logging
from typing import List, Dict, Any
import os

from .base_processor import BaseDocumentProcessor

# 日志配置
logger = logging.getLogger(__name__)

class ImageProcessor(BaseDocumentProcessor):
    """图片文档处理器（OCR）"""
    
    def __init__(self):
        """初始化图片处理器"""
        super().__init__()
        self.ocr_method = self._detect_ocr_method()
    
    def can_process(self, file_path: str) -> bool:
        """判断是否可以处理图片文件"""
        return file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'))
    
    def get_supported_extensions(self) -> List[str]:
        """获取支持的文件扩展名"""
        return ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
    
    def _detect_ocr_method(self) -> str:
        """检测可用的OCR方法"""
        try:
            import easyocr
            return 'easyocr'
        except ImportError:
            try:
                import pytesseract
                return 'pytesseract'
            except ImportError:
                logger.warning("未安装OCR库，图片处理功能将受限")
                return 'none'
    
    def extract_text(self, file_path: str) -> str:
        """
        从图片文件中提取文本（OCR）
        
        Args:
            file_path: 图片文件路径
        
        Returns:
            提取的文本内容
        """
        try:
            if self.ocr_method == 'easyocr':
                return self._extract_with_easyocr(file_path)
            elif self.ocr_method == 'pytesseract':
                return self._extract_with_pytesseract(file_path)
            else:
                return f"无法处理图片文件：{os.path.basename(file_path)} - 未安装OCR库"
                
        except Exception as e:
            logger.error(f"从图片提取文本失败: {file_path} - {e}")
            return f"图片OCR处理失败：{str(e)}"
    
    def _extract_with_easyocr(self, file_path: str) -> str:
        """使用EasyOCR提取文本"""
        try:
            import easyocr
            
            # 创建OCR读取器（支持中英文）
            reader = easyocr.Reader(['ch_tra', 'ch_sim', 'en'], gpu=False)
            
            content = []
            content.append(f"图片文件：{os.path.basename(file_path)}")
            content.append("OCR引擎：EasyOCR")
            content.append("=" * 50)
            
            # 执行OCR识别
            results = reader.readtext(file_path)
            
            if not results:
                content.append("（图片中未检测到文本内容）")
                return "\n".join(content)
            
            content.append(f"检测到 {len(results)} 个文本区域")
            content.append("")
            
            # 处理识别结果
            high_confidence_text = []
            all_text = []
            
            for i, (bbox, text, confidence) in enumerate(results, 1):
                cleaned_text = text.strip()
                if cleaned_text:
                    all_text.append(cleaned_text)
                    
                    # 高置信度文本（>0.7）
                    if confidence > 0.7:
                        high_confidence_text.append(cleaned_text)
                    
                    # 详细信息（调试用）
                    content.append(f"区域 {i}：{cleaned_text} (置信度: {confidence:.2f})")
            
            content.append("")
            content.append("=" * 50)
            content.append("提取的文本内容：")
            content.append("=" * 50)
            
            # 优先使用高置信度文本
            if high_confidence_text:
                content.extend(high_confidence_text)
            else:
                # 如果没有高置信度文本，使用所有文本
                content.extend(all_text)
            
            return "\n".join(content)
            
        except Exception as e:
            logger.error(f"EasyOCR处理失败: {file_path} - {e}")
            # 降级到pytesseract
            return self._extract_with_pytesseract(file_path)
    
    def _extract_with_pytesseract(self, file_path: str) -> str:
        """使用Pytesseract提取文本"""
        try:
            import pytesseract
            from PIL import Image
            
            content = []
            content.append(f"图片文件：{os.path.basename(file_path)}")
            content.append("OCR引擎：Pytesseract")
            content.append("=" * 50)
            
            # 打开图片
            image = Image.open(file_path)
            
            # 执行OCR识别（支持中英文）
            # 配置OCR参数
            config = '--oem 3 --psm 6 -l chi_tra+chi_sim+eng'
            
            try:
                text = pytesseract.image_to_string(image, config=config)
            except:
                # 如果中文识别失败，只用英文
                text = pytesseract.image_to_string(image, lang='eng')
            
            if text.strip():
                content.append("提取的文本内容：")
                content.append("=" * 50)
                content.append(text.strip())
            else:
                content.append("（图片中未检测到文本内容）")
            
            return "\n".join(content)
            
        except Exception as e:
            logger.error(f"Pytesseract处理失败: {file_path} - {e}")
            return f"OCR处理失败：{str(e)}"
    
    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        提取图片文档元数据
        
        Args:
            file_path: 图片文件路径
            
        Returns:
            图片元数据字典
        """
        try:
            from PIL import Image
            
            metadata_dict = {
                'document_type': 'Image',
                'file_extension': os.path.splitext(file_path)[1].lower(),
                'ocr_method': self.ocr_method
            }
            
            try:
                # 获取图片基本信息
                with Image.open(file_path) as img:
                    metadata_dict.update({
                        'width': img.width,
                        'height': img.height,
                        'mode': img.mode,
                        'format': img.format,
                        'size_pixels': img.width * img.height
                    })
                    
                    # 获取EXIF信息（如果有）
                    try:
                        exif = img._getexif()
                        if exif:
                            # 提取常用EXIF信息
                            exif_dict = {}
                            for tag_id, value in exif.items():
                                try:
                                    from PIL.ExifTags import TAGS
                                    tag = TAGS.get(tag_id, tag_id)
                                    exif_dict[tag] = str(value)
                                except:
                                    pass
                            
                            if exif_dict:
                                metadata_dict['exif'] = exif_dict
                    except:
                        pass
                    
            except Exception as e:
                logger.warning(f"获取图片基本信息失败: {file_path} - {e}")
                metadata_dict['image_error'] = str(e)
            
            # OCR处理信息
            if self.ocr_method != 'none':
                metadata_dict.update({
                    'ocr_available': True,
                    'supported_ocr_languages': self._get_supported_languages()
                })
            else:
                metadata_dict.update({
                    'ocr_available': False,
                    'ocr_error': '未安装OCR库'
                })
            
            return metadata_dict
            
        except Exception as e:
            logger.error(f"提取图片元数据失败: {file_path} - {e}")
            return {
                'document_type': 'Image',
                'error': str(e)
            }
    
    def _get_supported_languages(self) -> List[str]:
        """获取支持的OCR语言"""
        if self.ocr_method == 'easyocr':
            return ['中文繁体', '中文简体', '英文']
        elif self.ocr_method == 'pytesseract':
            try:
                import pytesseract
                langs = pytesseract.get_languages()
                return langs
            except:
                return ['英文']
        else:
            return [] 