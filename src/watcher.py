import os
import time
import logging
import argparse
import fitz  # PyMuPDF
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 设置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger()


# 提取 PDF 中的高亮标注
def extract_highlights(pdf_path, page_offset):
    highlights = []
    try:
        doc = fitz.open(pdf_path)
        # 收集所有高亮内容
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            page_num += 1

            # 获取所有高亮标注， 按照左上角坐标排序
            annots = [a for a in (page.annots() or []) if a.type[0] == 8 and a.vertices]

            def annot_sort_key(annot):
                quad_points = annot.vertices
                first_point = quad_points[0]
                return (first_point[1], first_point[0])

            annots.sort(key=annot_sort_key)

            for annot in annots:
                quad_points = annot.vertices
                quads = [
                    fitz.Quad(quad_points[i : i + 4])
                    for i in range(0, len(quad_points), 4)
                ]

                highlight_text = ""
                for quad in quads:
                    expanded_rect = fitz.Rect(
                        round(quad.rect.x0, 3) + 0.1,
                        round(quad.rect.y0, 3),
                        round(quad.rect.x1, 3) - 0.1,
                        round(quad.rect.y1, 3),
                    )
                    highlight_text += page.get_textbox(expanded_rect)

                if highlight_text:
                    highlights.append(f"{highlight_text}")

    except Exception as e:
        logger.error(f"Error extracting highlights from {pdf_path}: {e}")
    return highlights


# 将高亮标注转换为 Markdown 格式
def export_to_markdown(highlights, pdf_path):
    # 获取 PDF 文件的同名文件作为输出文件
    output_file = os.path.splitext(pdf_path)[0] + ".annots.md"
    try:
        with open(output_file, "w") as f:
            # 获取 PDF 文件的同名文件作为输出文件
            output_file = os.path.splitext(pdf_path)[0] + ".annots.md"
            # 获取 PDF 文件名（不含扩展名）作为标题
            pdf_title = os.path.splitext(os.path.basename(pdf_path))[0]
            f.write(f"# {pdf_title}\n\n")
            if len(highlights) == 0:
                f.write("\n\n")
            for index, highlight in enumerate(highlights, 1):
                f.write(f"{index}. {highlight}\n\n")
        logger.info(f"Highlights exported to {output_file}")
    except Exception as e:
        logger.error(f"Error writing markdown file: {e}")


# 监听文件变动的事件
class PDFEventHandler(FileSystemEventHandler):
    def __init__(self, page_offset):
        self.page_offset = page_offset

    def on_modified(self, event):
        if event.src_path.endswith(".pdf"):
            logger.info(f"Detected change in {event.src_path}")
            highlights = extract_highlights(event.src_path, self.page_offset)
            export_to_markdown(highlights, event.src_path)


# 设置监听的目录
def main():
    # 获取当前脚本所在目录
    watch_directory = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "reading"
    )

    if not os.path.exists(watch_directory):
        logger.error(f"The directory {watch_directory} does not exist. Exiting.")
        return

    os.makedirs(watch_directory, exist_ok=True)

    event_handler = PDFEventHandler(page_offset=3)  # 设置默认偏移量为3
    observer = Observer()
    observer.schedule(event_handler, watch_directory, recursive=True)

    logger.info(f"Listening for changes in {watch_directory}...")

    try:
        observer.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
