#!/usr/bin/env python3
"""
고아 데이터 정리 스크립트

Vector DB와 uploads 폴더에 있지만 meeting_dialogues에는 없는 데이터를 정리합니다.
"""

import sqlite3
import os
import sys

def cleanup_orphan_data():
    print("=" * 70)
    print("🧹 고아 데이터 정리 스크립트 시작")
    print("=" * 70)
    print()

    # 1. SQLite meeting_dialogues에서 유효한 meeting_id 조회
    print("📊 Step 1: SQLite에서 유효한 meeting_id 조회")
    conn = sqlite3.connect('database/minute_ai.db')
    cursor = conn.cursor()

    cursor.execute('SELECT DISTINCT meeting_id, audio_file FROM meeting_dialogues')
    valid_meetings = cursor.fetchall()

    valid_meeting_ids = set([row[0] for row in valid_meetings])
    valid_audio_files = set([row[1] for row in valid_meetings])

    print(f"  ✅ 유효한 meeting_id: {len(valid_meeting_ids)}개")
    for mid in sorted(valid_meeting_ids):
        print(f"    • {mid}")
    print()

    conn.close()

    # 2. Vector DB에서 고아 데이터 확인
    print("📊 Step 2: Vector DB에서 고아 데이터 확인")
    conn_vector = sqlite3.connect('database/vector_db/chroma.sqlite3')
    cursor_vector = conn_vector.cursor()

    # meeting_id 메타데이터 조회
    cursor_vector.execute('''
        SELECT DISTINCT string_value
        FROM embedding_metadata
        WHERE key = "meeting_id"
    ''')

    vector_meeting_ids = set([row[0] for row in cursor_vector.fetchall()])
    orphan_meeting_ids = vector_meeting_ids - valid_meeting_ids

    print(f"  📦 Vector DB의 meeting_id: {len(vector_meeting_ids)}개")
    print(f"  🗑️  고아 meeting_id: {len(orphan_meeting_ids)}개")

    for mid in sorted(orphan_meeting_ids):
        # audio_file 확인
        cursor_vector.execute('''
            SELECT string_value
            FROM embedding_metadata
            WHERE key = "audio_file" AND id IN (
                SELECT DISTINCT id FROM embedding_metadata
                WHERE key = "meeting_id" AND string_value = ?
            )
            LIMIT 1
        ''', (mid,))

        result = cursor_vector.fetchone()
        audio_file = result[0] if result else "Unknown"
        print(f"    • {mid} → {audio_file}")
    print()

    conn_vector.close()

    # 3. uploads 폴더에서 고아 파일 확인
    print("📊 Step 3: uploads 폴더에서 고아 파일 확인")
    upload_files = []
    for f in os.listdir('uploads'):
        if f.endswith(('.mp3', '.wav', '.m4a', '.flac', '.mp4')):
            upload_files.append(f)

    orphan_files = set(upload_files) - valid_audio_files

    print(f"  📂 uploads 폴더의 파일: {len(upload_files)}개")
    print(f"  🗑️  고아 파일: {len(orphan_files)}개")

    for f in sorted(orphan_files):
        file_path = os.path.join('uploads', f)
        file_size = os.path.getsize(file_path)
        print(f"    • {f} ({file_size / 1024 / 1024:.2f} MB)")
    print()

    # 4. 사용자 확인
    if not orphan_meeting_ids and not orphan_files:
        print("✅ 고아 데이터가 없습니다!")
        return

    print("=" * 70)
    print("⚠️  다음 데이터를 삭제합니다:")
    print(f"  - Vector DB 고아 meeting_id: {len(orphan_meeting_ids)}개")
    print(f"  - uploads 고아 파일: {len(orphan_files)}개")
    print()
    print("⚠️  자동으로 삭제를 진행합니다 (5초 대기)...")

    import time
    for i in range(5, 0, -1):
        print(f"  {i}초...")
        time.sleep(1)

    print("  🚀 삭제 시작!")

    print()
    print("=" * 70)
    print("🗑️  삭제 시작")
    print("=" * 70)

    # 5. Vector DB에서 고아 데이터 삭제
    if orphan_meeting_ids:
        print(f"\n📦 Vector DB에서 {len(orphan_meeting_ids)}개 meeting_id 삭제 중...")

        conn_vector = sqlite3.connect('database/vector_db/chroma.sqlite3')
        cursor_vector = conn_vector.cursor()

        for mid in orphan_meeting_ids:
            # embedding_metadata에서 삭제
            cursor_vector.execute('''
                DELETE FROM embedding_metadata
                WHERE id IN (
                    SELECT DISTINCT id FROM embedding_metadata
                    WHERE key = "meeting_id" AND string_value = ?
                )
            ''', (mid,))

            deleted_rows = cursor_vector.rowcount
            print(f"  ✅ {mid}: {deleted_rows}개 메타데이터 삭제")

        conn_vector.commit()
        conn_vector.close()
        print("  ✅ Vector DB 정리 완료")

    # 6. uploads 폴더에서 고아 파일 삭제
    if orphan_files:
        print(f"\n📂 uploads 폴더에서 {len(orphan_files)}개 파일 삭제 중...")

        for f in orphan_files:
            file_path = os.path.join('uploads', f)
            try:
                os.remove(file_path)
                print(f"  ✅ {f} 삭제 완료")
            except Exception as e:
                print(f"  ❌ {f} 삭제 실패: {e}")

        print("  ✅ 파일 정리 완료")

    print()
    print("=" * 70)
    print("🎉 고아 데이터 정리 완료!")
    print("=" * 70)


if __name__ == "__main__":
    try:
        cleanup_orphan_data()
    except KeyboardInterrupt:
        print("\n\n❌ 사용자에 의해 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
