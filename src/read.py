import os
import sys
import time
import shutil
import argparse
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

def get_unique_filename(dst_dir, new_filename):
    """生成唯一的文件名，如果存在重名则添加序号"""
    base, ext = os.path.splitext(new_filename)
    counter = 1
    result_filename = new_filename
    
    while os.path.exists(os.path.join(dst_dir, result_filename)):
        result_filename = f"{base}_{counter}{ext}"
        counter += 1
    
    return result_filename

def copy_pdf_to_reading(src_path):
    try:
        # 确保源文件存在且是 PDF
        if not os.path.exists(src_path):
            raise FileNotFoundError(f"Source file not found: {src_path}")
        if not src_path.lower().endswith('.pdf'):
            raise ValueError(f"Source file is not a PDF: {src_path}")

        # 构造目标路径
        filename = os.path.basename(src_path)
        name_without_ext = os.path.splitext(filename)[0]
        timestamp = time.strftime('%Y%m')
        new_filename = f"{name_without_ext}.{timestamp}.pdf"

        # 确保目标目录存在
        dst_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src', 'reading')
        os.makedirs(dst_dir, exist_ok=True)

        # 获取唯一的文件名
        unique_filename = get_unique_filename(dst_dir, new_filename)
        dst_path = os.path.join(dst_dir, unique_filename)

        # 复制文件
        shutil.copy2(src_path, dst_path)
        logger.info(f"Successfully copied {src_path} to {dst_path}")

    except Exception as e:
        logger.error(f"Error copying PDF: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Copy PDF file to reading directory with timestamp')
    parser.add_argument('pdf_path', help='Path to the PDF file')
    args = parser.parse_args()

    copy_pdf_to_reading(args.pdf_path)

if __name__ == '__main__':
    main()