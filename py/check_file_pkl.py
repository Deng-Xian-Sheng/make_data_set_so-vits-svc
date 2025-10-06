import pickle
import os

# 读取pkl文件
with open('../data/out/kugou/process_audio.pkl', 'rb') as f:
    data = pickle.load(f)

# 获取pkl文件中的所有键（假设data是字典类型）
pkl_keys = set(data.keys())  # 使用集合便于比较

# 获取../data/source/c目录下的mp3文件名（不含后缀）
mp3_dir = '../data/source/c'
mp3_files = set()

# 遍历目录（不递归）
for filename in os.listdir(mp3_dir):
    if filename.endswith('.mp3'):
        # 去除后缀名并添加到集合
        base_name = os.path.splitext(filename)[0]
        mp3_files.add(base_name)

# 计算差异
only_in_pkl = pkl_keys - mp3_files  # 只在pkl中存在的键
only_in_mp3 = mp3_files - pkl_keys  # 只在MP3目录中存在的文件

# 打印结果
print("只在pkl文件中存在的键（数量: {}）:".format(len(only_in_pkl)))
print(sorted(only_in_pkl))

print("\n只在MP3目录中存在的文件（数量: {}）:".format(len(only_in_mp3)))
print(sorted(only_in_mp3))

# 可选：将结果保存到文件
with open('comparison_results.txt', 'w') as result_file:
    result_file.write("只在pkl文件中存在的键（{}个）:\n".format(len(only_in_pkl)))
    result_file.write("\n".join(sorted(only_in_pkl)))
    
    result_file.write("\n\n只在MP3目录中存在的文件（{}个）:\n".format(len(only_in_mp3)))
    result_file.write("\n".join(sorted(only_in_mp3)))