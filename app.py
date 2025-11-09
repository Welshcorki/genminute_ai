from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory, session, Response, stream_with_context
import os
import json
import uuid
import datetime as dt
import subprocess
from werkzeug.utils import secure_filename
from google import genai
from google.genai import types
from dotenv import load_dotenv

# --- 커스텀 모듈 임포트 ---
from utils.stt import STTManager
from utils.db_manager import DatabaseManager
from utils.vector_db_manager import vdb_manager
from utils.validation import validate_title, parse_meeting_date
from utils.chat_manager import ChatManager
from utils.analysis import calculate_speaker_share
from utils.firebase_auth import initialize_firebase, verify_id_token
from utils.user_manager import get_or_create_user, get_user_by_id, can_access_meeting, get_user_meetings, get_shared_meetings, share_meeting, get_shared_users, remove_share, get_user_accessible_meeting_ids, is_admin, can_edit_meeting
from utils.decorators import login_required, admin_required

# --- 환경 변수 로드 ---
# 명시적으로 .env 파일 경로 지정
from pathlib import Path
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# 디버깅: 환경 변수 로드 확인
print(f"📂 .env 파일 경로: {env_path}")
print(f"📂 .env 파일 존재: {env_path.exists()}")
print(f"🔑 FIREBASE_API_KEY 로드: {os.getenv('FIREBASE_API_KEY')[:20] if os.getenv('FIREBASE_API_KEY') else 'None'}...")
print(f"🔑 FLASK_SECRET_KEY 로드: {'있음' if os.getenv('FLASK_SECRET_KEY') else 'None'}")

# --- 기본 설정 및 초기화 ---
app = Flask(__name__)

# Flask SECRET_KEY 설정 (세션 암호화)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
if not app.config['SECRET_KEY']:
    raise ValueError("FLASK_SECRET_KEY가 .env 파일에 설정되지 않았습니다!")

# Firebase 초기화
try:
    initialize_firebase()
except Exception as e:
    print(f"⚠️ Firebase 초기화 실패: {e}")
    print("로그인 기능이 작동하지 않을 수 있습니다.")

# 스크립트의 절대 경로를 기준으로 경로 설정
basedir = os.path.abspath(os.path.dirname(__file__))


