#!/bin/bash

# 监听目录
WATCH_DIR="$(cd "$(dirname "$0")/reading" && pwd)"


# 日志函数
log() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "\033[1;32m[$timestamp] $1\033[0m"
}

# 确保在项目根目录运行
cd "$(dirname "$0")/.." || exit 1

log "Starting PDF annotations watcher for directory: $WATCH_DIR"

fswatch -0 -x "$WATCH_DIR" | while IFS= read -r -d '' file_and_event; do
    file=$(echo "$file_and_event" | cut -d ' ' -f 1)
    event=$(echo "$file_and_event" | cut -d ' ' -f 2-)
    # log "Detected change in file: $file with event: $event"
    # 检查是否是 PDF 文件
    if [[ "$file" =~ \.pdf$ ]]; then
        log "Detected PDF file: $file"
        # 检查文件是否存在
        if [[ ! -f "$file" ]]; then
            log "Error: File $file does not exist."
            continue
        fi
        # 获取文件名（不含路径和扩展名）
        file_base_name=$(basename "$file" .pdf)
        # 生成输出文件名
        output_file="$WATCH_DIR/$file_base_name.pdfannots.md"

        log "Processing PDF file: $file"
        
        # 使用 pdfannots 提取注释并保存为 markdown
        if pdfannots "$file" -o "$output_file"; then
            log "Successfully generated annotations: $output_file"
        else
            log "Error: Failed to generate annotations for $file"
        fi
    fi
done