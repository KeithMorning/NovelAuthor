#!/bin/bash
OUTPUT_FILE="/private/tmp/claude-501/-Users-keithxi-Documents-work-Nover/tasks/b82251b.output"
LAST_SIZE=0

echo "监控章节生成进度..."
echo "按 Ctrl+C 停止监控"
echo ""

while true; do
    if [ -f "$OUTPUT_FILE" ]; then
        CURRENT_SIZE=$(wc -c < "$OUTPUT_FILE")
        if [ "$CURRENT_SIZE" != "$LAST_SIZE" ]; then
            clear
            echo "=========================================="
            echo "章节生成进度 (文件大小: $CURRENT_SIZE bytes)"
            echo "=========================================="
            echo ""
            tail -20 "$OUTPUT_FILE"
            LAST_SIZE=$CURRENT_SIZE
        fi
    fi
    sleep 3
done
