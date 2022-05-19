import os
import sys
import shutil
import subprocess as sp

temp_category = "./temp_category/"
codec_category = "./codec_category/"

max_occupancy_size = 1 * 1024 * 1024

textEdit = ""

def findAllFile(category):
    for root, ds, fs in os.walk(category):
        for f in fs:
            yield f

def get_audio_duration(filename):
    cmd = "ffprobe -v error -show_entries stream=duration -of default=noprint_wrappers=1:nokey=1 -i %s" % filename
    p = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE)
    p.wait()
    strout, strerr = p.communicate() # 去掉最后的回车
    ret = strout.decode("utf-8").split("\n")[0]
    return ret

def get_audio_sample_rate(filename):
    cmd = "ffprobe -v error -show_entries stream=sample_rate -of default=noprint_wrappers=1:nokey=1 -i %s" % filename
    p = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE)
    p.wait()
    strout, strerr = p.communicate()
    ret = strout.decode("utf-8").split("\n")[0]
    return ret

def get_audio_channels(filename):
    cmd = "ffprobe -v error -show_entries stream=channels -of default=noprint_wrappers=1:nokey=1 -i %s" % filename
    p = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE)
    p.wait()
    strout, strerr = p.communicate()
    ret = strout.decode("utf-8").split("\n")[0]
    return ret

def calculation_audio_occupancy(path):
    duration = get_audio_duration(path)
    textEdit.appendPlainText("duration =" + duration)
    sample_rate = get_audio_sample_rate(path)
    textEdit.appendPlainText("sample_rate =" + sample_rate)
    channels = get_audio_channels(path)
    textEdit.appendPlainText("channels =" + channels)

    occupancy_size = float(duration) * int(sample_rate) * int(channels) * 16 / 8

    return occupancy_size, float(duration), int(sample_rate), int(channels)

def estimate_audio_sample_rate(filename, duration, sample_rate):
    max_sample_rate = max_occupancy_size * 8 / 16 // duration
    textEdit.appendPlainText("max_sample_rate =" + str(max_sample_rate))
    rates = [48000, 44100, 32000, 24000, 22050, 16000]
    i = rates.index(sample_rate)
    for x in range(i, len(rates)):
        if rates[x] < max_sample_rate:
            textEdit.appendPlainText("变更后比特率 =" + str(rates[x]))
            return rates[x]
        else:
            continue
    textEdit.appendPlainText("音频文件" + filename + "过大,请手动修改！")
    raise Exception("音频文件{}过大,请手动修改！".format(filename))

def change_audio_channels(filename):
    src_path = temp_category + filename
    dst_path = codec_category + filename
    cmd = "ffmpeg -i %s -ac 1 %s" %(src_path, dst_path)
    p = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE)
    p.wait()
    strout, strerr = p.communicate()

def change_audio_sample_rate(filename, sample_rate):
    src_path = temp_category + filename
    dst_path = codec_category + filename
    cmd = "ffmpeg -i %s -ac 1 -ar %d %s" %(src_path, sample_rate, dst_path)
    p = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE)
    p.wait()
    strout, strerr = p.communicate()

def clever_select_audio_parameter(filename, occupancy_size, duration, sample_rate, channels):
    if (occupancy_size / 2 < max_occupancy_size) and channels == 2:
        change_audio_channels(filename)
    else:
        usable_sample_rate = estimate_audio_sample_rate(filename, duration, sample_rate)
        change_audio_sample_rate(filename, usable_sample_rate)

def start_work(path, QPlainTextEdit):
    global textEdit
    textEdit = QPlainTextEdit
    QPlainTextEdit.setPlainText("开始处理音频文件！")

    if os.path.exists(temp_category):
        QPlainTextEdit.appendPlainText(temp_category + "文件夹存在")
        shutil.rmtree(temp_category)
    if os.path.exists(codec_category):
        QPlainTextEdit.appendPlainText(codec_category + "文件夹存在")
        shutil.rmtree(codec_category)
    
    os.makedirs(temp_category)
    os.makedirs(codec_category)
    
    for file_name in findAllFile(path):
        QPlainTextEdit.appendPlainText("开始处理:" + file_name)
        src_path = path + "/" + file_name
        temp_path = temp_category + file_name
        occupancy_size, duration, sample_rate, channels = calculation_audio_occupancy(src_path)
        if occupancy_size > max_occupancy_size:
            shutil.copyfile(src_path, temp_path)
            clever_select_audio_parameter(file_name, occupancy_size, duration, sample_rate, channels)
        else:
            continue

    QPlainTextEdit.appendPlainText("音频文件处理完成!")