UPLOAD_FOLDER = os.path.join(basedir, "uploads")
DB_PATH = os.path.join(basedir, "database", "minute_ai.db")
ALLOWED_EXTENSIONS = {"wav", "mp3", "m4a", "flac", "mp4"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# 데이터베이스 매니저 초기화
db = DatabaseManager(DB_PATH)
stt_manager = STTManager()

# VectorDBManager에 DatabaseManager 인스턴스 주입
vdb_manager.db_manager = db

# ChatManager 초기화 (similarity 리트리버 사용)
chat_manager = ChatManager(vdb_manager, retriever_type="similarity")

# --- 유틸리티 함수 ---
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def convert_video_to_audio(video_path, audio_path):
    """
    비디오 파일(MP4)을 오디오 파일(WAV)로 변환합니다.

    Args:
        video_path: 입력 비디오 파일 경로
        audio_path: 출력 오디오 파일 경로

    Returns:
        bool: 변환 성공 여부
    """
    try:
        # ffmpeg 명령어로 비디오를 WAV로 변환
        # -y: 기존 파일 덮어쓰기
        # -i: 입력 파일
        # -vn: 비디오 스트림 제거 (오디오만 추출)
        # -acodec pcm_s16le: WAV 포맷 (16-bit PCM)
        # -ar 16000: 샘플링 레이트 16kHz (Whisper 권장)
        # -ac 1: 모노 채널
        command = [
            'ffmpeg',
            '-y',
            '-i', video_path,
            '-vn',
            '-acodec', 'pcm_s16le',
            '-ar', '16000',
            '-ac', '1',
            audio_path
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            timeout=1200
        )

        if result.returncode == 0:
            print(f"✅ 비디오 → 오디오 변환 성공: {audio_path}")
            return True
        else:
            print(f"❌ 비디오 → 오디오 변환 실패: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print(f"❌ 비디오 변환 타임아웃 (20분 초과)")
        return False
    except Exception as e:
        print(f"❌ 비디오 변환 중 오류 발생: {e}")
        return False


# --- Context Processor (모든 템플릿에서 사용 가능한 변수) ---
@app.context_processor
def inject_user_info():
    """모든 템플릿에 사용자 정보를 주입"""
    if 'user_id' in session:
        user_id = session['user_id']
        is_user_admin = is_admin(user_id)
        return {
            'current_user_id': user_id,
            'is_admin': is_user_admin,
            'user_name': session.get('name', '사용자'),
            'user_email': session.get('email', ''),
            'user_picture': session.get('profile_picture', '')
        }
    return {
        'current_user_id': None,
        'is_admin': False,
        'user_name': None,
        'user_email': None,
        'user_picture': None
    }


# --- Flask 라우트 ---

# 로그인 페이지
@app.route("/login")
def login_page():
    """로그인 페이지"""
    # 이미 로그인된 경우 메인 페이지로 리다이렉트
    if 'user_id' in session:
        return redirect(url_for('index'))

    # Firebase Config를 환경 변수에서 읽어서 템플릿에 전달
    firebase_config = {
        'apiKey': os.getenv('FIREBASE_API_KEY'),
        'authDomain': os.getenv('FIREBASE_AUTH_DOMAIN'),
        'projectId': os.getenv('FIREBASE_PROJECT_ID'),
        'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET'),
        'messagingSenderId': os.getenv('FIREBASE_MESSAGING_SENDER_ID'),
        'appId': os.getenv('FIREBASE_APP_ID'),
        'measurementId': os.getenv('FIREBASE_MEASUREMENT_ID')
    }

    # 디버깅: Firebase Config 확인
    print("🔍 Firebase Config 확인:")
    print(f"  API Key: {firebase_config['apiKey'][:20] if firebase_config['apiKey'] else 'None'}...")
    print(f"  Auth Domain: {firebase_config['authDomain']}")
    print(f"  Project ID: {firebase_config['projectId']}")

    return render_template("login.html", firebase_config=firebase_config)

# 로그인 API
@app.route("/api/login", methods=["POST"])
def login():
    """Firebase ID 토큰을 받아 세션 생성"""
    try:
        data = request.get_json()
        id_token = data.get('idToken')

        if not id_token:
            return jsonify({'success': False, 'error': 'ID 토큰이 필요합니다.'}), 400

        # Firebase ID 토큰 검증
        user_info = verify_id_token(id_token)

        if not user_info:
            return jsonify({'success': False, 'error': '유효하지 않은 토큰입니다.'}), 401

        # DB에서 사용자 조회 또는 생성
        user = get_or_create_user(
            google_id=user_info['uid'],
            email=user_info['email'],
            name=user_info.get('name'),
            profile_picture=user_info.get('picture')
        )

        # 세션 생성
        session['user_id'] = user['id']
        session['email'] = user['email']
        session['name'] = user.get('name', '')
        session['role'] = user['role']
        session['profile_picture'] = user.get('profile_picture', '')

        print(f"✅ 로그인 성공: {user['email']} (role: {user['role']})")

        return jsonify({
            'success': True,
            'user': {
                'id': user['id'],
                'email': user['email'],
                'name': user.get('name'),
                'role': user['role']
            }
        })

    except Exception as e:
        print(f"❌ 로그인 실패: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'로그인 처리 중 오류가 발생했습니다: {str(e)}'}), 500

# 로그아웃 API
@app.route("/api/logout", methods=["POST"])
def logout():
    """세션 삭제"""
    session.clear()
    return jsonify({'success': True, 'message': '로그아웃되었습니다.'})

# 현재 사용자 정보 API
@app.route("/api/me", methods=["GET"])
@login_required
def get_current_user():
    """현재 로그인한 사용자 정보 반환"""
    return jsonify({
        'success': True,
        'user': {
            'id': session['user_id'],
            'email': session['email'],
            'name': session.get('name', ''),
            'role': session['role'],
            'profile_picture': session.get('profile_picture', '')
        }
    })

# 메인 페이지 (로그인 필요)
@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/upload_script", methods=["POST"])
@login_required
def upload_script():
    """스크립트 텍스트를 입력받아 청킹, 문단요약, 회의록 생성까지 처리"""
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.accept_mimetypes.accept_json

    # 현재 로그인한 사용자 ID
    owner_id = session['user_id']

    # 제목 검증
    title = request.form.get('title', '').strip()
    is_valid, error_message = validate_title(title)
    if not is_valid:
        if is_ajax:
            return jsonify({"success": False, "error": error_message}), 400
        return render_template("index.html", error=error_message)

    # 스크립트 텍스트 검증
    script_text = request.form.get('script_text', '').strip()
    if not script_text:
        if is_ajax:
            return jsonify({"success": False, "error": "스크립트 내용을 입력해주세요."}), 400
        return render_template("index.html", error="스크립트 내용을 입력해주세요.")

    # 회의 일시 처리 (입력이 없으면 현재 시간 자동 설정)
    meeting_date_input = request.form.get('meeting_date', '')
    meeting_date = parse_meeting_date(meeting_date_input)

    try:
        # 1. 스크립트 파싱하여 segments 생성
        segments = stt_manager.parse_script(script_text)

        if not segments:
            if is_ajax:
                return jsonify({"success": False, "error": "스크립트 파싱에 실패했습니다. 형식을 확인해주세요."}), 500
            return render_template("index.html", error="스크립트 파싱에 실패했습니다. 형식을 확인해주세요.")

        # 2. SQLite DB에 개별 대화 저장 (audio_file은 더미값 사용)
        dummy_filename = f"script_{title[:20]}_{meeting_date.replace(' ', '_').replace(':', '-')}.txt"
        meeting_id = db.save_stt_to_db(segments, dummy_filename, title, meeting_date, owner_id)

        # 3. Vector DB에 대화록을 의미적 청크로 저장
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
                    segments=all_segments
                )
                print(f"✅ meeting_chunks에 저장 완료 (meeting_id: {meeting_id})")

                # 4. 청킹 저장 후 바로 문단 요약 자동 생성
                try:
                    print(f"🤖 문단 요약 자동 생성 시작 (meeting_id: {meeting_id})")

                    # transcript_text 생성
                    transcript_text = " ".join([row['segment'] for row in all_segments])

                    # subtopic_generate를 이용해 요약 생성
                    summary_content = stt_manager.subtopic_generate(first_segment['title'], transcript_text)

                    if summary_content:
                        # meeting_subtopic DB에 저장
                        vdb_manager.add_meeting_as_subtopic(
                            meeting_id=meeting_id,
                            title=first_segment['title'],
                            meeting_date=first_segment['meeting_date'],
                            audio_file=first_segment['audio_file'],
                            summary_content=summary_content
                        )
                        print(f"✅ 문단 요약 생성 및 저장 완료 (meeting_id: {meeting_id})")

                        # 5. 문단 요약 성공 후 마인드맵 키워드 자동 생성
                        try:
                            print(f"🗺️ 마인드맵 키워드 자동 생성 시작 (meeting_id: {meeting_id})")

                            # 마인드맵 키워드 생성
                            mindmap_content = stt_manager.extract_mindmap_keywords(
                                summary_content,
                                first_segment['title']
                            )

                            if mindmap_content:
                                # SQLite DB에 저장
                                db.save_mindmap(
                                    meeting_id=meeting_id,
                                    mindmap_content=mindmap_content
                                )
                                print(f"✅ 마인드맵 키워드 생성 및 저장 완료 (meeting_id: {meeting_id})")
                            else:
                                print(f"⚠️ 마인드맵 키워드 생성 실패 (meeting_id: {meeting_id})")

                        except Exception as mindmap_error:
                            print(f"⚠️ 마인드맵 키워드 자동 생성 중 오류 발생: {mindmap_error}")
                            import traceback
                            traceback.print_exc()
                            # 마인드맵 생성 실패해도 업로드는 성공으로 처리

                    else:
                        print(f"⚠️ 문단 요약 생성 실패 (meeting_id: {meeting_id})")

                except Exception as summary_error:
                    print(f"⚠️ 문단 요약 자동 생성 중 오류 발생: {summary_error}")
                    import traceback
                    traceback.print_exc()
                    # 요약 생성 실패해도 업로드는 성공으로 처리

        except Exception as vdb_error:
            print(f"❌ Vector DB 저장 중 오류 발생: {vdb_error}")
            import traceback
            traceback.print_exc()
            # 벡터 DB 저장에 실패해도 주요 기능은 계속 동작하도록 일단 넘어감

        # 5. 결과를 보여주는 뷰어 페이지로 리디렉션
        if is_ajax:
            return jsonify({
                "success": True,
                "meeting_id": meeting_id,
                "redirect_url": url_for('view_meeting', meeting_id=meeting_id)
            })
        else:
            return redirect(url_for('view_meeting', meeting_id=meeting_id))

    except Exception as e:
        if is_ajax:
            return jsonify({
                "success": False,
                "error": f"서버 처리 중 오류가 발생했습니다: {e}"
            }), 500
        else:
            return render_template("index.html", error=f"서버 처리 중 오류가 발생했습니다: {e}")

@app.route("/upload", methods=["POST"])
@login_required
def upload_and_process():
    """SSE 방식으로 실시간 진행 상황을 스트리밍"""
    import datetime
    import threading
    
    # 현재 로그인한 사용자 ID
    owner_id = session['user_id']
    
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
    
    # 파일 준비 및 저장 (generator 외부에서 먼저 저장)
    original_filename = secure_filename(file.filename)
    unique_id = uuid.uuid4().hex[:8]
    filename = f"{unique_id}_{original_filename}"
    original_file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    meeting_date = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_ext = filename.rsplit('.', 1)[1].lower()
    is_video = (file_ext == 'mp4')

    # 파일 저장 (generator 시작 전에 완료)
    timestamp = dt.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    thread_id = threading.current_thread().name
    print(f"\n[{timestamp}][{thread_id}] 📥 업로드 요청 수신")
    print(f"[{timestamp}][{thread_id}] 💾 파일 저장 시작: {filename}")
    file.save(original_file_path)
    timestamp = dt.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{timestamp}][{thread_id}] ✅ 파일 저장 완료: {filename}")

    # Generator 함수로 SSE 스트리밍
    def generate():
        thread_id = threading.current_thread().name

        try:
            # Step 1: 파일 업로드 완료
            yield f"data: {json.dumps({'step': 'upload', 'message': '파일 업로드가 완료되었습니다...', 'icon': '📤'})}\n\n"
            
            # 비디오 파일인 경우 오디오로 변환
            temp_audio_path = None
            if is_video:
                print(f"🎬 비디오 파일 감지: {filename}")
                base_name = filename.rsplit('.', 1)[0]
                temp_audio_filename = f"{base_name}_audio.wav"
                temp_audio_path = os.path.join(app.config["UPLOAD_FOLDER"], temp_audio_filename)
                
                if not convert_video_to_audio(original_file_path, temp_audio_path):
                    yield f"data: {json.dumps({'step': 'error', 'message': '비디오를 오디오로 변환하는 데 실패했습니다.'})}\n\n"
                    return
                
                audio_path_for_stt = temp_audio_path
            else:
                audio_path_for_stt = original_file_path
            
            # Step 2: 음성 인식
            yield f"data: {json.dumps({'step': 'stt', 'message': '회의 음성을 텍스트로 변환하고 있습니다...', 'icon': '🎤'})}\n\n"
            
            segments = stt_manager.transcribe_audio(audio_path_for_stt)
            
            if not segments:
                if temp_audio_path and os.path.exists(temp_audio_path):
                    os.remove(temp_audio_path)
                yield f"data: {json.dumps({'step': 'error', 'message': '음성 인식에 실패했습니다.'})}\n\n"
                return
            
            # SQLite DB에 저장
            meeting_id = db.save_stt_to_db(segments, filename, title, meeting_date, owner_id)
            
            # 임시 WAV 파일 삭제
            if temp_audio_path and os.path.exists(temp_audio_path):
                try:
                    os.remove(temp_audio_path)
                    print(f"🗑️  임시 오디오 파일 삭제 완료: {temp_audio_path}")
                except Exception as e:
                    print(f"⚠️ 임시 오디오 파일 삭제 실패: {e}")
            
            # Vector DB에 저장
            all_segments = db.get_segments_by_meeting_id(meeting_id)
            if all_segments:
                first_segment = all_segments[0]
                vdb_manager.add_meeting_as_chunk(
                    meeting_id=meeting_id,
                    title=first_segment['title'],
                    meeting_date=first_segment['meeting_date'],
                    audio_file=first_segment['audio_file'],
                    segments=all_segments
                )
                print(f"✅ meeting_chunks에 저장 완료 (meeting_id: {meeting_id})")
                
                # Step 3: 문단 요약 생성
                yield f"data: {json.dumps({'step': 'summary', 'message': '회의 내용을 분석하고 요약하고 있습니다...', 'icon': '📝'})}\n\n"
                
                try:
                    print(f"🤖 문단 요약 자동 생성 시작 (meeting_id: {meeting_id})")
                    transcript_text = " ".join([row['segment'] for row in all_segments])
                    summary_content = stt_manager.subtopic_generate(first_segment['title'], transcript_text)
                    
                    if summary_content:
                        vdb_manager.add_meeting_as_subtopic(
                            meeting_id=meeting_id,
                            title=first_segment['title'],
                            meeting_date=first_segment['meeting_date'],
                            audio_file=first_segment['audio_file'],
                            summary_content=summary_content
                        )
                        print(f"✅ 문단 요약 생성 및 저장 완료 (meeting_id: {meeting_id})")
                        
                        # Step 4: 마인드맵 생성
                        yield f"data: {json.dumps({'step': 'mindmap', 'message': '마인드맵을 생성하고 있습니다...', 'icon': '🗺️'})}\n\n"
                        
                        try:
                            print(f"🗺️ 마인드맵 키워드 자동 생성 시작 (meeting_id: {meeting_id})")
                            mindmap_content = stt_manager.extract_mindmap_keywords(
                                summary_content,
                                first_segment['title']
                            )
                            
                            if mindmap_content:
                                db.save_mindmap(
                                    meeting_id=meeting_id,
                                    mindmap_content=mindmap_content
                                )
                                print(f"✅ 마인드맵 키워드 생성 및 저장 완료 (meeting_id: {meeting_id})")
                            else:
                                print(f"⚠️ 마인드맵 키워드 생성 실패 (meeting_id: {meeting_id})")
                        
                        except Exception as mindmap_error:
                            print(f"⚠️ 마인드맵 키워드 자동 생성 중 오류 발생: {mindmap_error}")
                            import traceback
                            traceback.print_exc()
                    
                    else:
                        print(f"⚠️ 문단 요약 생성 실패 (meeting_id: {meeting_id})")
                
                except Exception as summary_error:
                    print(f"⚠️ 문단 요약 자동 생성 중 오류 발생: {summary_error}")
                    import traceback
                    traceback.print_exc()
            
            # Step 5: 완료
            redirect_url = url_for('view_meeting', meeting_id=meeting_id)
            yield f"data: {json.dumps({'step': 'complete', 'message': '노트 생성이 완료되었습니다!', 'redirect': redirect_url, 'icon': '✅'})}\n\n"
        
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'step': 'error', 'message': f'서버 처리 중 오류가 발생했습니다: {str(e)}'})}\n\n"
    
    return Response(stream_with_context(generate()), mimetype='text/event-stream')



