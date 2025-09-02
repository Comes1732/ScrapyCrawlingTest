
#!/bin/bash
# 脚本功能：在文件中搜索指定内容并输出匹配行号

# 检查参数数量是否符合要求（需要2个参数）
if [ $# -ne 2 ]; then
    # 参数错误时显示用法说明
    echo "错误：需要2个参数"
    echo "用法: $0 <文件名> <搜索内容>"
    exit 1
fi

# 将参数赋值给有意义的变量名
file_to_search=$1
search_pattern=$2

# 检查目标文件是否存在且可读
if [ ! -f "$file_to_search" ]; then
    echo "错误：文件 $file_to_search 不存在"
    exit 1
fi

if [ ! -r "$file_to_search" ]; then
    echo "错误：文件 $file_to_search 不可读"
    exit 1
fi

# 执行搜索并仅输出行号
echo "在文件 $file_to_search 中找到匹配 '$search_pattern' 的行号:"
grep -n "$search_pattern" "$file_to_search" | cut -d: -f1