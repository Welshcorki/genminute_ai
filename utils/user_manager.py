"""
사용자 관리 모듈
- users 테이블 CRUD
- 권한 확인 (admin/user)
- 공유 권한 관리
"""

import os
import sqlite3
from typing import Optional, Dict, List
from dotenv import load_dotenv

load_dotenv()

DB_PATH = "database/minute_ai.db"


def get_db_connection():
    """데이터베이스 연결"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 딕셔너리처럼 사용 가능
    return conn


def get_or_create_user(google_id: str, email: str, name: str = None, profile_picture: str = None) -> Dict:
    """
    사용자 조회 또는 생성

    Args:
        google_id: Firebase UID
        email: 이메일
        name: 이름
        profile_picture: 프로필 사진 URL

    Returns:
        사용자 정보 딕셔너리
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 1. google_id로 기존 사용자 조회
        cursor.execute("SELECT * FROM users WHERE google_id = ?", (google_id,))
        user = cursor.fetchone()

        if user:
            # 기존 사용자 정보 업데이트 (이름, 프로필 사진)
            cursor.execute("""
                UPDATE users
                SET name = ?, profile_picture = ?
                WHERE google_id = ?
            """, (name, profile_picture, google_id))
            conn.commit()

            return dict(user)

        # 2. email로 기존 사용자 조회 (migrate 시 생성된 더미 계정)
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()

        if user:
            # 더미 계정의 google_id를 실제 Firebase UID로 업데이트
            cursor.execute("""
                UPDATE users
                SET google_id = ?, name = ?, profile_picture = ?
                WHERE email = ?
            """, (google_id, name, profile_picture, email))
            conn.commit()

            print(f"✅ 기존 사용자 업데이트: {email} (google_id 갱신)")

            # 업데이트된 사용자 정보 반환
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            updated_user = cursor.fetchone()
            return dict(updated_user)

        # 3. 신규 사용자 생성
        # 환경변수에서 admin 이메일 목록 확인
        admin_emails = os.getenv('ADMIN_EMAILS', '').split(',')
        admin_emails = [e.strip() for e in admin_emails if e.strip()]
        role = 'admin' if email in admin_emails else 'user'

        cursor.execute("""
            INSERT INTO users (google_id, email, name, profile_picture, role)
            VALUES (?, ?, ?, ?, ?)
        """, (google_id, email, name, profile_picture, role))
        conn.commit()

        user_id = cursor.lastrowid

        print(f"✅ 신규 사용자 생성: {email} (role: {role})")

        return {
            'id': user_id,
            'google_id': google_id,
            'email': email,
            'name': name,
            'profile_picture': profile_picture,
            'role': role
        }

    finally:
        conn.close()


def get_user_by_id(user_id: int) -> Optional[Dict]:
    """사용자 ID로 조회"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        return dict(user) if user else None
    finally:
        conn.close()


def get_user_by_email(email: str) -> Optional[Dict]:
    """이메일로 사용자 조회"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        return dict(user) if user else None
    finally:
        conn.close()


def is_admin(user_id: int) -> bool:
    """사용자가 admin인지 확인"""
    user = get_user_by_id(user_id)
    return user and user['role'] == 'admin'


