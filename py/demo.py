# from resemblyzer import VoiceEncoder, preprocess_wav
# from scipy.spatial.distance import cosine
# import librosa


# def load_and_encode(file_path):
#     # 使用Librosa加载音频文件
#     audio, rate = librosa.load(file_path, sr=None)

#     # 使用Resemblyzer的VoiceEncoder处理音频
#     encoder = VoiceEncoder()
#     embedding = encoder.embed_utterance(audio)

#     return embedding


# def compare_voice(file1, file2):
#     # 加载并编码两个音频文件
#     embedding1 = load_and_encode(file1)
#     embedding2 = load_and_encode(file2)

#     # 计算两个嵌入之间的相似度
#     similarity = 1 - cosine(embedding1, embedding2)
#     return similarity


# # 指定音频文件的路径
# file1 = "./test_data/chunk6.mp3"  # 替换为你的文件路径
# file2 = "./test_data/2chunk9.mp3"  # 替换为你的文件路径

# # 计算相似度
# similarity_score = compare_voice(file1, file2)
# print(f"声纹相似度: {similarity_score}")


# from pydub import AudioSegment
# from pydub.silence import split_on_silence


# def split_audio(file_path, min_silence_len=500, silence_thresh=-20):
#     # 加载MP3文件
#     audio = AudioSegment.from_mp3(file_path)

#     # 分割音频
#     # min_silence_len: 静默最短持续时间（毫秒）
#     # silence_thresh: 认为是静默的阈值（dBFS）
#     chunks = split_on_silence(
#         audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh
#     )

#     # 导出分割后的音频
#     for i, chunk in enumerate(chunks):
#         chunk.export(f"./test_data/2chunk{i}.mp3", format="mp3")


# # 调用函数，替换为你的MP3文件路径
# split_audio("./test_data/23-12-2022-11-03-Melody.mp3")


import whisper
import sounddevice as sd
import numpy as np

# 录音设置
duration = 5  # 录音时长（秒）
samplerate = 16000  # 采样率


def record_audio(duration, samplerate):
    """录制音频"""
    recording = sd.rec(
        int(duration * samplerate), samplerate=samplerate, channels=1, dtype="float32"
    )
    sd.wait()
    return recording


def transcribe_audio(audio, model):
    """使用Whisper模型转录音频"""
    audio = np.squeeze(audio)  # 确保音频是一维的
    result = model.transcribe(audio)
    return result["text"]


def main():
    # 加载Whisper模型
    model = whisper.load_model("large-v3")

    while True:
        print("开始录音...")
        audio = record_audio(duration, samplerate)
        print("录音结束，正在识别...")

        # 识别语音
        text = transcribe_audio(audio, model)

        # 根据识别结果执行操作
        if "过" in text:
            print("过")
        elif "下一个" in text:
            print("下一个")
        else:
            print("未识别到指令")
            print(text)


if __name__ == "__main__":
    main()
