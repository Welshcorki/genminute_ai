#!/usr/bin/env python3
"""
데이터 정리 스크립트

1. 고아 데이터 정리: Vector DB와 uploads 폴더에 있지만 meeting_dialogues에는 없는 데이터를 정리
2. 전체 회의 데이터 삭제: 모든 회의 관련 데이터를 삭제 (users 테이블은 유지)
"""

import sqlite3
import os
import sys
import chromadb
from pathlib import Path

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
    try:
        chroma_client = chromadb.PersistentClient(path="./database/vector_db")

        vector_meeting_ids = set()
        audio_file_map = {}

        # meeting_chunks와 meeting_subtopic 컬렉션 확인
        for collection_name in ['meeting_chunks', 'meeting_subtopic']:
            try:
                collection = chroma_client.get_collection(name=collection_name)
                all_data = collection.get(include=['metadatas'])

                for metadata in all_data['metadatas']:
                    if metadata and 'meeting_id' in metadata:
                        mid = metadata['meeting_id']
                        vector_meeting_ids.add(mid)
                        if 'audio_file' in metadata and mid not in audio_file_map:
                            audio_file_map[mid] = metadata['audio_file']

                print(f"  • {collection_name}: {len(all_data['ids'])}개 문서")
            except Exception as e:
                print(f"  ⚠️  {collection_name}: {e}")

        orphan_meeting_ids = vector_meeting_ids - valid_meeting_ids

        print(f"  📦 Vector DB의 meeting_id: {len(vector_meeting_ids)}개")
        print(f"  🗑️  고아 meeting_id: {len(orphan_meeting_ids)}개")

        for mid in sorted(orphan_meeting_ids):
            audio_file = audio_file_map.get(mid, "Unknown")
            print(f"    • {mid} → {audio_file}")
        print()

    except Exception as e:
        print(f"  ⚠️  Vector DB 확인 실패: {e}")
        orphan_meeting_ids = set()
        audio_file_map = {}

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

        try:
            chroma_client = chromadb.PersistentClient(path="./database/vector_db")

            for mid in orphan_meeting_ids:
                total_deleted = 0

                for collection_name in ['meeting_chunks', 'meeting_subtopic']:
                    try:
                        collection = chroma_client.get_collection(name=collection_name)

                        # 해당 meeting_id를 가진 문서 검색
                        results = collection.get(
                            where={"meeting_id": mid},
                            include=[]
                        )

                        if results['ids']:
                            # 문서 삭제
                            collection.delete(ids=results['ids'])
                            deleted_count = len(results['ids'])
                            total_deleted += deleted_count
                            print(f"  • {collection_name}: {deleted_count}개 삭제")

                    except Exception as e:
                        print(f"  ⚠️  {collection_name} 삭제 실패: {e}")

                print(f"  ✅ {mid}: 총 {total_deleted}개 문서 삭제")

            print("  ✅ Vector DB 정리 완료")

        except Exception as e:
            print(f"  ❌ Vector DB 정리 실패: {e}")

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