def can_access_meeting(user_id: int, meeting_id: str) -> bool:
    """
    사용자가 해당 회의에 접근 권한이 있는지 확인

    조건:
    1. 본인이 생성한 노트
    2. admin 권한
    3. 공유받은 노트
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 1. Admin 체크
        if is_admin(user_id):
            return True

        # 2. 본인이 생성한 노트 체크 (meeting_dialogues 기준)
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM meeting_dialogues
            WHERE meeting_id = ? AND owner_id = ?
        """, (meeting_id, user_id))
        result = cursor.fetchone()
        if result and result['count'] > 0:
            return True

        # 3. 공유받은 노트 체크
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM meeting_shares
            WHERE meeting_id = ? AND shared_with_user_id = ?
        """, (meeting_id, user_id))
        result = cursor.fetchone()
        if result and result['count'] > 0:
            return True

        return False

    finally:
        conn.close()


def get_user_meetings(user_id: int) -> List[Dict]:
    """
    사용자가 접근 가능한 모든 회의 목록 조회

    조건:
    - Admin: 모든 노트
    - User: 본인이 생성한 노트 + 공유받은 노트
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        if is_admin(user_id):
            # Admin: 모든 노트 (meeting_dialogues에서 고유한 meeting_id 조회)
            cursor.execute("""
                SELECT
                    meeting_id,
                    title,
                    MAX(meeting_date) as meeting_date,
                    (SELECT audio_file FROM meeting_dialogues WHERE meeting_id = md.meeting_id LIMIT 1) as audio_file,
                    (SELECT owner_id FROM meeting_dialogues WHERE meeting_id = md.meeting_id LIMIT 1) as owner_id
                FROM meeting_dialogues md
                GROUP BY meeting_id
                ORDER BY meeting_date DESC
            """)
        else:
            # User: 본인 노트 + 공유받은 노트
            cursor.execute("""
                SELECT DISTINCT
                    md.meeting_id,
                    md.title,
                    MAX(md.meeting_date) as meeting_date,
                    (SELECT audio_file FROM meeting_dialogues WHERE meeting_id = md.meeting_id LIMIT 1) as audio_file,
                    (SELECT owner_id FROM meeting_dialogues WHERE meeting_id = md.meeting_id LIMIT 1) as owner_id,
                    CASE
                        WHEN (SELECT owner_id FROM meeting_dialogues WHERE meeting_id = md.meeting_id LIMIT 1) = ? THEN 'owner'
                        ELSE 'shared'
                    END as access_type
                FROM meeting_dialogues md
                LEFT JOIN meeting_shares s ON md.meeting_id = s.meeting_id
                WHERE (SELECT owner_id FROM meeting_dialogues WHERE meeting_id = md.meeting_id LIMIT 1) = ?
                   OR s.shared_with_user_id = ?
                GROUP BY md.meeting_id
                ORDER BY meeting_date DESC
            """, (user_id, user_id, user_id))

        meetings = cursor.fetchall()
        return [dict(meeting) for meeting in meetings]

    finally:
        conn.close()


