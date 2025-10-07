import os
import argparse
from pydub import AudioSegment

def convert_mp3_to_wav(directory):
    # 确保目录存在
    if not os.path.isdir(directory):
        print(f"错误：目录 '{directory}' 不存在")
        return

    # 获取目录下所有mp3文件（非递归）
    mp3_files = [f for f in os.listdir(directory) 
                 if f.lower().endswith('.mp3') and os.path.isfile(os.path.join(directory, f))]
    
    if not mp3_files:
        print(f"目录 '{directory}' 中没有找到MP3文件")
        return

    for mp3_file in mp3_files:
        # 构建完整文件路径
        mp3_path = os.path.join(directory, mp3_file)
        wav_file = os.path.splitext(mp3_file)[0] + '.wav'
        wav_path = os.path.join(directory, wav_file)
        
        try:
            # 转换MP3到WAV
            audio = AudioSegment.from_mp3(mp3_path)
            audio.export(wav_path, format="wav")
            
            # 验证WAV文件是否创建成功
            if os.path.exists(wav_path):
                os.remove(mp3_path)
                print(f"转换成功: '{mp3_file}' -> '{wav_file}' (原始文件已删除)")
            else:
                print(f"警告: 转换后的文件 '{wav_file}' 未找到，保留原始文件")
                
        except Exception as e:
            print(f"转换 '{mp3_file}' 失败: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='将目录中的MP3文件转换为WAV格式并删除原始文件')
    parser.add_argument('directory', type=str, help='包含MP3文件的目录路径')
    args = parser.parse_args()
    
    convert_mp3_to_wav(args.directory)