def cleanup_all_meeting_data():
    """모든 회의 데이터를 삭제합니다 (users 테이블은 유지)"""
    print("=" * 70)
    print("🗑️  전체 회의 데이터 삭제 스크립트 시작")
    print("=" * 70)
    print()

    # 1. 현재 데이터 확인
    print("📊 Step 1: 현재 데이터 확인")
    conn = sqlite3.connect('database/minute_ai.db')
    cursor = conn.cursor()

    # 각 테이블의 데이터 개수 확인
    tables_to_check = ['meeting_dialogues', 'meeting_minutes', 'meeting_mindmap', 'meeting_shares']
    data_counts = {}

    for table in tables_to_check:
        try:
            cursor.execute(f'SELECT COUNT(*) FROM {table}')
            count = cursor.fetchone()[0]
            data_counts[table] = count
            print(f"  • {table}: {count}개")
        except sqlite3.OperationalError:
            data_counts[table] = 0
            print(f"  • {table}: 테이블 없음")

    # meeting_id 목록 확인
    cursor.execute('SELECT DISTINCT meeting_id, title FROM meeting_dialogues')
    meetings = cursor.fetchall()
    print(f"\n  📋 회의 목록 ({len(meetings)}개):")
    for mid, title in meetings:
        print(f"    • {title} ({mid[:8]}...)")

    conn.close()

    # 2. Vector DB 확인
    print("\n📊 Step 2: Vector DB 데이터 확인")
    try:
        chroma_client = chromadb.PersistentClient(path="./database/vector_db")

        total_docs = 0
        vector_meeting_ids = set()

        for collection_name in ['meeting_chunks', 'meeting_subtopic']:
            try:
                collection = chroma_client.get_collection(name=collection_name)
                all_data = collection.get(include=['metadatas'])
                doc_count = len(all_data['ids'])
                total_docs += doc_count

                for metadata in all_data['metadatas']:
                    if metadata and 'meeting_id' in metadata:
                        vector_meeting_ids.add(metadata['meeting_id'])

                print(f"  • {collection_name}: {doc_count}개 문서")
            except Exception as e:
                print(f"  ⚠️  {collection_name}: {e}")

        print(f"  • 총 {total_docs}개 문서, {len(vector_meeting_ids)}개 meeting_id")

    except Exception as e:
        print(f"  ⚠️  Vector DB 확인 실패: {e}")
        vector_meeting_ids = set()
        total_docs = 0

    # 3. uploads 폴더 확인
    print("\n📊 Step 3: uploads 폴더 확인")
    upload_files = []
    total_size = 0
    try:
        for f in os.listdir('uploads'):
            if f.endswith(('.mp3', '.wav', '.m4a', '.flac', '.mp4')):
                file_path = os.path.join('uploads', f)
                file_size = os.path.getsize(file_path)
                upload_files.append((f, file_size))
                total_size += file_size

        print(f"  • 파일 개수: {len(upload_files)}개")
        print(f"  • 총 용량: {total_size / 1024 / 1024:.2f} MB")
    except Exception as e:
        print(f"  ⚠️  uploads 폴더 확인 실패: {e}")

    # 4. 삭제 확인
    print("\n" + "=" * 70)
    print("⚠️  경고: 다음 데이터를 모두 삭제합니다!")
    print("=" * 70)
    print(f"  ✓ meeting_dialogues: {data_counts.get('meeting_dialogues', 0)}개")
    print(f"  ✓ meeting_minutes: {data_counts.get('meeting_minutes', 0)}개")
    print(f"  ✓ meeting_mindmap: {data_counts.get('meeting_mindmap', 0)}개")
    print(f"  ✓ meeting_shares: {data_counts.get('meeting_shares', 0)}개")
    print(f"  ✓ Vector DB: {total_docs}개 문서 ({len(vector_meeting_ids)}개 meeting_id)")
    print(f"  ✓ uploads 폴더: {len(upload_files)}개 파일 ({total_size / 1024 / 1024:.2f} MB)")
    print()
    print("  ⚠️  users 테이블은 유지됩니다!")
    print()

    # 사용자 확인
    user_input = input("  정말로 삭제하시겠습니까? (yes/no): ").strip().lower()
    if user_input != 'yes':
        print("\n❌ 삭제가 취소되었습니다.")
        return

    print("\n⚠️  5초 후 삭제를 시작합니다...")
    import time
    for i in range(5, 0, -1):
        print(f"  {i}초...")
        time.sleep(1)

    print("\n  🚀 삭제 시작!")
    print("=" * 70)

    # 5. SQLite DB 테이블 삭제
    print("\n📊 SQLite DB 테이블 정리 중...")
    conn = sqlite3.connect('database/minute_ai.db')
    cursor = conn.cursor()

    for table in tables_to_check:
        try:
            cursor.execute(f'DELETE FROM {table}')
            deleted = cursor.rowcount
            print(f"  ✅ {table}: {deleted}개 삭제")
        except sqlite3.OperationalError as e:
            print(f"  ⚠️  {table}: {e}")

    conn.commit()
    conn.close()
    print("  ✅ SQLite DB 정리 완료")

    # 6. Vector DB 정리
    print("\n📦 Vector DB 정리 중...")
    try:
        chroma_client = chromadb.PersistentClient(path="./database/vector_db")

        total_deleted = 0
        for collection_name in ['meeting_chunks', 'meeting_subtopic']:
            try:
                collection = chroma_client.get_collection(name=collection_name)
                all_data = collection.get(include=[])
                doc_count = len(all_data['ids'])

                if doc_count > 0:
                    # 모든 문서 삭제
                    collection.delete(ids=all_data['ids'])
                    total_deleted += doc_count
                    print(f"  ✅ {collection_name}: {doc_count}개 문서 삭제")
                else:
                    print(f"  • {collection_name}: 삭제할 문서 없음")

            except Exception as e:
                print(f"  ⚠️  {collection_name} 삭제 실패: {e}")

        print(f"  ✅ Vector DB 정리 완료 (총 {total_deleted}개 문서 삭제)")

    except Exception as e:
        print(f"  ⚠️  Vector DB 정리 실패: {e}")

    # 7. uploads 폴더 정리
    print("\n📂 uploads 폴더 정리 중...")
    deleted_count = 0
    for f, size in upload_files:
        file_path = os.path.join('uploads', f)
        try:
            os.remove(file_path)
            deleted_count += 1
            print(f"  ✅ {f} ({size / 1024 / 1024:.2f} MB)")
        except Exception as e:
            print(f"  ❌ {f} 삭제 실패: {e}")

    print(f"  ✅ {deleted_count}/{len(upload_files)}개 파일 삭제 완료")

    print("\n" + "=" * 70)
    print("🎉 전체 회의 데이터 삭제 완료!")
    print("=" * 70)
    print("\n  ✓ users 테이블은 유지되었습니다.")
    print("  ✓ 데이터베이스 구조는 그대로 유지됩니다.")


def show_menu():
    """메인 메뉴 표시"""
    print("\n" + "=" * 70)
    print("🧹 Minute AI - 데이터 정리 도구")
    print("=" * 70)
    print()
    print("1. 고아 데이터 정리 (고아 데이터만 삭제)")
    print("2. 전체 회의 데이터 삭제 (모든 회의 데이터 삭제, users는 유지)")
    print("3. 종료")
    print()

    while True:
        choice = input("선택하세요 (1-3): ").strip()
        if choice in ['1', '2', '3']:
            return choice
        print("❌ 잘못된 입력입니다. 1, 2, 3 중 하나를 입력하세요.")


if __name__ == "__main__":
    try:
        choice = show_menu()

        if choice == '1':
            cleanup_orphan_data()
        elif choice == '2':
            cleanup_all_meeting_data()
        elif choice == '3':
            print("\n👋 프로그램을 종료합니다.")
            sys.exit(0)

    except KeyboardInterrupt:
        print("\n\n❌ 사용자에 의해 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