def get_shared_meetings(user_id: int) -> List[Dict]:
    """
    사용자가 공유받은 회의 목록만 조회 (본인 노트 제외)

    Args:
        user_id: 사용자 ID

    Returns:
        공유받은 회의 목록 (meeting_id, title, meeting_date, audio_file)
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 공유받은 노트만 조회 (owner_id != user_id)
        cursor.execute("""
            SELECT DISTINCT
                md.meeting_id,
                md.title,
                MAX(md.meeting_date) as meeting_date,
                (SELECT audio_file FROM meeting_dialogues WHERE meeting_id = md.meeting_id LIMIT 1) as audio_file,
                (SELECT owner_id FROM meeting_dialogues WHERE meeting_id = md.meeting_id LIMIT 1) as owner_id
            FROM meeting_dialogues md
            INNER JOIN meeting_shares s ON md.meeting_id = s.meeting_id
            WHERE s.shared_with_user_id = ?
            GROUP BY md.meeting_id
            ORDER BY meeting_date DESC
        """, (user_id,))

        meetings = cursor.fetchall()
        return [dict(meeting) for meeting in meetings]

    finally:
        conn.close()


def share_meeting(meeting_id: str, owner_id: int, shared_with_email: str) -> Dict:
    """
    회의 노트 공유

    Args:
        meeting_id: 회의 ID
        owner_id: 소유자 ID
        shared_with_email: 공유받을 사용자 이메일

    Returns:
        {'success': bool, 'message': str}
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 1. 공유받을 사용자 조회
        shared_user = get_user_by_email(shared_with_email)
        if not shared_user:
            return {'success': False, 'message': '해당 이메일의 사용자를 찾을 수 없습니다.'}

        # 2. 본인에게 공유 방지
        if shared_user['id'] == owner_id:
            return {'success': False, 'message': '본인에게는 공유할 수 없습니다.'}

        # 3. 소유자 확인
        cursor.execute("""
            SELECT owner_id FROM meeting_dialogues WHERE meeting_id = ? LIMIT 1
        """, (meeting_id,))
        result = cursor.fetchone()

        if not result:
            return {'success': False, 'message': '회의를 찾을 수 없습니다.'}

        if result['owner_id'] != owner_id:
            return {'success': False, 'message': '회의 소유자만 공유할 수 있습니다.'}

        # 4. 이미 공유되어 있는지 확인
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM meeting_shares
            WHERE meeting_id = ? AND shared_with_user_id = ?
        """, (meeting_id, shared_user['id']))
        result = cursor.fetchone()

        if result['count'] > 0:
            return {'success': False, 'message': '이미 공유된 사용자입니다.'}

        # 5. 공유 생성
        cursor.execute("""
            INSERT INTO meeting_shares (meeting_id, owner_id, shared_with_user_id, permission)
            VALUES (?, ?, ?, 'read')
        """, (meeting_id, owner_id, shared_user['id']))
        conn.commit()

        print(f"✅ 회의 공유 완료: {meeting_id} → {shared_with_email}")

        return {'success': True, 'message': f'{shared_with_email}에게 공유되었습니다.'}

    except Exception as e:
        print(f"❌ 회의 공유 실패: {e}")
        return {'success': False, 'message': f'공유 실패: {str(e)}'}

    finally:
        conn.close()


def get_shared_users(meeting_id: str) -> List[Dict]:
    """회의를 공유받은 사용자 목록 조회"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                u.id,
                u.email,
                u.name,
                u.profile_picture,
                s.permission,
                s.created_at as shared_at
            FROM meeting_shares s
            JOIN users u ON s.shared_with_user_id = u.id
            WHERE s.meeting_id = ?
            ORDER BY s.created_at DESC
        """, (meeting_id,))

        users = cursor.fetchall()
        return [dict(user) for user in users]

    finally:
        conn.close()


def remove_share(meeting_id: str, owner_id: int, shared_user_id: int) -> Dict:
    """공유 제거"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 소유자 확인
        cursor.execute("""
            SELECT owner_id FROM meeting_minutes WHERE meeting_id = ?
        """, (meeting_id,))
        result = cursor.fetchone()

        if not result or result['owner_id'] != owner_id:
            return {'success': False, 'message': '회의 소유자만 공유를 제거할 수 있습니다.'}

        # 공유 제거
        cursor.execute("""
            DELETE FROM meeting_shares
            WHERE meeting_id = ? AND owner_id = ? AND shared_with_user_id = ?
        """, (meeting_id, owner_id, shared_user_id))
        conn.commit()

        if cursor.rowcount > 0:
            return {'success': True, 'message': '공유가 제거되었습니다.'}
        else:
            return {'success': False, 'message': '공유 정보를 찾을 수 없습니다.'}

    finally:
        conn.close()


def get_user_accessible_meeting_ids(user_id: int) -> List[str]:
    """
    사용자가 접근 가능한 모든 meeting_id 목록 반환

    조건:
    - Admin: 모든 노트
    - User: 본인이 생성한 노트 + 공유받은 노트

    Args:
        user_id: 사용자 ID

    Returns:
        meeting_id 목록 (예: ['meeting_1', 'meeting_2', ...])
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        if is_admin(user_id):
            # Admin: 모든 meeting_id
            cursor.execute("""
                SELECT DISTINCT meeting_id
                FROM meeting_dialogues
            """)
        else:
            # User: 본인 노트 + 공유받은 노트
            cursor.execute("""
                SELECT DISTINCT md.meeting_id
                FROM meeting_dialogues md
                LEFT JOIN meeting_shares s ON md.meeting_id = s.meeting_id
                WHERE md.owner_id = ? OR s.shared_with_user_id = ?
            """, (user_id, user_id))

        results = cursor.fetchall()
        meeting_ids = [row['meeting_id'] for row in results]

        print(f"✅ 사용자 {user_id} 접근 가능한 노트: {len(meeting_ids)}개")
        return meeting_ids

    finally:
        conn.close()
