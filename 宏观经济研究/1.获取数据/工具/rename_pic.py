import os
import datetime

def convert_timestamp_to_filename(timestamp_ms):
    """将毫秒级时间戳转换为IMG_YYYYMMDD_HHMMSS格式的文件名前缀"""
    # 将毫秒转换为秒
    timestamp_sec = timestamp_ms / 1000
    # 转换为东八区时间
    dt = datetime.datetime.fromtimestamp(timestamp_sec, datetime.timezone(datetime.timedelta(hours=8)))
    # 格式化为YYYYMMDD_HHMMSS
    return dt.strftime("IMG_%Y%m%d_%H%M%S")

def batch_rename_files(directory):
    """批量重命名指定目录下符合条件的文件"""
    # 记录重命名结果
    renamed_files = []
    skipped_files = []
    
    # 遍历目录中的所有文件
    for filename in os.listdir(directory):
        # 检查文件名是否以"mmexport"开头
        if filename.startswith("mmexport"):
            # 分割文件名和扩展名
            base_name, ext = os.path.splitext(filename)
            # 提取数字部分
            timestamp_str = base_name[len("mmexport"):]
            
            try:
                # 尝试将数字部分转换为整数（时间戳）
                timestamp_ms = int(timestamp_str)
                # 转换时间戳为文件名前缀
                new_base = convert_timestamp_to_filename(timestamp_ms)
                # 构建新文件名
                new_filename = f"{new_base}{ext}"
                # 构建完整路径
                old_path = os.path.join(directory, filename)
                new_path = os.path.join(directory, new_filename)
                
                # 检查新文件名是否已存在
                if os.path.exists(new_path):
                    # 如果已存在，添加计数器避免覆盖
                    counter = 1
                    while True:
                        temp_new_filename = f"{new_base}_{counter}{ext}"
                        temp_new_path = os.path.join(directory, temp_new_filename)
                        if not os.path.exists(temp_new_path):
                            new_filename = temp_new_filename
                            new_path = temp_new_path
                            break
                        counter += 1
                
                # 执行重命名
                os.rename(old_path, new_path)
                renamed_files.append(f"{filename} -> {new_filename}")
                
            except ValueError:
                # 数字部分无法转换为整数，跳过该文件
                skipped_files.append(f"{filename} (无效的时间戳格式)")
            except Exception as e:
                # 其他错误
                skipped_files.append(f"{filename} (错误: {str(e)})")
    
    # 保存结果到日志文件
    result_log = "批量重命名结果\n"
    result_log += "====================\n"
    result_log += f"成功重命名 {len(renamed_files)} 个文件:\n"
    for item in renamed_files:
        result_log += f"- {item}\n"
    
    result_log += "\n"
    result_log += f"跳过 {len(skipped_files)} 个文件:\n"
    for item in skipped_files:
        result_log += f"- {item}\n"
    
    log_path = os.path.join(directory, "重命名日志.md")
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(result_log)
    
    print(f"重命名完成，结果已保存到: {log_path}")
    print(f"成功重命名: {len(renamed_files)} 个文件")
    print(f"跳过: {len(skipped_files)} 个文件")

if __name__ == "__main__":
    # 指定目标目录
    target_directory = r"H:\照片\WeiXin"
    
    # 验证目录是否存在
    if not os.path.exists(target_directory):
        print(f"错误: 目录不存在 - {target_directory}")
    elif not os.path.isdir(target_directory):
        print(f"错误: 不是有效的目录 - {target_directory}")
    else:
        batch_rename_files(target_directory)