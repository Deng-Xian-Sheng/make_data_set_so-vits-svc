# Copyright (c) [2023] [JinCanQi]
# [make_data_set_so-vits-svc] is licensed under Mulan PubL v2.
# You can use this software according to the terms and conditions of the Mulan PubL v2.
# You may obtain a copy of Mulan PubL v2 at:
#          http://license.coscl.org.cn/MulanPubL-2.0
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PubL v2 for more details.

import os
import pickle
from pydub import AudioSegment
from pydub.silence import split_on_silence
from pydub.effects import compress_dynamic_range
import librosa
from multiprocessing import Process, Manager, Queue, Pipe
import numpy as np
import tkinter as tk
from tkinter import ttk
import atexit
import pyaudio
import ctypes


# AUDIO_FORMAT 音频文件格式
AUDIO_FORMAT: str = "mp3"

# 要求时长 ms
MIN_DURATION: int = 5 * 1000
MAX_DURATION: int = 15 * 1000

# SILENCE_THRESH 静默阈值 dBFS 程序会动态赋值
SILENCE_THRESH: int = -20

# MIN_SILENCE_LEN 无声片段最小长度 ms 1000ms为1s 程序会动态赋值
MIN_SILENCE_LEN: int = 1000

# KEEP_SILENCE 分割后，是否在片段的开头和结尾保留一些低于静默阈值的声音，以防止声音突然截断，这可以使声音更自然，可选值 bool || int
# false为不保留，true为全部保留，int为保留的时间 ms，默认500ms
KEEP_SILENCE: int = 500

# SEEK_STEP 在检测到静默后从非静默点向前搜索的持续时间。这在音频中有少量噪音或音损的情况下或许有用。较大的 SEEK_STEP 可能有助于缓解此类噪音
# 默认 1ms
# 用于指定在寻找下一个静默部分时音频文件的跳跃步长。
# seek_step参数指定了每次跳跃的时间长度，单位为毫秒。
# 如果您需要更快的处理速度，可以将seek_step设置为更大的值。
# 但是，如果您将seek_step设置得太大，可能会导致分割不准确。
SEEK_STEP: int = 1

# 淡入淡出时间 ms
FADE_TIME: int = 500

# 压缩器参数
compress_dynamic_range_params: dict = {
    "threshold": -10,
    "ratio": 2,
    "attack": 30,
    "release": 300,
}

AUDIO_DIR = "../data/source/c/"
OUTPUT_DIR = "../data/out/kugou/"

# 队列放10首歌，已经很大了，因为很占内存
GUI_to_thread_queue = Queue(maxsize=10)
thread_to_GUI_queue = Queue(maxsize=10)

GUI_to_audio_play_data_queue = Queue(maxsize=1)

GUI_to_audio_play_control_queue = Queue(maxsize=1)
audio_play_to_GUI_control_queue = Queue(maxsize=1)

GUI_to_audio_play_scale_queue1, GUI_to_audio_play_scale_queue2 = Pipe()
audio_play_to_GUI_scale_queue1, audio_play_to_GUI_scale_queue2 = Pipe()

local_data_exit_flag = Manager().Value(ctypes.c_bool, False)
local_data_file_list = Manager().list()

local_data_processd_audio = Manager().dict()
PROCESSD_AUDIO_FILE = os.path.join(OUTPUT_DIR, "process_audio.pkl")


def split_segment(segment: AudioSegment) -> list:
    """
    通过淡入淡出将某个音频片段再次分割

    :param segment: 音频片段
    :type segment: pydub.AudioSegment
    :return: 分割后的音频片段列表
    :rtype: list[pydub.AudioSegment]
    """

    # 获取总时长 ms
    duration: int = len(segment)

    # 片段数 = 总时长 / MAX_DURATION
    block_number: int = int(duration / MAX_DURATION)

    # 每个的时长 = 总时长 / 片段数 此处向下取整，余数的时长就被抛弃了，所以后面我们判断是最后一个片段则该片段一直持续到最后
    duration_one: int = int(duration / block_number)

    # 分割后的音频片段
    segments: list[AudioSegment] = []

    # 遍历分割
    for i in range(0, block_number):
        # 起始位置
        start = i * duration_one

        # 结束位置
        if i == block_number - 1:
            # 最后一个片段
            end = duration
        else:
            # 非最后一个片段
            end = start + duration_one

        # 淡入淡出
        segment_fade = segment[start:end].fade_in(FADE_TIME).fade_out(FADE_TIME)  # type: ignore

        # 添加到分割后的音频片段
        segments.append(segment_fade)

    return segments