@app.route("/notes")
@login_required
def list_notes():
    try:
        # 사용자별 노트 목록 조회 (본인 노트 + 공유받은 노트)
        user_id = session['user_id']
        meetings = get_user_meetings(user_id)
        return render_template("notes.html", meetings=meetings)
    except Exception as e:
        return render_template("index.html", error=f"노트 목록을 불러오는 중 오류가 발생했습니다: {e}")

@app.route("/notes_json")
@login_required
def list_notes_json():
    """노트 목록을 JSON으로 반환 (업로드 상태 확인용)"""
    try:
        user_id = session['user_id']
        meetings = get_user_meetings(user_id)
        return jsonify({"success": True, "meetings": meetings})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/shared-notes")
@login_required
def shared_notes():
    try:
        # 공유받은 노트만 조회
        user_id = session['user_id']
        meetings = get_shared_meetings(user_id)
        return render_template("shared-notes.html", meetings=meetings)
    except Exception as e:
        return render_template("index.html", error=f"공유 노트 목록을 불러오는 중 오류가 발생했습니다: {e}")

@app.route("/view/<string:meeting_id>")
@login_required
def view_meeting(meeting_id):
    # 권한 체크
    user_id = session['user_id']
    if not can_access_meeting(user_id, meeting_id):
        return "⛔ 접근 권한이 없습니다.", 403

    return render_template("viewer.html", meeting_id=meeting_id)

