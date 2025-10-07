import os
import gradio as gr
from openai import OpenAI
import azure.cognitiveservices.speech as speechsdk
import subprocess

"""运行此代码需要使用venv"""
"""运行此代码需要使用venv"""
"""运行此代码需要使用venv"""

# 配置API密钥
AZURE_SPEECH_KEY = ""
AZURE_SERVICE_REGION = "eastasia"

openai_client = OpenAI(api_key="123",base_url="http://127.0.0.1:5001/v1")

def generate_ssml(text):
    """使用LLM生成SSML"""
    try:
        response = openai_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "user", "content":f"""请根据待转语音的文本，编写适合微软Azure TTS引擎的SSML脚本。
要求使用晓辰语音`<voice name='zh-CN-XiaochenNeural'>`，要使语音更真实、更像人。

注意：只需要输出SSML代码，不要包含任何其他内容或解释。

下面是微软 SSML 文档的基本结构和语法的子集：
<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="string">
    <mstts:backgroundaudio src="string" volume="string" fadein="string" fadeout="string"/>
    <voice name="string" effect="string">
        <audio src="string"></audio>
        <bookmark mark="string"/>
        <break strength="string" time="string" />
        <emphasis level="value"></emphasis>
        <lang xml:lang="string"></lang>
        <lexicon uri="string"/>
        <math xmlns="http://www.w3.org/1998/Math/MathML"></math>
        <mstts:audioduration value="string"/>
        <mstts:ttsembedding speakerProfileId="string"></mstts:ttsembedding>
        <mstts:express-as style="string" styledegree="value" role="string"></mstts:express-as>
        <mstts:silence type="string" value="string"/>
        <mstts:viseme type="string"/>
        <p></p>
        <phoneme alphabet="string" ph="string"></phoneme>
        <prosody pitch="value" contour="value" range="value" rate="value" volume="value"></prosody>
        <s></s>
        <say-as interpret-as="string" format="string" detail="string"></say-as>
        <sub alias="string"></sub>
    </voice>
</speak>

下面是待转语音的文本：
{text}

务必确保输出的SSML完整！"""
            }
        ],
            stream=False
        )
        ssml = response.choices[0].message.content
        # 确保返回的是有效的SSML
        if "<speak" not in ssml:
            ssml = f"<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='zh-CN'><voice name='zh-CN-XiaochenNeural'>{text}</voice></speak>"
        return ssml
    except Exception as e:
        print(f"生成SSML时出错: {e}")
        return f"<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='zh-CN'><voice name='zh-CN-XiaochenNeural'>{text}</voice></speak>"

def text_to_speech(text):
    """使用Azure TTS将文本转换为语音"""
    try:
        # 生成SSML
        ssml = generate_ssml(text)
        print(f"生成的SSML: {ssml}")
        
        # 配置Azure语音服务
        speech_config = speechsdk.SpeechConfig(
            subscription=AZURE_SPEECH_KEY,
            region=AZURE_SERVICE_REGION
        )
        speech_config.speech_synthesis_voice_name = 'zh-CN-XiaochenNeural'
        
        # 使用临时文件保存音频
        # audio_file = "tts_output_audio.wav"
        audio_file = "raw/tts_output_audio.wav"
        audio_config = speechsdk.audio.AudioOutputConfig(filename=audio_file)
        
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config,
            audio_config=audio_config
        )
        
        # 使用SSML合成语音
        result = synthesizer.speak_ssml_async(ssml).get()
        
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            print("语音合成成功，开始转换音色")
            # inference_main.py 在 https://www.codewithgpu.com/i/svc-develop-team/so-vits-svc/so-vits-svc-4.1-Stable/376/14.3里面，依赖它（现在这个镜像已经有更高版本了，如果inference_main.py文件仍在且所需的命令行参数仍在，就可以用高版本）
            result = subprocess.run(
                [
                    "/root/miniconda3/bin/python",
                    "inference_main.py",
                    "-m", "logs/44k/G_15200.pth",
                    "-n", "tts_output_audio",
                    "-s", "dwy",
                    "-lg", "1",
                    "-f0p", "rmvpe",
                    "-lea", "0",
                    "-sd", "-50",
                    "-wf", "mp3"
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            print(result.stdout)

            return f"results/tts_output_audio_0key_dwy_sovits_rmvpe.mp3"
        else:
            cancellation = result.cancellation_details
            error_msg = f"语音合成失败: {cancellation.reason}"
            if cancellation.reason == speechsdk.CancellationReason.Error:
                error_msg += f"\n错误详情: {cancellation.error_details}"
            print(error_msg)
            return None
    except Exception as e:
        print(f"语音合成过程中出错: {e}")
        return None

# 创建Gradio界面
with gr.Blocks() as demo:
    gr.Markdown("# 文本转语音系统")
    gr.Markdown("输入文本，系统将使用DeepSeek生成SSML，然后通过Azure TTS转换为语音")
    
    with gr.Row():
        with gr.Column():
            input_text = gr.Textbox(label="输入文本", lines=5, placeholder="请输入要转换为语音的文本...")
            submit_btn = gr.Button("转换为语音")
        with gr.Column():
            audio_output = gr.Audio(label="生成的语音", type="filepath")
    
    submit_btn.click(
        fn=text_to_speech,
        inputs=input_text,
        outputs=audio_output
    )

# 运行应用
if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=6006)