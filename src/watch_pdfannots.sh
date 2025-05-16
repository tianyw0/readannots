#!/bin/bash

# 监听目录
WATCH_DIR="$(cd "$(dirname "$0")/reading" && pwd)"


# 日志函数
log() {
    local level=$1
    shift
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    case "$level" in
        INFO)
            echo -e "\033[1;32m[$timestamp] [INFO] $*\033[0m"
            ;;
        WARN)
            echo -e "\033[1;33m[$timestamp] [WARN] $*\033[0m"
            ;;
        ERROR)
            echo -e "\033[1;31m[$timestamp] [ERROR] $*\033[0m"
            ;;
        *)
            echo -e "\033[1;37m[$timestamp] [UNKNOWN] $*\033[0m"
            ;;
    esac
}

# 确保在项目根目录运行
cd "$(dirname "$0")/.." || exit 1

log INFO "Starting PDF annotations watcher for directory: $WATCH_DIR"

fswatch -0 -x "$WATCH_DIR" | while IFS= read -r -d '' file_and_event; do
    file=$(echo "$file_and_event" | cut -d ' ' -f 1)
    event=$(echo "$file_and_event" | cut -d ' ' -f 2-)
    # log INFO "Detected change in file: $file with event: $event"
    # 检查是否是 PDF 文件
    if [[ "$file" =~ \.pdf$ ]]; then
        log INFO "Detected PDF file: $file"
        # 检查文件是否存在
        if [[ ! -f "$file" ]]; then
            log ERROR "File $file does not exist."
            continue
        fi
        # 获取文件名（不含路径和扩展名）
        file_base_name=$(basename "$file" .pdf)
        # 生成输出文件名
        output_file="$WATCH_DIR/$file_base_name.pdfannots.json"

        log INFO "Processing PDF file: $file"

        # 使用 pdfannots 提取注释并保存为 JSON
        if pdfannots "$file" -f json -o "$output_file"; then
            log INFO "Successfully generated annotations: $output_file"
        else
            log ERROR "Failed to generate annotations for $file"
        fi
    fi
done