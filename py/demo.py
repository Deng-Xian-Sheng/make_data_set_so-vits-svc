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


#
# Copyright 2016 The BigDL Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import torch
import time
from bigdl.llm.transformers import AutoModelForSpeechSeq2Seq
from transformers import WhisperProcessor
from multiprocessing import Process, Queue, Value
import pyaudio
import numpy as np
from io import BytesIO

speech_to_text_queue = Queue()

"""
linux 执行这个优化性能
pip install bigdl-nano
source bigdl-nano-init
"""

"""
请实现一个类class SoundRecording(Process):，
它使用多进程库multiprocessing，
它使用pyaudio的回调模式录音，
如果检测到录制的音频的音量大于某个值(单位dBFS)，
就缓存音频数据，
如果检测到录制的音频的音量大小小于某个值(单位dBFS)且持续某个秒数后就立即将缓存的音频数据使用非阻塞发送到speech_to_text队列(multiprocessing的Queue())，
如果缓存的音频数据时长等于5秒时就立即将缓存的音频数据使用非阻塞发送到speech_to_text队列(multiprocessing的Queue())。
"""

class SoundRecording(Process):
    def __init__(
        self,
        threshold,
        silence_duration=2,
        threshold_anti_shake=300, #音量防抖动阈值ms
        chunk_size=1024,
        audio_format=pyaudio.paInt16,
        channels=1,
        rate=16000,
    ):
        super(SoundRecording, self).__init__()
        self.threshold = threshold
        self.silence_duration = silence_duration
        self.chunk_size = chunk_size
        self.format = audio_format
        self.channels = channels
        self.rate = rate
        self.stream = None
        self.running = True
        self.audio_buffer = BytesIO()
        self.last_high_volume_time = None #上次高音量时间
        self.threshold_anti_shake = threshold_anti_shake

    def run(self):
        self.audio_interface = pyaudio.PyAudio()
        self.stream = self.audio_interface.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk_size,
            stream_callback=self.callback
        )

        self.stream.start_stream() #? 可有可无？

        # ! add exit flag
        time.sleep(120)
        self.stream.stop_stream()
        self.stream.close()
        self.audio_interface.terminate()

    def callback(self, in_data, frame_count, time_info, status):
        volume = self.rms(in_data)
        current_time = time.time()

        if volume >= self.threshold or (self.last_high_volume_time is not None and (current_time - self.last_high_volume_time) * 1000.0 <= self.threshold_anti_shake):
            print(1,time.time())
            if volume >= self.threshold:
                print(4,time.time())
                self.last_high_volume_time = current_time
            else:
                # ! debug delete me
                print(3,time.time())
            self.audio_buffer.write(in_data)
        
        if self.last_high_volume_time is not None and ((current_time - self.last_high_volume_time >= self.silence_duration) or (((self.audio_buffer.tell() * self.chunk_size) / self.rate) >= 5)):
            self.flush_buffer()
            print(2,time.time())

        return (None, pyaudio.paContinue)

    def flush_buffer(self):
        if self.audio_buffer.tell() != 0:
            # 将字节串转换为浮点数数组
            #todo 流的处理
            speech_to_text_queue.put(np.frombuffer(b"".join(self.audio_buffer.getvalue()),dtype=np.int16).astype(np.float32) / 32768.0,block=False)
            self.audio_buffer.seek(0)  # 重置缓冲区指针
            self.audio_buffer.truncate()  # 重置缓冲区
            self.last_high_volume_time = None
    
    def rms(self,frame):
        shorts = np.frombuffer(frame, dtype=np.int16)
        count = len(shorts)
        sum_squares = np.sum(np.square(shorts / 32768.0))
        rms = np.sqrt(sum_squares / count)
        return 20 * np.log10(rms + 1e-7)
    
class SpeechToText(Process):
    def run(self) -> None:
        model_path = "model"
        language = "chinese"

        # Load model in 4 bit,
        # which convert the relevant layers in the model into INT4 format
        model = AutoModelForSpeechSeq2Seq.from_pretrained(model_path, load_in_4bit=True)
        model.config.forced_decoder_ids = None

        # Load processor
        processor = WhisperProcessor.from_pretrained(model_path)
        forced_decoder_ids = processor.get_decoder_prompt_ids(
            language=language, task="transcribe"
        )

        # Generate predicted tokens
        with torch.inference_mode():
            while True:
                # ! add exit flag
                audio_data = speech_to_text_queue.get()
                input_features = processor(
                    audio_data, sampling_rate=16000, return_tensors="pt"
                ).input_features
                st = time.time()
                # if your selected model is capable of utilizing previous key/value attentions
                # to enhance decoding speed, but has `"use_cache": false` in its model config,
                # it is important to set `use_cache=True` explicitly in the `generate` function
                # to obtain optimal performance with BigDL-LLM INT4 optimizations
                predicted_ids = model.generate(
                    input_features, forced_decoder_ids=forced_decoder_ids
                )
                end = time.time()
                output_str = processor.batch_decode(
                    predicted_ids, skip_special_tokens=True
                )
                print(f"Inference time: {end-st} s")
                print("-" * 20, "Output", "-" * 20)
                print(output_str)


if __name__ == "__main__":
    sound_recording = SoundRecording(threshold=-50)
    sound_recording.start()
    speech_to_text = SpeechToText()
    speech_to_text.start()
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            speech_to_text.terminate()
            break
