# make_data_set_so-vits-svc

make data set for so-vits-svc

## Language

go and python

go responsible for scraping data, python is responsible for preprocessing the data

## Function

go:

1. [x] Grab all the works of Kugou's personal homepage and store them scientifically locally
2. [x] Restore the file name that has been processed by UltimateVocalRemover
3. [x] Some utility functions such as getting the intersection of files in two folders and copying them into the other folders

python:

4. [x] Scientific segmentation of audio
5. [ ] Solve the problem of multiple speakers with the help of Alibaba Cloud DAMO Academy's speaker recognition model
6. [x] Have a human examine the dataset

## QA

The code for the dev branch is messy, don't expect too much until there is no main branch

## Copyright

The crawler itself does not have any copyright risk, and this project assumes that you have obtained written permission or that you are the author

If you've violated the copyright owner, remove content that you haven't authorized

## Law

依据现行的(2002年1月1日)《计算机软件保护条例》

>第十七条 为了学习和研究软件内含的设计思想和原理，通过安装、显示、传输或者存储软件等方式使用软件的，可以不经软件著作权人许可，不向其支付报酬。

来自大自然的馈赠

## 备注

目前代码已经成型了，我也使用它获得了用于音色迁移的音频数据集。

最近提交了fix pkl,`py/fix_pkl.py`,一个在pkl出问题时删除特定键的py脚本(当你希望重新审核某首歌的时候你需要将审核通过的片段删除并将pkl文件中这首歌的名字删除,以便重新审核它)。

这个工具目前来说,能用，但是不算好用,音频审核的ttk gui在所有歌曲干声审核完成之后会卡死,没有一个好的提示来表达审核完成。（判断审核完毕并设置退出flag的逻辑有点问题）

记录已审核歌曲的pkl文件里面没有记录审核过的片段,当初设计的时候可能是想要让其记录已经审核过的片段的,但是没能实现,只记录了歌曲。

总体来讲,这是一个需要你测试的项目,你把代码一股脑喂给AI,让其写一个你能理解的`根据酷狗音乐app的个人主页的/kmr/v1/audio_group/author接口返回的json下载音乐.然后你手动提取干声,然后它根据干声分割并提供一个审核界面供你审核音频片段,最后得到用于音色迁移训练的音频片段数据集`是没问题的,有代码参考AI可以更容易的工作,这些代码是起作用的,就是稍微有点乱,我也懒得整理了,新的AI项目等着我去完成

在`py/tts_test.py`还有一个具有音色迁移的tts，其实是先用DeepSeek（网页版逆向的接口）编写用于TTS的描述XML,这是一种用于改变语速、停顿的描述文本，没有也行。然后用Azure的tts服务生成语音，然后再调用训练好的音色迁移模型改变语音的音色。