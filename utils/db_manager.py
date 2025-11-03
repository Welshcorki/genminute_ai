
import sqlite3
import uuid
import datetime

class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def save_stt_to_db(self, segments, audio_filename, title, meeting_date=None):
        """
        음성 인식 결과를 데이터베이스에 저장합니다.

        Args:
            segments (list): 음성 인식 결과 세그먼트 리스트
            audio_filename (str): 오디오 파일명
            title (str): 회의 제목
            meeting_date (str, optional): 회의 일시 (형식: "YYYY-MM-DD HH:MM:SS")
                                          제공되지 않으면 현재 시간 사용

        Returns:
            str: 생성된 meeting_id
        """
        meeting_id = str(uuid.uuid4())

        # meeting_date가 제공되지 않으면 현재 시간 사용
        if meeting_date is None:
            meeting_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = self._get_connection()
        cursor = conn.cursor()
        for segment in segments:
            cursor.execute("""
                INSERT INTO meeting_dialogues
                (meeting_id, meeting_date, speaker_label, start_time, segment, confidence, audio_file, title)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                meeting_id, meeting_date, str(segment['speaker']), segment['start_time'],
                segment['text'], segment['confidence'], audio_filename, title
            ))
        conn.commit()
        conn.close()
        print(f"✅ DB 저장 완료: meeting_id={meeting_id}, meeting_date={meeting_date}")
        return meeting_id

    def get_meeting_by_id(self, meeting_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM meeting_dialogues WHERE meeting_id = ? ORDER BY start_time ASC", (meeting_id,))
        rows = cursor.fetchall()
        conn.close()
        return rows

    def get_all_meetings(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT meeting_id, title, MAX(meeting_date) as date 
            FROM meeting_dialogues 
            GROUP BY meeting_id 
            ORDER BY date DESC
        """)
        meetings = cursor.fetchall()
        conn.close()
        return meetings

    def get_segments_by_meeting_id(self, meeting_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM meeting_dialogues WHERE meeting_id = ? ORDER BY start_time ASC", (meeting_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def save_minutes(self, meeting_id, title, meeting_date, minutes_content):
        """
        생성된 회의록을 데이터베이스에 저장합니다.

        Args:
            meeting_id (str): 회의 ID
            title (str): 회의 제목
            meeting_date (str): 회의 일시
            minutes_content (str): 회의록 내용 (마크다운 형식)

        Returns:
            bool: 저장 성공 여부
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # meeting_minutes 테이블이 없으면 생성
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meeting_minutes (
                meeting_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                meeting_date TEXT NOT NULL,
                minutes_content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 기존 회의록이 있는지 확인
        cursor.execute("SELECT meeting_id FROM meeting_minutes WHERE meeting_id = ?", (meeting_id,))
        existing = cursor.fetchone()

        if existing:
            # 기존 회의록 업데이트
            cursor.execute("""
                UPDATE meeting_minutes
                SET title = ?, meeting_date = ?, minutes_content = ?, updated_at = ?
                WHERE meeting_id = ?
            """, (title, meeting_date, minutes_content, created_at, meeting_id))
            print(f"✅ 회의록 업데이트 완료: meeting_id={meeting_id}")
        else:
            # 새 회의록 저장
            cursor.execute("""
                INSERT INTO meeting_minutes (meeting_id, title, meeting_date, minutes_content, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (meeting_id, title, meeting_date, minutes_content, created_at, created_at))
            print(f"✅ 회의록 저장 완료: meeting_id={meeting_id}")

        conn.commit()
        conn.close()
        return True

    def get_minutes_by_meeting_id(self, meeting_id):
        """
        meeting_id로 저장된 회의록을 조회합니다.

        Args:
            meeting_id (str): 회의 ID

        Returns:
            dict or None: 회의록 정보 (meeting_id, title, meeting_date, minutes_content, created_at, updated_at)
                          없으면 None 반환
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # meeting_minutes 테이블이 없으면 None 반환
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='meeting_minutes'")
        if not cursor.fetchone():
            conn.close()
            return None

        cursor.execute("""
            SELECT meeting_id, title, meeting_date, minutes_content, created_at, updated_at
            FROM meeting_minutes
            WHERE meeting_id = ?
        """, (meeting_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def delete_meeting_data(self, meeting_id=None, audio_file=None, title=None):
        """
        지정된 조건에 따라 회의 데이터를 삭제합니다.
        경고: 아무 조건도 주어지지 않으면 테이블의 모든 데이터가 삭제됩니다.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        query = "DELETE FROM meeting_dialogues"
        conditions = []
        params = []

        if meeting_id:
            conditions.append("meeting_id = ?")
            params.append(meeting_id)
        if audio_file:
            conditions.append("audio_file = ?")
            params.append(audio_file)
        if title:
            conditions.append("title = ?")
            params.append(title)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        cursor.execute(query, tuple(params))
        deleted_rows = cursor.rowcount
        conn.commit()
        conn.close()

        print(f"✅ DB 삭제 완료: {deleted_rows}개 행 삭제됨")
        return deleted_rows
