"""
Firebase Authentication 모듈
- Firebase Admin SDK 초기화
- ID 토큰 검증
"""

import os
import firebase_admin
from firebase_admin import credentials, auth
from typing import Optional, Dict

# Firebase Admin SDK 초기화 (한 번만 실행)
_firebase_initialized = False

def initialize_firebase():
    """Firebase Admin SDK 초기화"""
    global _firebase_initialized

    if _firebase_initialized:
        return

    try:
        # firebase-adminsdk.json 파일 경로
        cred_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'firebase-adminsdk.json')

        if not os.path.exists(cred_path):
            raise FileNotFoundError(
                f"Firebase Admin SDK 인증 파일을 찾을 수 없습니다: {cred_path}\n"
                "Firebase Console에서 서비스 계정 비공개 키를 다운로드하고 "
                "프로젝트 루트에 'firebase-adminsdk.json'으로 저장해주세요."
            )

        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        _firebase_initialized = True
        print("✅ Firebase Admin SDK 초기화 완료")

    except Exception as e:
        print(f"❌ Firebase 초기화 실패: {e}")
        raise


def verify_id_token(id_token: str) -> Optional[Dict[str, str]]:
    """
    Firebase ID 토큰 검증

    Args:
        id_token: 프론트엔드에서 받은 Firebase ID Token

    Returns:
        성공 시: {
            'uid': 사용자 고유 ID,
            'email': 이메일,
            'name': 이름,
            'picture': 프로필 사진 URL
        }
        실패 시: None
    """
    try:
        # Firebase에서 토큰 검증
        decoded_token = auth.verify_id_token(id_token)

        # 사용자 정보 추출
        user_info = {
            'uid': decoded_token['uid'],
            'email': decoded_token.get('email'),
            'name': decoded_token.get('name'),
            'picture': decoded_token.get('picture')
        }

        return user_info

    except auth.InvalidIdTokenError:
        print("❌ 유효하지 않은 ID 토큰")
        return None
    except auth.ExpiredIdTokenError:
        print("❌ 만료된 ID 토큰")
        return None
    except Exception as e:
        print(f"❌ 토큰 검증 실패: {e}")
        return None


def get_user_by_uid(uid: str) -> Optional[Dict]:
    """
    Firebase UID로 사용자 정보 조회

    Args:
        uid: Firebase 사용자 고유 ID

    Returns:
        사용자 정보 또는 None
    """
    try:
        user = auth.get_user(uid)
        return {
            'uid': user.uid,
            'email': user.email,
            'name': user.display_name,
            'picture': user.photo_url,
            'email_verified': user.email_verified
        }
    except auth.UserNotFoundError:
        return None
    except Exception as e:
        print(f"❌ 사용자 조회 실패: {e}")
        return None