@app.route("/api/meeting/<string:meeting_id>")
@login_required
def get_meeting_data(meeting_id):
    try:
        # 권한 체크
        user_id = session['user_id']
        if not can_access_meeting(user_id, meeting_id):
            return jsonify({"success": False, "error": "접근 권한이 없습니다."}), 403

        rows = db.get_meeting_by_id(meeting_id)
        if not rows:
            return jsonify({"success": False, "error": "해당 회의를 찾을 수 없습니다."}), 404

        transcript = [dict(row) for row in rows]
        audio_file = rows[0]['audio_file']
        title = rows[0]['title']
        meeting_date = rows[0]['meeting_date']

        # 참석자 목록 추출 (중복 제거된 speaker_label 목록)
        # transcript는 이미 dict로 변환되었으므로 .get() 사용 가능
        participants = list(set([t['speaker_label'] for t in transcript if t.get('speaker_label')]))
        participants.sort()  # 알파벳/숫자 순으로 정렬

        # 화자별 점유율 계산
        speaker_share_data = calculate_speaker_share(meeting_id)

        # 수정 권한 확인 (owner 또는 admin만 수정 가능)
        can_edit = can_edit_meeting(user_id, meeting_id)

        return jsonify({
            "success": True,
            "meeting_id": meeting_id,
            "title": title,
            "meeting_date": meeting_date,
            "participants": participants,
            "audio_url": url_for('uploaded_file', filename=audio_file),
            "transcript": transcript,
            "speaker_share": speaker_share_data,
            "can_edit": can_edit
        })
    except Exception as e:
        return jsonify({"success": False, "error": f"DB 조회 오류: {e}"}), 500