def merge_segment(segment1: AudioSegment, segment2: AudioSegment) -> AudioSegment:
    """
    合并两个音频片段

    :param segment1: 音频片段1
    :type segment1: pydub.AudioSegment
    :param segment2: 音频片段2
    :type segment2: pydub.AudioSegment
    :return: 合并后的音频片段
    :rtype: pydub.AudioSegment
    """
    return segment1 + segment2


def process(file_path: str) -> list:
    """
    分割音频，返回处理后的数据

    :param file_path: 文件路径
    :return: 处理后的数据
    :rtype: list[pydub.AudioSegment]
    :type file_path: str
    """
    sound: AudioSegment = AudioSegment.from_file(file_path, format=AUDIO_FORMAT)
    sound: AudioSegment = compress_dynamic_range(sound, **compress_dynamic_range_params)
    SILENCE_THRESH = int(-abs(sound.dBFS) * 1.5)

    # 获取节拍
    tempo, _ = librosa.beat.beat_track(
        y=np.array(sound.get_array_of_samples(), dtype=np.float32), sr=sound.frame_rate
    )

    # 根据BPM动态调整静默长度
    if tempo <= 100:
        # 节奏较慢，静默长度可以设置得更长
        MIN_SILENCE_LEN = int(1.5 * 1000)
    elif 100 < tempo <= 120:
        # 中等节奏，静默长度适中
        MIN_SILENCE_LEN = int(1.0 * 1000)
    else:
        # 节奏较快，静默长度更短
        MIN_SILENCE_LEN = int(0.5 * 1000)

    audio_chunks = split_on_silence(
        sound,
        min_silence_len=MIN_SILENCE_LEN,  # type: ignore
        silence_thresh=SILENCE_THRESH,
        keep_silence=KEEP_SILENCE,
        seek_step=SEEK_STEP,
    )

    # 遍历音频片段
    i = 0
    while i < len(audio_chunks):
        # 时长 ms
        duration = int(audio_chunks[i].duration_seconds * 1000)  # type: ignore

        # 严格时长约束
        if duration > MAX_DURATION:
            # 抹除当前值
            in_split_segment = audio_chunks.pop(i)

            # 使用 split_segment() 再次分割，抹除当前值并把分割后的值追加到当前值的下一个值
            out_split_segment = split_segment(in_split_segment)  # type: ignore

            for ii, vv in enumerate(out_split_segment):
                audio_chunks.insert(i + ii, vv)

        if duration < MIN_DURATION:
            # 抹除当前值
            in_merge_segment = audio_chunks.pop(i)

            # 不是最后一个值则抹除下一个值
            if i < len(audio_chunks):
                in2_merge_segment = audio_chunks.pop(i)

                # 将当前和下一个合并
                out_merge_segment = merge_segment(in_merge_segment, in2_merge_segment)  # type: ignore

                # 将合并后的值插入到当前值的位置
                audio_chunks.insert(i, out_merge_segment)
        i += 1
    return audio_chunks


# 遍历目录下的文件，返回文件路径列表
def walk_dir(dir_path: str):
    """
    遍历目录下的文件，返回文件路径列表

    :param dir_path: 目录路径
    :type dir_path: str
    :return: 文件路径列表
    :rtype: list[str]
    """
    file_paths: list[str] = []

    for root, dirs, files in os.walk(dir_path):
        for file in files:
            # 判断后缀是否为 AUDIO_FORMAT
            if os.path.splitext(file)[1] == "." + AUDIO_FORMAT:
                file_paths.append(os.path.join(root, file))
    return file_paths


