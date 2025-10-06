import json
import os
import requests
import re
from datetime import datetime
import math
import argparse
import time
from urllib.parse import unquote

# 配置参数
CONFIG = {
    "author_birthday": "2009-11-14",  # 默认歌手生日
    "output_dir": "./data/source/kugou/",
    "api_template": "https://m.kugou.com/app/i/getSongInfo.php?cmd=playInfo&hash={}",
    "quality": "flac"  # 可选: flac, 320, high, 128
}

def calculate_age(birthday_str, publish_date_str):
    """计算歌曲发布时歌手的年龄"""
    birthday = datetime.strptime(birthday_str, "%Y-%m-%d")
    publish_date = datetime.strptime(publish_date_str, "%Y-%m-%d")
    age = math.floor((publish_date - birthday).days / 365)
    return max(0, age)  # 年龄不能为负数

def sanitize_filename(name):
    """移除文件名中的非法字符"""
    illegal_chars = r'[\\/:*?"<>|]'
    return re.sub(illegal_chars, '_', name)

def get_download_url(song_data, quality):
    """获取指定质量的下载链接"""
    # 根据质量选择hash
    quality_map = {
        "flac": "hash_flac",
        "320": "hash_320",
        "high": "hash_high",
        "128": "hash"
    }
    
    hash_key = quality_map.get(quality, "hash")
    audio_hash = song_data["audio_info"].get(hash_key, "")
    
    if not audio_hash:
        print(f"未找到{quality}质量的hash")
        return None
    
    try:
        # 构造API请求
        url = CONFIG["api_template"].format(audio_hash)
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # 解析响应
        data = response.json()
        
        # 检查状态
        if data.get("status") != 1:
            print(f"API返回错误状态: {data.get('errcode', '未知错误')}")
            return None
        
        # 优先返回主下载链
        if data.get("url"):
            return data["url"]
        
        # 备用下载链
        if data.get("backup_url") and isinstance(data["backup_url"], list) and data["backup_url"]:
            return data["backup_url"][0]
        
    except Exception as e:
        print(f"获取下载链接失败: {e}")
    
    return None

def download_song(url, filename, output_dir):
    """下载歌曲文件"""
    try:
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 获取文件扩展名
        parsed_url = unquote(url)
        ext = os.path.splitext(parsed_url)[1].split('?')[0] or '.mp3'
        filepath = os.path.join(output_dir, f"{filename}{ext}")
        
        # 下载文件
        print(f"开始下载: {filename}{ext}")
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        # 获取文件大小（用于进度显示）
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                # 显示下载进度
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    print(f"\r下载进度: {percent:.1f}% ({downloaded}/{total_size} bytes)", end='')
        
        print(f"\n下载完成: {filepath}")
        return True
        
    except Exception as e:
        print(f"\n下载失败: {filename} - {str(e)}")
        return False

def process_songs(json_file):
    """处理歌曲JSON文件并下载"""
    with open(json_file, 'r', encoding='utf-8') as f:
        songs = json.load(f)
    
    count = 1
    total_songs = len(songs)
    
    for song in songs:
        try:
            # 解析歌曲信息
            song_name = song["audio_name"]
            publish_date = song["publish_date"]
            authors = ", ".join([author["base"]["author_name"] for author in song["authors"]])
            
            print(f"\n处理歌曲 {count}/{total_songs}: {song_name} - {authors}")
            
            # 计算歌手年龄
            age = calculate_age(CONFIG["author_birthday"], publish_date)
            
            # 生成安全文件名
            safe_name = sanitize_filename(song_name)
            filename = f"{count}-{age}-{publish_date}-{safe_name}"
            
            # 获取下载链接
            download_url = get_download_url(song, CONFIG["quality"])
            if not download_url:
                print(f"跳过: {song_name} - 无有效下载链接")
                continue
                
            # 下载歌曲
            if download_song(download_url, filename, CONFIG["output_dir"]):
                count += 1
                
            # 避免请求过快
            time.sleep(1)
                
        except Exception as e:
            print(f"处理歌曲失败: {song_name} - {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='下载酷狗歌曲')
    parser.add_argument('json_file', help='歌曲JSON文件路径')
    parser.add_argument('--birthday', default=CONFIG["author_birthday"], 
                        help='歌手生日 (格式: YYYY-MM-DD)')
    parser.add_argument('--output', default=CONFIG["output_dir"], 
                        help='输出目录路径')
    parser.add_argument('--quality', choices=['flac', '320', 'high', '128'], 
                        default=CONFIG["quality"], help='音频质量 (flac, 320, high, 128)')
    
    args = parser.parse_args()
    
    # 更新配置
    CONFIG["author_birthday"] = args.birthday
    CONFIG["output_dir"] = args.output
    CONFIG["quality"] = args.quality
    
    print(f"开始下载任务，音频质量: {CONFIG['quality']}")
    print(f"歌手生日: {CONFIG['author_birthday']}")
    print(f"输出目录: {CONFIG['output_dir']}")
    
    process_songs(args.json_file)
    print("\n所有歌曲处理完成!")