@app.route("/api/summarize/<string:meeting_id>", methods=["POST"])
@login_required
def summarize_meeting(meeting_id):
    try:
        # 권한 체크
        user_id = session['user_id']
        if not can_access_meeting(user_id, meeting_id):
            return jsonify({"success": False, "error": "접근 권한이 없습니다."}), 403
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
@admin_required
def retriever_page():
    """리트리버 테스트 페이지를 렌더링합니다. (Admin 전용 디버그 메뉴)"""
    return render_template("retriever.html")

@app.route("/script-input")
def script_input_page():
    """스크립트 입력 페이지를 렌더링합니다."""
    return render_template("script_input.html")

@app.route("/test-summary")
@admin_required
def test_summary_page():
    """요약 생성 테스트 페이지 (Admin 전용)"""
    return render_template("test_summary.html")

@app.route("/api/test_summary", methods=["POST"])
@admin_required
def test_summary_api():
    """요약 생성 테스트 API"""
    try:
        data = request.get_json()
        text = data.get("text", "").strip()
        title = data.get("title", "테스트 회의").strip()

        if not text:
            return jsonify({"success": False, "error": "텍스트를 입력해주세요."}), 400

        # subtopic_generate 호출
        summary_content = stt_manager.subtopic_generate(title, text)

        if summary_content:
            return jsonify({
                "success": True,
                "summary": summary_content
            })
        else:
            return jsonify({"success": False, "error": "요약 생성에 실패했습니다."}), 500

    except Exception as e:
        print(f"❌ 요약 테스트 API 오류: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/test-mindmap")
@admin_required
def test_mindmap_page():
    """마인드맵 생성 테스트 페이지 (Admin 전용)"""
    return render_template("test_mindmap.html")

