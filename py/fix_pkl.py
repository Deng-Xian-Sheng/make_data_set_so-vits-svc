import pickle
import os

# 定义要删除的键
key_to_delete = '15-12-2022-08-12-I Love You 3000'

# 读取pkl文件
with open('../data/out/kugou/process_audio.pkl', 'rb') as f:
    data = pickle.load(f)

# print(data)

# 检查并删除指定键
if key_to_delete in data:
    del data[key_to_delete]
    print(f"已删除键: {key_to_delete}")
else:
    print(f"未找到键: {key_to_delete}")

# 备份原文件（可选）
os.rename('../data/out/kugou/process_audio.pkl', '../data/out/kugou/process_audio_backup.pkl')

# 写入更新后的数据
with open('../data/out/kugou/process_audio.pkl', 'wb') as f:
    pickle.dump(data, f)

print("文件更新完成！原文件已备份为 process_audio_backup.pkl")