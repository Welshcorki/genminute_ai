from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory
import os
import json
from werkzeug.utils import secure_filename
from google import genai
from google.genai import types
from dotenv import load_dotenv

# --- 커스텀 모듈 임포트 ---
from utils.stt import STTManager
from utils.db_manager import DatabaseManager
from utils.vector_db_manager import vdb_manager
from utils.validation import validate_title, parse_meeting_date

# --- 기본 설정 및 초기화 ---
app = Flask(__name__)

# 스크립트의 절대 경로를 기준으로 경로 설정
basedir = os.path.abspath(os.path.dirname(__file__))


UPLOAD_FOLDER = os.path.join(basedir, "uploads")
DB_PATH = os.path.join(basedir, "database", "minute_ai.db")
ALLOWED_EXTENSIONS = {"wav", "mp3", "m4a", "flac"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# 데이터베이스 매니저 초기화
db = DatabaseManager(DB_PATH)
stt_manager = STTManager()

# --- 유틸리티 함수 ---
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# --- Flask 라우트 ---
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_and_process():
    # 제목 검증
    title = request.form.get('title', '').strip()
    is_valid, error_message = validate_title(title)
    if not is_valid:
        return render_template("index.html", error=error_message)

    # 오디오 파일 검증
    if 'audio_file' not in request.files:
        return render_template("index.html", error="오디오 파일이 없습니다.")

    file = request.files['audio_file']
    if file.filename == '' or not allowed_file(file.filename):
        return render_template("index.html", error="파일이 없거나 허용되지 않는 형식입니다.")

    # 회의 일시 처리 (입력이 없으면 현재 시간 자동 설정)
    meeting_date_input = request.form.get('meeting_date', '')
    meeting_date = parse_meeting_date(meeting_date_input)

    try:
        filename = secure_filename(file.filename)
        audio_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(audio_path)
    
        segments = stt_manager.transcribe_audio(audio_path)

        if not segments:
            return render_template("index.html", error="음성 인식에 실패했습니다. API 키 등을 확인해주세요.")

        # 1. SQLite DB에 개별 대화 저장 (meeting_date 전달)
        meeting_id = db.save_stt_to_db(segments, filename, title, meeting_date)

        # 2. Vector DB에 대화록을 의미적 청크로 저장
        try:
            all_segments = db.get_segments_by_meeting_id(meeting_id)
            if all_segments:
                # 메타데이터는 첫 번째 세그먼트에서 가져옴
                first_segment = all_segments[0]
                # segments를 직접 전달하여 의미적 청킹 수행
                vdb_manager.add_meeting_as_chunk(
                    meeting_id=meeting_id,
                    title=first_segment['title'],
                    meeting_date=first_segment['meeting_date'],
                    audio_file=first_segment['audio_file'],
                    segments=all_segments  # 전체 segments 전달
                )
        except Exception as vdb_error:
            print(f"Vector DB 저장 중 오류 발생: {vdb_error}")
            # 벡터 DB 저장에 실패해도 주요 기능은 계속 동작하도록 일단 넘어감

        # 3. 결과를 보여주는 뷰어 페이지로 리디렉션
        return redirect(url_for('view_meeting', meeting_id=meeting_id))

    except Exception as e:
        return render_template("index.html", error=f"서버 처리 중 오류가 발생했습니다: {e}")

@app.route("/notes")
def list_notes():
    try:
        meetings = db.get_all_meetings()
        return render_template("notes.html", meetings=meetings)
    except Exception as e:
        return render_template("index.html", error=f"노트 목록을 불러오는 중 오류가 발생했습니다: {e}")

@app.route("/view/<string:meeting_id>")
def view_meeting(meeting_id):
    return render_template("viewer.html", meeting_id=meeting_id)

@app.route("/api/meeting/<string:meeting_id>")
def get_meeting_data(meeting_id):
    try:
        rows = db.get_meeting_by_id(meeting_id)
        if not rows:
            return jsonify({"success": False, "error": "해당 회의를 찾을 수 없습니다."}), 404

        transcript = [dict(row) for row in rows]
        audio_file = rows[0]['audio_file']
        title = rows[0]['title']

        return jsonify({
            "success": True, "meeting_id": meeting_id, "title": title,
            "audio_url": url_for('uploaded_file', filename=audio_file),
            "transcript": transcript
        })
    except Exception as e:
        return jsonify({"success": False, "error": f"DB 조회 오류: {e}"}), 500

@app.route("/api/summarize/<string:meeting_id>", methods=["POST"])
def summarize_meeting(meeting_id):
    try:
        # 1. meeting_id로 회의록 내용 조회
        rows = db.get_meeting_by_id(meeting_id)
        if not rows:
            return jsonify({"success": False, "error": "해당 회의를 찾을 수 없습니다."}), 404

        # 2. title, transcript_text, meeting_date, audio_file 추출
        title = rows[0]['title']
        meeting_date = rows[0]['meeting_date'] # Assuming 'meeting_date' is available in the first row
        audio_file = rows[0]['audio_file'] # Assuming 'audio_file' is available in the first row
        transcript_text = " ".join([row['segment'] for row in rows])

        # 3. stt_manager의 subtopic_generate를 이용해 요약 생성
        summary_content = stt_manager.subtopic_generate(title, transcript_text)


        if not summary_content:
            return jsonify({"success": False, "error": "요약 생성에 실패했습니다."}), 500

        # 4. 생성한 내용을 'meeting_subtopic' DB에 저장 (vector_db_manager.add_meeting_as_subtopic 함수 이용)
        vdb_manager.add_meeting_as_subtopic(
            meeting_id=meeting_id,
            title=title,
            meeting_date=meeting_date,
            audio_file=audio_file,
            summary_content=summary_content
        )

        return jsonify({"success": True, "message": "요약이 성공적으로 생성 및 저장되었습니다.", "summary": summary_content})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": f"요약 처리 중 오류 발생: {str(e)}"}), 500

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.route("/api/delete_vector_db_entry", methods=["POST"])
def delete_vector_db_entry():
    try:
        data = request.get_json()
        db_type = data.get("db_type")
        meeting_id = data.get("meeting_id")
        audio_file = data.get("audio_file")
        title = data.get("title")

        if not db_type:
            return jsonify({"success": False, "error": "삭제할 DB 타입을 지정해야 합니다."}), 400

        vdb_manager.delete_from_collection(
            db_type=db_type,
            meeting_id=meeting_id,
            audio_file=audio_file,
            title=title
        )
        return jsonify({"success": True, "message": f"'{db_type}' 컬렉션에서 항목 삭제 요청이 처리되었습니다."})

    except ValueError as ve:
        return jsonify({"success": False, "error": str(ve)}), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": f"벡터 DB 삭제 중 오류 발생: {str(e)}"}), 500

@app.route("/api/search", methods=["POST"])
def search_retriever():
    """리트리버 검색 API"""
    try:
        data = request.get_json()
        query = data.get("query")
        db_type = data.get("db_type")
        retriever_type = data.get("retriever_type", "similarity") # Default to similarity

        if not query or not db_type:
            return jsonify({"success": False, "error": "검색어와 DB 타입을 모두 입력해주세요."}), 400

        print(f"🔍 API 검색 요청: DB='{db_type}', Query='{query}', Retriever Type='{retriever_type}'")
        results = vdb_manager.search(db_type=db_type, query=query, retriever_type=retriever_type, k=5)

        # 결과를 JSON으로 직렬화 가능한 형태로 변환
        formatted_results = [
            {
                "page_content": doc.page_content,
                "metadata": doc.metadata,
            }
            for doc in results
        ]
        
        print(f"✅ 검색 완료: {len(formatted_results)}개 결과 반환")
        return jsonify({"success": True, "results": formatted_results})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": f"검색 중 오류 발생: {str(e)}"}), 500

@app.route("/summary_template")
def summary_template_page():
    return render_template("summary_template.html")

@app.route("/retriever")
def retriever_page():
    """리트리버 테스트 페이지를 렌더링합니다."""
    return render_template("retriever.html")

@app.route("/api/check_summary/<string:meeting_id>", methods=["GET"])
def check_summary(meeting_id):
    """문단 요약 존재 여부 확인 API"""
    try:
        # Vector DB에서 문단 요약 조회
        summary_content = vdb_manager.get_summary_by_meeting_id(meeting_id)

        if summary_content:
            return jsonify({
                "success": True,
                "has_summary": True,
                "summary": summary_content
            })
        else:
            return jsonify({
                "success": True,
                "has_summary": False,
                "message": "문단 요약이 아직 생성되지 않았습니다."
            })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": f"요약 조회 중 오류 발생: {str(e)}"}), 500

@app.route("/api/get_minutes/<string:meeting_id>", methods=["GET"])
def get_minutes(meeting_id):
    """회의록 조회 API - SQLite DB에서 저장된 회의록을 조회합니다."""
    try:
        # DB에서 회의록 조회
        minutes_data = db.get_minutes_by_meeting_id(meeting_id)

        if minutes_data:
            return jsonify({
                "success": True,
                "has_minutes": True,
                "minutes": minutes_data['minutes_content'],
                "created_at": minutes_data['created_at'],
                "updated_at": minutes_data['updated_at']
            })
        else:
            return jsonify({
                "success": True,
                "has_minutes": False,
                "message": "회의록이 아직 생성되지 않았습니다."
            })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": f"회의록 조회 중 오류 발생: {str(e)}"}), 500

@app.route("/api/generate_minutes/<string:meeting_id>", methods=["POST"])
def generate_minutes(meeting_id):
    """회의록 생성 API - 청킹된 문서를 기반으로 정식 회의록을 생성하고 DB에 저장합니다."""
    try:
        # 1. meeting_id로 회의록 내용 조회
        rows = db.get_meeting_by_id(meeting_id)
        if not rows:
            return jsonify({"success": False, "error": "해당 회의를 찾을 수 없습니다."}), 404

        # 2. title, meeting_date, transcript_text 추출
        title = rows[0]['title']
        meeting_date = rows[0]['meeting_date']
        transcript_text = " ".join([row['segment'] for row in rows])

        # 3. vector DB에서 청킹된 문서 가져오기 (chunk_index 순서대로)
        chunks_content = vdb_manager.get_chunks_by_meeting_id(meeting_id)

        if not chunks_content:
            return jsonify({
                "success": False,
                "error": "청킹된 회의 내용을 찾을 수 없습니다. 오디오 파일을 먼저 업로드해주세요."
            }), 400

        # 4. stt_manager의 generate_minutes를 이용해 회의록 생성
        minutes_content = stt_manager.generate_minutes(title, transcript_text, chunks_content)

        if not minutes_content:
            return jsonify({"success": False, "error": "회의록 생성에 실패했습니다."}), 500

        # 5. 생성된 회의록을 SQLite DB에 저장
        db.save_minutes(meeting_id, title, meeting_date, minutes_content)

        return jsonify({
            "success": True,
            "message": "회의록이 성공적으로 생성 및 저장되었습니다.",
            "minutes": minutes_content
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": f"회의록 생성 중 오류 발생: {str(e)}"}), 500

@app.route("/api/delete_meeting/<string:meeting_id>", methods=["POST"])
def delete_meeting(meeting_id):
    """
    회의와 관련된 모든 데이터를 삭제합니다.
    - SQLite DB: meeting_dialogues, meeting_minutes
    - Vector DB: meeting_chunk, meeting_subtopic
    - 오디오 파일
    """
    try:
        # 1. meeting_id로 오디오 파일명 조회
        audio_file = db.get_audio_file_by_meeting_id(meeting_id)

        if not audio_file:
            return jsonify({"success": False, "error": "해당 회의를 찾을 수 없습니다."}), 404

        # 2. SQLite DB에서 삭제
        deleted_sqlite = db.delete_meeting_by_id(meeting_id)

        # 3. Vector DB에서 삭제 (meeting_chunk)
        try:
            vdb_manager.delete_from_collection(
                db_type="chunk",
                meeting_id=meeting_id
            )
            print(f"✅ Vector DB (meeting_chunk) 삭제 완료")
        except Exception as e:
            print(f"⚠️ Vector DB (meeting_chunk) 삭제 중 오류: {e}")

        # 4. Vector DB에서 삭제 (meeting_subtopic)
        try:
            vdb_manager.delete_from_collection(
                db_type="subtopic",
                meeting_id=meeting_id
            )
            print(f"✅ Vector DB (meeting_subtopic) 삭제 완료")
        except Exception as e:
            print(f"⚠️ Vector DB (meeting_subtopic) 삭제 중 오류: {e}")

        # 5. 오디오 파일 삭제
        audio_path = os.path.join(app.config["UPLOAD_FOLDER"], audio_file)
        if os.path.exists(audio_path):
            os.remove(audio_path)
            print(f"✅ 오디오 파일 삭제 완료: {audio_file}")
        else:
            print(f"⚠️ 오디오 파일을 찾을 수 없음: {audio_file}")

        return jsonify({
            "success": True,
            "message": "회의 데이터가 성공적으로 삭제되었습니다.",
            "deleted": {
                "sqlite_dialogues": deleted_sqlite["dialogues"],
                "sqlite_minutes": deleted_sqlite["minutes"],
                "audio_file": audio_file
            }
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": f"삭제 중 오류 발생: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)