class AudioReviewInterface:
    def __init__(self):
        self.root = tk.Tk()

        # 绑定窗口关闭事件处理器
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # 设置大小
        self.root.geometry("500x200")

        self.audio_list = []
        self.audio_name = ""
        self.current_index = 0
        self.result_dict = {}

        self.root.title(self.audio_name)

        self.play_button = ttk.Button(self.root, text="Play", command=self.play_audio)
        self.play_button.pack()

        self.pause_button = ttk.Button(
            self.root, text="Pause", command=self.pause_audio
        )
        self.pause_button.pack()
        self.pause_button.config(state=tk.DISABLED)

        self.scale = ttk.Scale(
            self.root,
            from_=0,
            to=10000,
            orient=tk.HORIZONTAL,
        )
        self.scale.pack(fill="x")
        self.scale.bind("<B1-Motion>", self.to_audio_play_scale_queue)

        self.yes_button = ttk.Button(self.root, text="Yes", command=self.yes_action)
        self.yes_button.pack()

        self.no_button = ttk.Button(self.root, text="No", command=self.no_action)
        self.no_button.pack()

        self.prev_button = ttk.Button(self.root, text="Back", command=self.prev_audio)
        self.prev_button.pack()

        self.next_button = ttk.Button(self.root, text="Next", command=self.next_audio)
        self.next_button.pack()

        self.audio_length_label = ttk.Label(self.root, text="")
        self.audio_length_label.pack()

        self.audio_index_label = ttk.Label(self.root, text="")
        self.audio_index_label.pack()

        self.next_audio()

    def play_audio(self):
        self.play_button.config(state=tk.DISABLED)
        self.pause_button.config(state=tk.NORMAL)
        GUI_to_audio_play_control_queue.put(True)

    def pause_audio(self):
        self.play_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED)
        GUI_to_audio_play_control_queue.put(False)

    def yes_action(self):
        self.result_dict[self.current_index] = "Yes"
        self.next_audio()

    def no_action(self):
        self.result_dict[self.current_index] = "No"
        self.next_audio()

    def prev_audio(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.update_labels()
            self.update_action()
            GUI_to_audio_play_data_queue.put(self.audio_list[self.current_index])
            self.play_audio()

    def next_audio(self):
        if self.current_index < len(self.audio_list) - 1:
            self.current_index += 1
            self.update_labels()
            self.update_action()
        else:
            if len(self.audio_list) != 0:
                GUI_to_thread_queue.put(
                    {
                        "audio_slice": self.audio_list,
                        "result_dict": self.result_dict,
                        "audio_name": self.audio_name,
                    }
                )
            dict = thread_to_GUI_queue.get()
            self.audio_list = dict["audio_list"]
            self.audio_name = dict["audio_name"]
            self.current_index = 0
            self.result_dict = {}
            self.root.title(self.audio_name)
            self.update_labels()
        GUI_to_audio_play_data_queue.put(self.audio_list[self.current_index])
        self.play_audio()

    def update_from_audio_play(self):
        """从 AudioPlay 获取更新并应用到 GUI"""
        # 处理播放控制更新
        if not audio_play_to_GUI_control_queue.empty():
            control = audio_play_to_GUI_control_queue.get()
            if control:
                self.play_button.config(state=tk.DISABLED)
                self.pause_button.config(state=tk.NORMAL)
            else:
                self.play_button.config(state=tk.NORMAL)
                self.pause_button.config(state=tk.DISABLED)

        # 处理播放进度更新
        if audio_play_to_GUI_scale_queue2.poll():
            progress = audio_play_to_GUI_scale_queue2.recv()
            self.scale.set(progress)

    # 修改 mainloop 方法
    def mainloop(self):
        """重写 mainloop 方法以包含定时检查"""
        while True:
            if local_data_exit_flag.get():
                self.root.destroy()
                break

            self.root.update_idletasks()
            self.root.update()
            self.update_from_audio_play()

    def to_audio_play_scale_queue(self, event):
        GUI_to_audio_play_scale_queue1.send(self.scale.get())

    def on_close(self):
        """
        当用户点击窗口关闭按钮时调用
        """
        # 设置退出标志
        local_data_exit_flag.set(True)

    def update_action(self):
        # 判断当前音频是否选择Yes或者No
        # 如果未选择则不做操作，否则将按钮设为选择的值
        if self.current_index in self.result_dict:
            if self.result_dict[self.current_index] == "Yes":
                self.yes_button.config(state=tk.DISABLED)
                self.no_button.config(state=tk.ACTIVE)
            elif self.result_dict[self.current_index] == "No":
                self.yes_button.config(state=tk.ACTIVE)
                self.no_button.config(state=tk.DISABLED)
        else:
            self.yes_button.config(state=tk.ACTIVE)
            self.no_button.config(state=tk.ACTIVE)

    def update_labels(self):
        self.audio_length_label.config(
            text=f"duration: {len(self.audio_list[self.current_index]) / 1000} second"
        )
        self.audio_index_label.config(
            text=f"article {self.current_index + 1} / of {len(self.audio_list)}"
        )


class ProcessThreadToGUI(Process):
    def run(self) -> None:
        file_list = walk_dir(AUDIO_DIR)

        for file in file_list:
            local_data_file_list.append(file)

        for file in file_list:
            if local_data_exit_flag.get():
                break

            audio_name = os.path.splitext(os.path.basename(file))[0]

            # 检查当前音频是否已经处理过
            if audio_name in local_data_processd_audio:
                continue  # 如果已处理，则跳过

            audio_slice = process(file)
            thread_to_GUI_queue.put(
                {
                    "audio_list": audio_slice,
                    "audio_name": audio_name,
                }
            )


class GUIToProcessThread(Process):
    def run(self) -> None:
        while True:
            if local_data_exit_flag.get():
                break
            dict = GUI_to_thread_queue.get()
            audio_slice = dict["audio_slice"]
            result_dict = dict["result_dict"]
            audio_name = dict["audio_name"]
            # 处理片段并写入文件
            for i, segment in enumerate(audio_slice):
                if i in result_dict and result_dict[i] == "Yes":
                    output_file = os.path.join(
                        OUTPUT_DIR, f"{audio_name}_{i}.{AUDIO_FORMAT}"
                    )
                    segment.export(output_file, format=AUDIO_FORMAT)

                    # 更新 local_data_processd_audio 字典
                    if audio_name not in local_data_processd_audio:
                        local_data_processd_audio[audio_name] = []
                    local_data_processd_audio[audio_name].append(output_file)

            # 判断audio_name是local_data_file_list最后一个
            if (
                audio_name
                == os.path.splitext(os.path.basename(local_data_file_list[-1]))[0]
            ):
                # 退出
                local_data_exit_flag.set(True)


# 使用pyaudio回调模式播放音频
class AudioPlay(Process):
    def defer(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)  # type: ignore

            if GUI_to_audio_play_scale_queue2.poll():
                scale = GUI_to_audio_play_scale_queue2.recv()
                if float(scale) != 0.0:
                    new_play_progress = int(
                        (
                            (float(scale) / 10000.0)
                            * (args[0].segment_frame_count / args[2])
                        )
                        * args[2]
                    )
                    if new_play_progress >= args[0].play_progress:
                        args[0].play_progress = new_play_progress + args[2]
                    else:
                        args[0].play_progress = new_play_progress - args[2]
                else:
                    args[0].play_progress = 0

            elif args[0].control:
                # 自增播放进度
                args[0].play_progress = args[0].play_progress + args[2]

                audio_play_to_GUI_scale_queue1.send(
                    int(
                        (
                            (args[0].play_progress / args[2])
                            / (args[0].segment_frame_count / args[2])
                        )
                        * 10000.0
                    )
                )

            return result

        return wrapper

    @defer  # type: ignore
    def callback(self, in_data, frame_count, time_info, status):
        if not GUI_to_audio_play_control_queue.empty():
            self.control = GUI_to_audio_play_control_queue.get()

        # 如果播放控制为暂停，则返回静默数据
        if not self.control and not GUI_to_audio_play_scale_queue2.poll():
            silent_data = self.generate_silence(frame_count)
            return (silent_data, pyaudio.paContinue)

        # 播放音频数据
        end = min(self.play_progress + frame_count, self.segment_frame_count)  # type: ignore
        data = self.audio_segment.get_sample_slice(self.play_progress, end).raw_data

        # 检查是否需要补足静默数据
        if len(data) < frame_count * self.audio_segment.frame_width:  # type: ignore
            remaining_frames = frame_count - len(data) // self.audio_segment.frame_width  # type: ignore
            silent_data = self.generate_silence(remaining_frames)
            data += silent_data
            # 重置播放暂停控制
            self.control = False
            audio_play_to_GUI_control_queue.put(self.control)
            # 重置播放进度（样本帧数）
            self.play_progress = 0
            audio_play_to_GUI_scale_queue1.send(0)

        return (data, pyaudio.paContinue)

    def generate_silence(self, frame_count):
        """生成指定长度的静默数据"""
        return b"\x00" * frame_count * self.audio_segment.frame_width

    def run(self) -> None:
        self.p = pyaudio.PyAudio()
        self.stream = None  # type: ignore

        # 声明AudioSegment音频对象
        self.audio_segment = None  # type: ignore
        # 声明播放进度（样本帧数）
        self.play_progress = 0
        # 声明播放暂停控制
        self.control = False
        # 声明总样本帧数
        self.segment_frame_count = None

        while True:
            if local_data_exit_flag.get():
                if self.stream is not None:
                    self.stream.close()  # type: ignore
                self.p.terminate()
                break

            if not GUI_to_audio_play_data_queue.empty() or self.audio_segment is None:
                if self.stream is not None:
                    self.stream.close()  # type: ignore

                if self.audio_segment is not None:
                    # 重置播放暂停控制
                    self.control = False
                    # 重置播放进度（样本帧数）
                    self.play_progress = 0
                    # 重置总样本帧数
                    self.segment_frame_count = None

                self.audio_segment: AudioSegment = GUI_to_audio_play_data_queue.get()

                self.segment_frame_count = int(self.audio_segment.frame_count())

                self.stream: pyaudio._Stream = self.p.open(
                    format=self.p.get_format_from_width(
                        self.audio_segment.sample_width
                    ),
                    channels=self.audio_segment.channels,
                    rate=self.audio_segment.frame_rate,
                    output=True,
                    stream_callback=self.callback,
                )


def save_data(filename, data):
    """将数据保存到指定的文件"""
    # 首先将管理字典转换为普通字典
    normal_dict = dict(data)
    # 然后使用pickle保存
    with open(filename, "wb") as file:
        pickle.dump(normal_dict, file)


def load_data(filename, managed_dict):
    """从指定文件加载数据到管理字典"""
    # 从文件中加载普通字典
    with open(filename, "rb") as file:
        normal_dict = pickle.load(file)
    # 将普通字典转换为管理字典
    for key, value in normal_dict.items():
        managed_dict[key] = value
    return managed_dict


def exit_handler():
    # 将字典保存到文件
    save_data(PROCESSD_AUDIO_FILE, local_data_processd_audio)


if __name__ == "__main__":
    if os.path.exists(PROCESSD_AUDIO_FILE):
        load_data(PROCESSD_AUDIO_FILE, local_data_processd_audio)

    # atexit.register(exit_handler)

    # GUIToProcessThread().start()

    AudioPlay().start()

    # ProcessThreadToGUI().start()

    thread_to_GUI_queue.put(
        {
            "audio_list": [
                AudioSegment.from_file(
                    "../data/Govi - Romance Dance.mp3", format=AUDIO_FORMAT
                )
            ],
            "audio_name": "Govi - Romance Dance",
        }
    )

    AudioReviewInterface().mainloop()
