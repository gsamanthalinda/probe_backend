from uuid import UUID
from fastapi import APIRouter, Depends, status, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()
from sqlalchemy.orm import Session
from database import get_db
from probe.schemas.user import UserCreate, UserRead, UserRegisterResponse, UserUpdate, ForgotPasswordRequest, ResetPasswordConfirm, MFAVerifyRequest, MFADisableRequest, MFALoginRequest, MFASetupResponse, TokenResponse, LoginRequest, RefreshResponse
from probe.services.user import (
    get_user,
    create_user,
    update_user,
    delete_user,
    authenticate_user,
    list_users,
    request_password_reset,
    reset_password_with_token,
    logout_user,
    refresh_token,
    setup_mfa,
    verify_and_enable_mfa,
    disable_mfa_user,
)
from probe.services.auth import get_current_user, get_admin_user, limiter

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserRegisterResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def route_create_user(
    request: Request,
    data: UserCreate,
    db: Session = Depends(get_db),
):
    user = create_user(db, data)
    return {"user": user}


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def route_login(request: Request, data: LoginRequest, db: Session = Depends(get_db)):
    return authenticate_user(db, data.email, data.password, None)


@router.post("/login/2fa", response_model=TokenResponse)
@limiter.limit("10/minute")
def route_login_2fa(request: Request, data: MFALoginRequest, db: Session = Depends(get_db)):
    return authenticate_user(db, data.email, data.password, data.code)


@router.post("/refresh-token", response_model=RefreshResponse)
@limiter.limit("10/minute")
def route_refresh_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    token_str = credentials.credentials
    return refresh_token(db, token_str)


@router.post("/logout")
@limiter.limit("10/minute")
def route_logout(
    request: Request,
    current_user=Depends(get_current_user),
):
    logout_user(current_user.user_id)
    return {"message": "Logged out successfully."}


@router.post("/forgot-password")
@limiter.limit("5/minute")
def route_forgot_password(
    request: Request,
    data: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    return request_password_reset(db, data)


@router.get("/reset-password", response_class=HTMLResponse)
def route_reset_password_form(request: Request, token: str = ""):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Reset Password - HERckers</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 500px; margin: 50px auto; padding: 20px; }}
            h2 {{ color: #2c3e50; }}
            input {{ width: 100%; padding: 12px; margin: 8px 0; box-sizing: border-box; border: 1px solid #ddd; border-radius: 4px; }}
            button {{ background-color: #3498db; color: white; padding: 12px 24px; border: none; border-radius: 4px; cursor: pointer; width: 100%; }}
            button:hover {{ background-color: #2980b9; }}
            .error {{ color: #e74c3c; }}
            .success {{ color: #27ae60; }}
        </style>
    </head>
    <body>
        <h2>Reset Your Password</h2>
        <div id="message"></div>
        <form id="resetForm">
            <input type="hidden" id="token" value="{token}" />
            <input type="password" id="new_password" placeholder="New Password" required minlength="8" />
            <input type="password" id="confirm_password" placeholder="Confirm New Password" required minlength="8" />
            <button type="submit">Reset Password</button>
        </form>
        <script>
            document.getElementById('resetForm').addEventListener('submit', async (e) => {{
                e.preventDefault();
                const token = document.getElementById('token').value;
                const newPassword = document.getElementById('new_password').value;
                const confirmPassword = document.getElementById('confirm_password').value;
                const messageDiv = document.getElementById('message');

                if (newPassword !== confirmPassword) {{
                    messageDiv.innerHTML = '<p class="error">Passwords do not match</p>';
                    return;
                }}

                try {{
                    const response = await fetch('/users/reset-password', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ token: token, new_password: newPassword }})
                    }});
                    const data = await response.json();
                    if (response.ok) {{
                        messageDiv.innerHTML = '<p class="success">Password reset successful! You can now login.</p>';
                        document.getElementById('resetForm').reset();
                    }} else {{
                        messageDiv.innerHTML = '<p class="error">' + (data.detail || 'Error resetting password') + '</p>';
                    }}
                }} catch (error) {{
                    messageDiv.innerHTML = '<p class="error">Network error. Please try again.</p>';
                }}
            }});
        </script>
    </body>
    </html>
    """


@router.post("/reset-password")
@limiter.limit("5/minute")
def route_reset_password(
    request: Request,
    data: ResetPasswordConfirm,
    db: Session = Depends(get_db),
):
    return reset_password_with_token(db, data)


@router.get("/", response_model=list[UserRead])
@limiter.limit("30/minute")
def route_list_users(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_admin_user),
):
    return list_users(db, current_user)


@router.get("/{user_id}", response_model=UserRead)
@limiter.limit("60/minute")
def route_get_user(
    request: Request,
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_user(db, user_id, current_user)


@router.patch("/{user_id}", response_model=UserRead)
@limiter.limit("10/minute")
def route_update_user(
    request: Request,
    user_id: UUID,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return update_user(db, user_id, data, current_user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/minute")
def route_delete_user(
    request: Request,
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    delete_user(db, user_id, current_user)


@router.post("/2fa/setup", response_model=MFASetupResponse)
@limiter.limit("10/minute")
def route_setup_mfa(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    setup_data = setup_mfa(db, current_user.user_id)
    return setup_data


@router.post("/2fa/verify")
@limiter.limit("10/minute")
def route_verify_mfa(
    request: Request,
    data: MFAVerifyRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = verify_and_enable_mfa(db, current_user.user_id, data.code)
    return result


@router.post("/2fa/disable")
@limiter.limit("10/minute")
def route_disable_mfa(
    request: Request,
    data: MFADisableRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = disable_mfa_user(db, current_user.user_id, data.password, data.code)
    return result
