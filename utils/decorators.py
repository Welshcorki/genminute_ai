"""
Flask 라우트 데코레이터
- @login_required: 로그인 필수
- @admin_required: Admin 권한 필수
"""

from functools import wraps
from flask import session, redirect, url_for, jsonify, request
from utils.user_manager import is_admin


def login_required(f):
    """
    로그인이 필요한 라우트에 사용하는 데코레이터

    사용법:
        @app.route('/protected')
        @login_required
        def protected_route():
            user_id = session['user_id']
            return "Protected content"
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # API 요청인 경우 JSON 응답
            if request.path.startswith('/api/'):
                return jsonify({'error': '로그인이 필요합니다.', 'redirect': '/login'}), 401

            # HTML 페이지 요청인 경우 로그인 페이지로 리다이렉트
            return redirect(url_for('login_page'))

        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    """
    Admin 권한이 필요한 라우트에 사용하는 데코레이터

    사용법:
        @app.route('/admin/debug')
        @admin_required
        def debug_page():
            return "Admin only content"
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 로그인 체크
        if 'user_id' not in session:
            # API 요청인 경우 JSON 응답
            if request.path.startswith('/api/'):
                return jsonify({'error': '로그인이 필요합니다.', 'redirect': '/login'}), 401

            # HTML 페이지 요청인 경우 로그인 페이지로 리다이렉트
            return redirect(url_for('login_page'))

        # Admin 권한 체크
        user_id = session['user_id']
        if not is_admin(user_id):
            # API 요청인 경우 JSON 응답
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Admin 권한이 필요합니다.'}), 403

            # HTML 페이지 요청인 경우 403 에러 페이지
            return "⛔ 접근 권한이 없습니다. Admin 권한이 필요합니다.", 403

        return f(*args, **kwargs)

    return decorated_function


def optional_login(f):
    """
    로그인이 선택적인 라우트에 사용하는 데코레이터
    로그인 여부와 상관없이 접근 가능하지만, 로그인 상태를 확인할 수 있음

    사용법:
        @app.route('/home')
        @optional_login
        def home():
            if 'user_id' in session:
                return f"Welcome back, {session['user_id']}"
            return "Welcome, guest"
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 로그인 체크는 하지 않고, 세션만 확인
        return f(*args, **kwargs)

    return decorated_function
