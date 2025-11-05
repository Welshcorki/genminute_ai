import sqlite3
from collections import defaultdict
import os

basedir = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(basedir, "..", "database", "minute_ai.db")

def calculate_speaker_share(meeting_id):
    """특정 회의의 화자별 발언 점유율을 계산합니다 (글자 수 기반)."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT speaker_label, segment FROM meeting_dialogues WHERE meeting_id = ?", (meeting_id,))
            rows = cursor.fetchall()

        if not rows:
            return None

        speaker_text_lengths = defaultdict(int)
        total_length = 0

        for row in rows:
            speaker = row['speaker_label']
            text = row['segment'] if row['segment'] is not None else ""
            text_length = len(text)
            speaker_text_lengths[speaker] += text_length
            total_length += text_length

        if total_length == 0:
            return None

        speaker_percentages = {speaker: (length / total_length) * 100 for speaker, length in speaker_text_lengths.items()}
        sorted_speakers = sorted(speaker_percentages.items(), key=lambda item: item[1], reverse=True)

        chart_data = {
            "labels": [item[0] for item in sorted_speakers],
            "data": [round(item[1], 2) for item in sorted_speakers]
        }

        return chart_data

    except Exception as e:
        print(f"Error in calculate_speaker_share: {e}")
        return None
