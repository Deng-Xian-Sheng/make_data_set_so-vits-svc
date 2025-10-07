import os
import hashlib

def calculate_md5(file_path):
    """计算文件的MD5哈希值"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def rename_files_to_md5(directory):
    """将目录中的文件重命名为其MD5值（保留扩展名）"""
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        
        # 跳过子目录和隐藏文件
        if not os.path.isfile(file_path) or filename.startswith('.'):
            continue
        
        # 计算MD5并准备新文件名
        try:
            file_md5 = calculate_md5(file_path)
            file_ext = os.path.splitext(filename)[1]
            new_filename = f"{file_md5}{file_ext}"
            new_path = os.path.join(directory, new_filename)
            
            # 避免文件名冲突
            counter = 1
            while os.path.exists(new_path):
                new_filename = f"{file_md5}_{counter}{file_ext}"
                new_path = os.path.join(directory, new_filename)
                counter += 1
            
            # 执行重命名
            os.rename(file_path, new_path)
            print(f"Renamed: {filename} -> {new_filename}")
        
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")

if __name__ == "__main__":
    target_dir = input("Enter directory path: ").strip()
    
    if not os.path.isdir(target_dir):
        print("Error: Invalid directory path")
    else:
        rename_files_to_md5(target_dir)
        print("Operation completed.")