@app.route("/api/test_mindmap", methods=["POST"])
@admin_required
def test_mindmap_api():
    """마인드맵 생성 테스트 API"""
    try:
        data = request.get_json()
        summary_text = data.get("summary_text", "").strip()
        title = data.get("title", "테스트 회의").strip()

        if not summary_text:
            return jsonify({"success": False, "error": "요약 텍스트를 입력해주세요."}), 400

        # extract_mindmap_keywords 호출
        mindmap_content = stt_manager.extract_mindmap_keywords(summary_text, title)

        if mindmap_content:
            return jsonify({
                "success": True,
                "mindmap": mindmap_content
            })
        else:
            return jsonify({"success": False, "error": "마인드맵 생성에 실패했습니다."}), 500

    except Exception as e:
        print(f"❌ 마인드맵 테스트 API 오류: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/test-stt")
@admin_required
def test_stt_page():
    """STT 테스트 페이지 (Admin 전용)"""
    return render_template("test_stt.html")

@app.route("/test-minutes")
@admin_required
def test_minutes_page():
    """회의록 생성 테스트 페이지 (Admin 전용)"""
    return render_template("test_minutes.html")

@app.route("/api/test_minutes", methods=["POST"])
@admin_required
def test_minutes_api():
    """회의록 생성 테스트 API"""
    try:
        data = request.get_json()
        summary_text = data.get("summary_text", "").strip()
        transcript_text = data.get("transcript_text", "").strip()
        title = data.get("title", "테스트 회의").strip()

        if not summary_text:
            return jsonify({"success": False, "error": "요약 텍스트를 입력해주세요."}), 400

        # transcript_text가 없으면 summary_text를 사용
        if not transcript_text:
            transcript_text = summary_text

        # meeting_date는 현재 시간으로 설정
        from datetime import datetime
        meeting_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # generate_minutes 호출
        minutes_content = stt_manager.generate_minutes(title, transcript_text, summary_text, meeting_date)

        if minutes_content:
            return jsonify({
                "success": True,
                "minutes": minutes_content
            })
        else:
            return jsonify({"success": False, "error": "회의록 생성에 실패했습니다."}), 500

    except Exception as e:
        print(f"❌ 회의록 테스트 API 오류: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/test_stt", methods=["POST"])
@admin_required
def test_stt_api():
    """STT 테스트 API"""
    try:
        # 파일 확인
        if 'audio_file' not in request.files:
            return jsonify({"success": False, "error": "파일을 선택해주세요."}), 400

        file = request.files['audio_file']
        if file.filename == '':
            return jsonify({"success": False, "error": "파일을 선택해주세요."}), 400

        if not allowed_file(file.filename):
            return jsonify({"success": False, "error": "지원하지 않는 파일 형식입니다."}), 400

        # 임시 파일로 저장
        import tempfile
        import os
        from datetime import datetime

        temp_dir = tempfile.gettempdir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_stt_{timestamp}_{file.filename}"
        temp_path = os.path.join(temp_dir, filename)

        file.save(temp_path)

        # STT 처리
        segments = stt_manager.transcribe_audio(temp_path, file.filename)

        # 임시 파일 삭제
        if os.path.exists(temp_path):
            os.remove(temp_path)

        if segments:
            # 세그먼트를 텍스트로 변환
            transcript_text = "\n".join([
                f"Speaker {seg['speaker_label']}: {seg['segment']}"
                for seg in segments
            ])

            return jsonify({
                "success": True,
                "segments": segments,
                "transcript_text": transcript_text
            })
        else:
            return jsonify({"success": False, "error": "음성 인식에 실패했습니다."}), 500

    except Exception as e:
        print(f"❌ STT 테스트 API 오류: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/check_summary/<string:meeting_id>", methods=["GET"])
@login_required
def check_summary(meeting_id):
    """문단 요약 존재 여부 확인 API"""
    try:
        # 권한 체크
        user_id = session['user_id']
        if not can_access_meeting(user_id, meeting_id):
            return jsonify({"success": False, "error": "접근 권한이 없습니다."}), 403
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

@app.route("/api/mindmap/<string:meeting_id>", methods=["GET"])
@login_required
def get_mindmap(meeting_id):
    """마인드맵 키워드 조회 API"""
    try:
        # 권한 체크
        user_id = session['user_id']
        if not can_access_meeting(user_id, meeting_id):
            return jsonify({"success": False, "error": "접근 권한이 없습니다."}), 403

        # SQLite DB에서 마인드맵 조회
        mindmap_content = db.get_mindmap_by_meeting_id(meeting_id)

        if mindmap_content:
            return jsonify({
                "success": True,
                "has_mindmap": True,
                "mindmap_content": mindmap_content
            })
        else:
            return jsonify({
                "success": True,
                "has_mindmap": False,
                "message": "마인드맵이 아직 생성되지 않았습니다."
            })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": f"마인드맵 조회 중 오류 발생: {str(e)}"}), 500

