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
def extract_highlights(pdf_path, line_height):
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
                    # 根据行高调整文本框的高度
                    height = quad.rect.height * line_height
                    y_adjustment = (height - quad.rect.height) / 2
                    expanded_rect = fitz.Rect(
                        round(quad.rect.x0, 3) + 0.1,
                        round(quad.rect.y0 - y_adjustment, 3),
                        round(quad.rect.x1, 3) - 0.1,
                        round(quad.rect.y1 + y_adjustment, 3),
                    )
                    # 输出原始高度和调整后的高度
                    logger.info(
                        f"高亮区域高度 - 原始: {quad.rect.height:.2f}, "
                        f"调整后: {height:.2f}, "
                        f"调整量: {y_adjustment:.2f}"
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
    def __init__(self, line_height=1.5):
        self.line_height = line_height

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(".pdf"):
            try:
                highlights = extract_highlights(
                    event.src_path, self.line_height
                )  # Pass line_height instead of page_offset
                if highlights:
                    export_to_markdown(highlights, event.src_path)
            except Exception as e:
                logger.error(f"Error extracting highlights from {event.src_path}: {e}")


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

    parser = argparse.ArgumentParser(
        description="Watch PDF files for changes and extract highlights"
    )
    parser.add_argument(
        "--line-height",
        type=float,
        default=1.5,
        help="Line height multiplier for text extraction",
    )
    args = parser.parse_args()

    event_handler = PDFEventHandler(line_height=args.line_height)
    observer = Observer()
    observer.schedule(event_handler, ".", recursive=True)

    logger.info(f"Listening for changes in {watch_directory}...")

    try:
        observer.start()  # Start the observer only once
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
