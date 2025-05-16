#!/bin/bash

# 监听目录
WATCH_DIR="$(cd "$(dirname "$0")/../reading" && pwd)"

# 日志文件
LOG_FILE="$WATCH_DIR/pdfannots.log"

# 日志函数
log() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] $1" | tee -a "$LOG_FILE"
}

# 确保在项目根目录运行
cd "$(dirname "$0")/.." || exit 1

log "Starting PDF annotations watcher for directory: $WATCH_DIR"

# 使用 fswatch 监听 PDF 文件变化，指定关注 Updated 和 Created 事件
fswatch -0 --event Updated --event Created "$WATCH_DIR" | while IFS= read -r -d "" file; do
    # 检查是否是 PDF 文件
    if [[ "$file" =~ \.pdf$ ]]; then
        # 获取文件名（不含路径和扩展名）
        filename=$(basename "$file" .pdf)
        # 生成输出文件名
        output_file="$WATCH_DIR/$filename.$(date +%Y%m%d_%H%M%S).pdfannots.md"
        
        log "Processing PDF file: $file"
        
        # 使用 pdfannots 提取注释并保存为 markdown
        if pdfannots "$file" -o "$output_file"; then
            log "Successfully generated annotations: $output_file"
        else
            log "Error: Failed to generate annotations for $file"
        fi
    fi
done