@app.route("/api/get_minutes/<string:meeting_id>", methods=["GET"])
@login_required
def get_minutes(meeting_id):
    """회의록 조회 API - SQLite DB에서 저장된 회의록을 조회합니다."""
    try:
        # 권한 체크
        user_id = session['user_id']
        if not can_access_meeting(user_id, meeting_id):
            return jsonify({"success": False, "error": "접근 권한이 없습니다."}), 403
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
@login_required
def generate_minutes(meeting_id):
    """회의록 생성 API - 청킹된 문서를 기반으로 정식 회의록을 생성하고 DB에 저장합니다."""
    try:
        # 권한 체크
        user_id = session['user_id']
        if not can_access_meeting(user_id, meeting_id):
            return jsonify({"success": False, "error": "접근 권한이 없습니다."}), 403
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

        # 4. stt_manager의 generate_minutes를 이용해 회의록 생성 (meeting_date 전달)
        minutes_content = stt_manager.generate_minutes(title, transcript_text, chunks_content, meeting_date)

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
@login_required
def delete_meeting(meeting_id):
    """
    회의와 관련된 모든 데이터를 삭제합니다.
    - SQLite DB: meeting_dialogues, meeting_minutes
    - Vector DB: meeting_chunk, meeting_subtopic
    - 오디오 파일
    """
    try:
        # 권한 체크 (소유자 또는 admin만 삭제 가능)
        user_id = session['user_id']
        if not can_access_meeting(user_id, meeting_id):
            return jsonify({"success": False, "error": "접근 권한이 없습니다."}), 403
        # VectorDBManager의 delete_from_collection(db_type="all")로 모든 데이터 삭제
        result = vdb_manager.delete_from_collection(db_type="all", meeting_id=meeting_id)
        return jsonify(result)

    except ValueError as e:
        # meeting_id를 찾을 수 없는 경우
        return jsonify({"success": False, "error": str(e)}), 404
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": f"삭제 중 오류 발생: {str(e)}"}), 500

@app.route("/api/chat", methods=["POST"])
@login_required
def chat():
    """
    챗봇 API 엔드포인트
    사용자 질문을 받아 회의록 기반으로 답변을 생성합니다.

    보안:
    - meeting_id가 있으면: 해당 노트만 검색 (권한 체크)
    - meeting_id가 없으면: 사용자가 접근 가능한 모든 노트에서 검색
    """
    try:
        user_id = session['user_id']
        # 요청 데이터 가져오기
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "error": "요청 데이터가 없습니다."}), 400

        query = data.get("query", "").strip()
        meeting_id = data.get("meeting_id")  # 선택적

        if not query:
            return jsonify({"success": False, "error": "질문을 입력해주세요."}), 400

        # meeting_id가 제공된 경우 권한 체크
        if meeting_id:
            if not can_access_meeting(user_id, meeting_id):
                return jsonify({"success": False, "error": "접근 권한이 없습니다."}), 403
            accessible_meeting_ids = None
        else:
            # meeting_id가 없으면 사용자가 접근 가능한 모든 노트 ID 조회
            accessible_meeting_ids = get_user_accessible_meeting_ids(user_id)
            if not accessible_meeting_ids:
                return jsonify({
                    "success": True,
                    "answer": "접근 가능한 노트가 없습니다. 먼저 회의록을 업로드해주세요.",
                    "sources": []
                }), 200

        # ChatManager를 통해 질의 처리
        result = chat_manager.process_query(
            query,
            meeting_id=meeting_id,
            accessible_meeting_ids=accessible_meeting_ids
        )

        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 500

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": f"챗봇 처리 중 오류가 발생했습니다: {str(e)}"
        }), 500

# 공유 기능 API
@app.route("/api/share/<string:meeting_id>", methods=["POST"])
@login_required
def share_meeting_api(meeting_id):
    """노트 공유 API"""
    try:
        user_id = session['user_id']

        # 권한 체크 (소유자만 공유 가능)
        if not can_access_meeting(user_id, meeting_id):
            return jsonify({"success": False, "error": "접근 권한이 없습니다."}), 403

        # 공유받을 사용자 이메일
        data = request.get_json()
        shared_with_email = data.get('email', '').strip()

        if not shared_with_email:
            return jsonify({"success": False, "error": "이메일을 입력해주세요."}), 400

        # 공유 처리
        result = share_meeting(meeting_id, user_id, shared_with_email)
        return jsonify(result)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": f"공유 중 오류가 발생했습니다: {str(e)}"}), 500

@app.route("/api/shared_users/<string:meeting_id>", methods=["GET"])
@login_required
def get_shared_users_api(meeting_id):
    """노트를 공유받은 사용자 목록 조회"""
    try:
        user_id = session['user_id']

        # 권한 체크
        if not can_access_meeting(user_id, meeting_id):
            return jsonify({"success": False, "error": "접근 권한이 없습니다."}), 403

        # 공유받은 사용자 목록
        shared_users = get_shared_users(meeting_id)
        return jsonify({"success": True, "shared_users": shared_users})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": f"조회 중 오류가 발생했습니다: {str(e)}"}), 500

