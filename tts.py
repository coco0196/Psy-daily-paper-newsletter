import os
import json
from datetime import datetime
import edge_tts
import asyncio
import argparse
from utils import get_logger, get_last_week_range, weekly_basename

logger = get_logger()

async def generate_audio(text, output_path):
    """使用 Edge TTS 生成语音"""
    try:
        voice = "zh-CN-XiaoxiaoNeural"
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)
        return True
    except Exception as e:
        logger.error(f"生成语音时出错：{str(e)}")
        return False

async def generate_weekly_paper_audio(start_date=None, end_date=None, weekly_key=None):
    """为指定周报生成语音播报"""
    if not weekly_key:
        if not start_date or not end_date:
            start_date, end_date = get_last_week_range()
        weekly_key = weekly_basename(start_date, end_date)
    elif not start_date or not end_date:
        if "_to_" in weekly_key:
            start_date, end_date = weekly_key.split("_to_", 1)
        else:
            start_date, end_date = get_last_week_range()

    date_range = f"{start_date} 至 {end_date}"

    audio_dir = 'audio'
    os.makedirs(audio_dir, exist_ok=True)

    json_file = os.path.join('Psy-day-paper-deepseek', f"{weekly_key}_Psy_deepseek_clean.json")
    if not os.path.exists(json_file):
        logger.error(f"未找到 {weekly_key} 的论文数据文件")
        return False

    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            papers = json.load(f)

        if not isinstance(papers, list) or len(papers) == 0:
            logger.info(f"{date_range} 没有论文数据，跳过生成语音")
            return False

        script = f"欢迎收听心理学论文周报，本期时间为{date_range}。本周为您带来{len(papers)}篇论文解读。\n\n"

        has_valid_content = False
        for i, paper in enumerate(papers, 1):
            translation = paper.get('translation', '')
            if '标题：' in translation and '摘要：' in translation:
                title = translation.split('标题：')[1].split('\n')[0]
                summary = translation.split('摘要：')[1].strip()
                script += f"第{i}篇论文：{title}\n{summary}\n\n"
                has_valid_content = True

        if not has_valid_content:
            logger.warning("没有找到有效的论文内容，跳过生成语音")
            return False

        script += "感谢收听，我们下周再会。"

        output_path = os.path.join(audio_dir, f"{weekly_key}_weekly_papers.mp3")
        success = await generate_audio(script, output_path)

        if success:
            logger.info(f"语音文件已生成：{output_path}")
            return True
        logger.error("生成语音文件失败")
        return False

    except Exception as e:
        logger.error(f"生成语音播报时出错：{str(e)}")
        return False


# 兼容旧调用名
generate_daily_paper_audio = generate_weekly_paper_audio

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='生成心理学论文周报语音播报')
    parser.add_argument('--start-date', type=str, help='周报起始日期 (YYYY-MM-DD格式)')
    parser.add_argument('--end-date', type=str, help='周报结束日期 (YYYY-MM-DD格式)')
    parser.add_argument('--weekly-key', type=str, help='周报文件基名，如 2026-05-26_to_2026-06-01')
    args = parser.parse_args()

    success = asyncio.run(generate_weekly_paper_audio(
        start_date=args.start_date,
        end_date=args.end_date,
        weekly_key=args.weekly_key,
    ))
    if not success:
        exit(1)
    exit(0)
