from pydub import AudioSegment


def cut_and_convert_audio(input_path, output_path, start_sec, end_sec):
    """
    裁剪音频并转换格式
    :param input_path: 输入m4a文件路径（如：./input.m4a）
    :param output_path: 输出mp3文件路径（如：./output.mp3）
    :param start_sec: 起始时间（秒），默认1秒
    :param end_sec: 结束时间（秒），默认2秒
    """
    try:
        # 1. 加载m4a音频文件（pydub默认按毫秒处理，需转换）
        audio = AudioSegment.from_file(input_path, format="m4a")

        # 2. 转换时间单位：秒 -> 毫秒
        start_ms = start_sec * 1000
        end_ms = end_sec * 1000

        # 3. 裁剪音频（只保留1-2秒的片段）
        cut_audio = audio[start_ms:end_ms]

        # 4. 导出为mp3格式（设置比特率保证音质）
        cut_audio.export(output_path, format="mp3", bitrate="128k")

        print(f"音频裁剪转换完成！输出文件：{output_path}")

    except FileNotFoundError:
        print(f"错误：找不到输入文件 {input_path}")
    except Exception as e:
        print(f"处理失败：{str(e)}")


# 调用示例
if __name__ == "__main__":
    # 替换为你的输入/输出文件路径
    input_m4a = r"D:\Users\33659\Documents\WeChat Files\wxid_26oalpoh10gt22\FileStorage\File\2026-02\2026年02月22日 21点32分.m4a" # 源m4a文件路径
    output_mp3 = "lose.mp3"  # 输出mp3文件路径
    cut_and_convert_audio(input_m4a, output_mp3, start_sec=1, end_sec=9.5)