@app.route("/api/unshare/<string:meeting_id>/<int:user_id>", methods=["POST"])
@login_required
def unshare_meeting_api(meeting_id, user_id):
    """노트 공유 해제 API"""
    try:
        owner_id = session['user_id']

        # 권한 체크 (소유자만 공유 해제 가능)
        if not can_access_meeting(owner_id, meeting_id):
            return jsonify({"success": False, "error": "접근 권한이 없습니다."}), 403

        # 공유 해제
        result = remove_share(meeting_id, owner_id, user_id)
        return jsonify(result)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": f"공유 해제 중 오류가 발생했습니다: {str(e)}"}), 500

@app.route("/api/update_title/<string:meeting_id>", methods=["POST"])
@login_required
def update_title_api(meeting_id):
    """노트 제목 수정 API"""
    try:
        user_id = session['user_id']

        # 1. 권한 체크 (owner 또는 admin만 수정 가능)
        if not can_edit_meeting(user_id, meeting_id):
            return jsonify({"success": False, "error": "제목을 수정할 권한이 없습니다. (소유자만 수정 가능)"}), 403

        # 2. 제목 가져오기
        data = request.get_json()
        new_title = data.get('title', '').strip()

        # 3. 제목 validation
        if not new_title:
            return jsonify({"success": False, "error": "제목을 입력해주세요."}), 400

        if len(new_title) > 100:
            return jsonify({"success": False, "error": "제목은 100자 이하로 입력해주세요."}), 400

        # 4. DB 업데이트 (ChromaDB + SQLite)
        result = db.update_meeting_title(meeting_id, new_title)

        if result['success']:
            vector_info = result.get('updated_vector', {})
            return jsonify({
                "success": True,
                "message": "제목이 성공적으로 수정되었습니다.",
                "new_title": new_title,
                "updated_dialogues": result['updated_dialogues'],
                "updated_minutes": result['updated_minutes'],
                "updated_vector_chunks": vector_info.get('updated_chunks', 0),
                "updated_vector_subtopics": vector_info.get('updated_subtopics', 0)
            })
        else:
            return jsonify({"success": False, "error": result.get('error', '알 수 없는 오류')}), 500

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": f"제목 수정 중 오류가 발생했습니다: {str(e)}"}), 500

@app.route("/api/update_date/<string:meeting_id>", methods=["POST"])
@login_required
def update_date_api(meeting_id):
    """노트 날짜 수정 API"""
    try:
        user_id = session['user_id']

        # 1. 권한 체크 (owner 또는 admin만 수정 가능)
        if not can_edit_meeting(user_id, meeting_id):
            return jsonify({"success": False, "error": "날짜를 수정할 권한이 없습니다. (소유자만 수정 가능)"}), 403

        # 2. 날짜 가져오기
        data = request.get_json()
        new_date = data.get('date', '').strip()

        # 3. 날짜 validation
        if not new_date:
            return jsonify({"success": False, "error": "날짜를 입력해주세요."}), 400

        # 날짜 형식 검증 (YYYY-MM-DD HH:MM:SS)
        try:
            import datetime
            # 브라우저에서 받는 형식: "YYYY-MM-DDTHH:MM"
            # DB에 저장할 형식: "YYYY-MM-DD HH:MM:SS"

            # ISO 형식 파싱 시도 (T가 포함된 경우)
            if 'T' in new_date:
                parsed_date = datetime.datetime.strptime(new_date, "%Y-%m-%dT%H:%M")
            else:
                # 이미 DB 형식인 경우
                parsed_date = datetime.datetime.strptime(new_date, "%Y-%m-%d %H:%M:%S")

            # DB 형식으로 변환 (초 단위는 00으로 설정)
            formatted_date = parsed_date.strftime("%Y-%m-%d %H:%M:%S")

        except ValueError as ve:
            return jsonify({"success": False, "error": f"날짜 형식이 올바르지 않습니다: {str(ve)}"}), 400

        # 4. DB 업데이트 (ChromaDB + SQLite)
        result = db.update_meeting_date(meeting_id, formatted_date)

        if result['success']:
            vector_info = result.get('updated_vector', {})
            return jsonify({
                "success": True,
                "message": "날짜가 성공적으로 수정되었습니다.",
                "new_date": formatted_date,
                "updated_dialogues": result['updated_dialogues'],
                "updated_minutes": result['updated_minutes'],
                "updated_vector_chunks": vector_info.get('updated_chunks', 0),
                "updated_vector_subtopics": vector_info.get('updated_subtopics', 0)
            })
        else:
            return jsonify({"success": False, "error": result.get('error', '알 수 없는 오류')}), 500

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": f"날짜 수정 중 오류가 발생했습니다: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)