import os
from datetime import timedelta, date
from importlib import import_module

import qrcode
from PIL import Image
from django.conf import settings
from django.contrib import auth
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.utils.timezone import now
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from otpauth import TOTP

from problem.models import Problem
from utils.constants import ContestRuleType
from options.options import SysOptions
from utils.api import APIView, validate_serializer, CSRFExemptAPIView
from utils.captcha import Captcha
from utils.shortcuts import rand_str, img2base64, datetime2str
from ..decorators import login_required
from ..models import User, UserProfile, AdminType, UserStreak, DailyCheckIn
from ..serializers import (ApplyResetPasswordSerializer, ResetPasswordSerializer,
                           UserChangePasswordSerializer, UserLoginSerializer,
                           UserRegisterSerializer, UsernameOrEmailCheckSerializer,
                           RankInfoSerializer, UserChangeEmailSerializer, SSOSerializer)
from ..serializers import (TwoFactorAuthCodeSerializer, UserProfileSerializer,
                           EditUserProfileSerializer, ImageUploadForm)
from ..tasks import send_email_async


class UserProfileAPI(APIView):
    @method_decorator(ensure_csrf_cookie)
    def get(self, request, **kwargs):
        """
        判断是否登录， 若登录返回用户信息
        """
        user = request.user
        if not user.is_authenticated:
            return self.success()
        show_real_name = False
        username = request.GET.get("username")
        try:
            if username:
                user = User.objects.get(username=username, is_disabled=False)
            else:
                user = request.user
                # api返回的是自己的信息，可以返real_name
                show_real_name = True
        except User.DoesNotExist:
            return self.error("User does not exist")
        return self.success(UserProfileSerializer(user.userprofile, show_real_name=show_real_name, context={'request': request}).data)

    @validate_serializer(EditUserProfileSerializer)
    @login_required
    def put(self, request):
        data = request.data
        user_profile = request.user.userprofile
        for k, v in data.items():
            # Skip avatar field if it's empty to prevent overwriting existing avatar
            if k == 'avatar' and not v:
                continue
            setattr(user_profile, k, v)
        user_profile.save()
        return self.success(UserProfileSerializer(user_profile, show_real_name=True, context={'request': request}).data)


class AvatarUploadAPI(APIView):
    request_parsers = ()

    @login_required
    def post(self, request):
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            avatar = form.cleaned_data["image"]
        else:
            return self.error("Invalid file content")
        if avatar.size > 2 * 1024 * 1024:
            return self.error("Picture is too large (max 2MB)")
        suffix = os.path.splitext(avatar.name)[-1].lower()
        if suffix not in [".gif", ".jpg", ".jpeg", ".bmp", ".png"]:
            return self.error("Unsupported file format")

        user_profile = request.user.userprofile
        
        # Delete old avatar if it's not the default one
        old_avatar = user_profile.avatar
        if old_avatar and not old_avatar.endswith("default.png"):
            old_avatar_path = old_avatar.replace(settings.AVATAR_URI_PREFIX, settings.AVATAR_UPLOAD_DIR)
            if os.path.exists(old_avatar_path):
                try:
                    os.remove(old_avatar_path)
                except:
                    pass  # Ignore errors when deleting old avatar

        # Generate new filename
        name = rand_str(10) + suffix
        avatar_path = os.path.join(settings.AVATAR_UPLOAD_DIR, name)
        
        # Save and process the image
        try:
            # Open and process the image
            img = Image.open(avatar)
            
            # Convert RGBA to RGB if necessary
            if img.mode == 'RGBA':
                # Create a white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
                img = background
            elif img.mode not in ['RGB', 'L']:
                img = img.convert('RGB')
            
            # Calculate dimensions for a square crop
            width, height = img.size
            min_dimension = min(width, height)
            
            # Calculate crop box for center square
            left = (width - min_dimension) // 2
            top = (height - min_dimension) // 2
            right = left + min_dimension
            bottom = top + min_dimension
            
            # Crop to square
            img = img.crop((left, top, right, bottom))
            
            # Resize to 200x200 pixels
            img = img.resize((200, 200), Image.Resampling.LANCZOS)
            
            # Save the processed image
            if suffix == '.png':
                img.save(avatar_path, 'PNG', optimize=True)
            else:
                img.save(avatar_path, 'JPEG', quality=90, optimize=True)
                
        except Exception as e:
            return self.error(f"Failed to process image: {str(e)}")

        # Update user profile
        user_profile.avatar = f"{settings.AVATAR_URI_PREFIX}/{name}"
        user_profile.save()
        
        # Build absolute URL for the response
        avatar_url = request.build_absolute_uri(user_profile.avatar)
        
        return self.success({
            "avatar": avatar_url,
            "message": "Avatar uploaded successfully"
        })
    
    @login_required
    def delete(self, request):
        """Delete user's custom avatar and revert to default"""
        user_profile = request.user.userprofile
        
        # Delete current avatar if it's not the default one
        if user_profile.avatar and not user_profile.avatar.endswith("default.png"):
            avatar_path = user_profile.avatar.replace(settings.AVATAR_URI_PREFIX, settings.AVATAR_UPLOAD_DIR)
            if os.path.exists(avatar_path):
                try:
                    os.remove(avatar_path)
                except:
                    pass
        
        # Set back to default avatar
        user_profile.avatar = f"{settings.AVATAR_URI_PREFIX}/default.png"
        user_profile.save()
        
        # Build absolute URL for the response
        avatar_url = request.build_absolute_uri(user_profile.avatar)
        
        return self.success({
            "avatar": avatar_url,
            "message": "Avatar reset to default"
        })


class TwoFactorAuthAPI(APIView):
    @login_required
    def get(self, request):
        """
        Get QR code
        """
        user = request.user
        if user.two_factor_auth:
            return self.error("2FA is already turned on")
        token = rand_str()
        user.tfa_token = token
        user.save()

        label = f"{SysOptions.website_name_shortcut}:{user.username}"
        image = qrcode.make(TOTP(token).to_uri("totp", label, SysOptions.website_name.replace(" ", "")))
        return self.success(img2base64(image))

    @login_required
    @validate_serializer(TwoFactorAuthCodeSerializer)
    def post(self, request):
        """
        Open 2FA
        """
        code = request.data["code"]
        user = request.user
        if TOTP(user.tfa_token).valid_totp(code):
            user.two_factor_auth = True
            user.save()
            return self.success("Succeeded")
        else:
            return self.error("Invalid code")

    @login_required
    @validate_serializer(TwoFactorAuthCodeSerializer)
    def put(self, request):
        code = request.data["code"]
        user = request.user
        if not user.two_factor_auth:
            return self.error("2FA is already turned off")
        if TOTP(user.tfa_token).valid_totp(code):
            user.two_factor_auth = False
            user.save()
            return self.success("Succeeded")
        else:
            return self.error("Invalid code")


class CheckTFARequiredAPI(APIView):
    @validate_serializer(UsernameOrEmailCheckSerializer)
    def post(self, request):
        """
        Check TFA is required
        """
        data = request.data
        result = False
        if data.get("username"):
            try:
                user = User.objects.get(username=data["username"])
                result = user.two_factor_auth
            except User.DoesNotExist:
                pass
        return self.success({"result": result})


class UserLoginAPI(APIView):
    @validate_serializer(UserLoginSerializer)
    def post(self, request):
        """
        User login api
        """
        data = request.data
        try:
            user = auth.authenticate(username=data["username"], password=data["password"])
            print(data, user)
            # None is returned if username or password is wrong
            if user is None:
                return self.error("Invalid username or password")
                
            if user.is_disabled:
                return self.error("Your account has been disabled")
                
            if not user.two_factor_auth:
                auth.login(request, user)
                return self.success("Succeeded")

            # `tfa_code` not in post data
            if user.two_factor_auth and "tfa_code" not in data:
                return self.error("tfa_required")

            if TOTP(user.tfa_token).valid_totp(data["tfa_code"]):
                auth.login(request, user)
                return self.success("Succeeded")
            else:
                return self.error("Invalid two factor verification code")
        except AttributeError as e:
            # This can happen if the user object is malformed
            return self.error(f"Invalid user data: {str(e)}")
        except AssertionError as e:
            if "database connection isn't set to UTC" in str(e):
                # Log the timezone configuration error
                import logging
                logger = logging.getLogger(__name__)
                logger.error("Database timezone configuration error: %s", str(e))
                return self.error("Server configuration error. Please contact the administrator.")
            raise  # Re-raise if it's a different assertion error
        except Exception as e:
            # Log the actual error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Login error for user {data.get('username')}: {str(e)}")
            return self.error("A server error occurred during login. Please try again later.")


class UserLogoutAPI(APIView):
    def get(self, request):
        auth.logout(request)
        return self.success()


class UsernameOrEmailCheck(APIView):
    @validate_serializer(UsernameOrEmailCheckSerializer)
    def post(self, request):
        """
        check username or email is duplicate
        """
        data = request.data
        # True means already exist.
        result = {
            "username": False,
            "email": False
        }
        if data.get("username"):
            result["username"] = User.objects.filter(username=data["username"].lower()).exists()
        if data.get("email"):
            result["email"] = User.objects.filter(email=data["email"].lower()).exists()
        return self.success(result)


class UserRegisterAPI(APIView):
    @validate_serializer(UserRegisterSerializer)
    def post(self, request):
        """
        User register api
        """
        if not SysOptions.allow_register:
            return self.error("Register function has been disabled by admin")

        data = request.data
        data["username"] = data["username"].lower()
        data["email"] = data["email"].lower()
        captcha = Captcha(request)
        if not captcha.check(data["captcha"]):
            return self.error("Invalid captcha")
        if User.objects.filter(username=data["username"]).exists():
            return self.error("Username already exists")
        if User.objects.filter(email=data["email"]).exists():
            return self.error("Email already exists")
        user = User.objects.create(username=data["username"], email=data["email"])
        user.set_password(data["password"])
        user.save()
        UserProfile.objects.create(user=user)
        return self.success("Succeeded")


class UserChangeEmailAPI(APIView):
    @validate_serializer(UserChangeEmailSerializer)
    @login_required
    def post(self, request):
        data = request.data
        user = auth.authenticate(username=request.user.username, password=data["password"])
        if user:
            if user.two_factor_auth:
                if "tfa_code" not in data:
                    return self.error("tfa_required")
                if not TOTP(user.tfa_token).valid_totp(data["tfa_code"]):
                    return self.error("Invalid two factor verification code")
            data["new_email"] = data["new_email"].lower()
            if User.objects.filter(email=data["new_email"]).exists():
                return self.error("The email is owned by other account")
            user.email = data["new_email"]
            user.save()
            return self.success("Succeeded")
        else:
            return self.error("Wrong password")


class UserChangePasswordAPI(APIView):
    @validate_serializer(UserChangePasswordSerializer)
    @login_required
    def post(self, request):
        """
        User change password api
        """
        data = request.data
        username = request.user.username
        user = auth.authenticate(username=username, password=data["old_password"])
        if user:
            if user.two_factor_auth:
                if "tfa_code" not in data:
                    return self.error("tfa_required")
                if not TOTP(user.tfa_token).valid_totp(data["tfa_code"]):
                    return self.error("Invalid two factor verification code")
            user.set_password(data["new_password"])
            user.save()
            return self.success("Succeeded")
        else:
            return self.error("Invalid old password")


class ApplyResetPasswordAPI(APIView):
    @validate_serializer(ApplyResetPasswordSerializer)
    def post(self, request):
        if request.user.is_authenticated:
            return self.error("You have already logged in, are you kidding me? ")
        data = request.data
        captcha = Captcha(request)
        if not captcha.check(data["captcha"]):
            return self.error("Invalid captcha")
        try:
            user = User.objects.get(email__iexact=data["email"])
        except User.DoesNotExist:
            return self.error("User does not exist")
        if user.reset_password_token_expire_time and 0 < int(
                (user.reset_password_token_expire_time - now()).total_seconds()) < 20 * 60:
            return self.error("You can only reset password once per 20 minutes")
        user.reset_password_token = rand_str()
        user.reset_password_token_expire_time = now() + timedelta(minutes=20)
        user.save()
        render_data = {
            "username": user.username,
            "website_name": SysOptions.website_name,
            "link": f"{SysOptions.website_base_url}/reset-password/{user.reset_password_token}"
        }
        email_html = render_to_string("reset_password_email.html", render_data)
        send_email_async.send(from_name=SysOptions.website_name_shortcut,
                              to_email=user.email,
                              to_name=user.username,
                              subject="Reset your password",
                              content=email_html)
        return self.success("Succeeded")


class ResetPasswordAPI(APIView):
    @validate_serializer(ResetPasswordSerializer)
    def post(self, request):
        data = request.data
        captcha = Captcha(request)
        if not captcha.check(data["captcha"]):
            return self.error("Invalid captcha")
        try:
            user = User.objects.get(reset_password_token=data["token"])
        except User.DoesNotExist:
            return self.error("Token does not exist")
        if user.reset_password_token_expire_time < now():
            return self.error("Token has expired")
        user.reset_password_token = None
        user.two_factor_auth = False
        user.set_password(data["password"])
        user.save()
        return self.success("Succeeded")


class SessionManagementAPI(APIView):
    @login_required
    def get(self, request):
        engine = import_module(settings.SESSION_ENGINE)
        session_store = engine.SessionStore
        current_session = request.session.session_key
        session_keys = request.user.session_keys
        result = []
        modified = False
        for key in session_keys[:]:
            session = session_store(key)
            # session does not exist or is expiry
            if not session._session:
                session_keys.remove(key)
                modified = True
                continue

            s = {}
            if current_session == key:
                s["current_session"] = True
            s["ip"] = session["ip"]
            s["user_agent"] = session["user_agent"]
            s["last_activity"] = datetime2str(session["last_activity"])
            s["session_key"] = key
            result.append(s)
        if modified:
            request.user.save()
        return self.success(result)

    @login_required
    def delete(self, request):
        session_key = request.GET.get("session_key")
        if not session_key:
            return self.error("Parameter Error")
        request.session.delete(session_key)
        if session_key in request.user.session_keys:
            request.user.session_keys.remove(session_key)
            request.user.save()
            return self.success("Succeeded")
        else:
            return self.error("Invalid session_key")


class UserRankAPI(APIView):
    def get(self, request):
        rule_type = request.GET.get("rule")
        if rule_type not in ContestRuleType.choices():
            rule_type = ContestRuleType.ACM
        profiles = UserProfile.objects.filter(user__admin_type=AdminType.REGULAR_USER, user__is_disabled=False) \
            .select_related("user")
        if rule_type == ContestRuleType.ACM:
            profiles = profiles.filter(submission_number__gt=0).order_by("-accepted_number", "submission_number")
        else:
            profiles = profiles.filter(total_score__gt=0).order_by("-total_score")
        return self.success(self.paginate_data(request, profiles, RankInfoSerializer))


class ProfileProblemDisplayIDRefreshAPI(APIView):
    @login_required
    def get(self, request):
        profile = request.user.userprofile
        acm_problems = profile.acm_problems_status.get("problems", {})
        oi_problems = profile.oi_problems_status.get("problems", {})
        ids = list(acm_problems.keys()) + list(oi_problems.keys())
        if not ids:
            return self.success()
        display_ids = Problem.objects.filter(id__in=ids, visible=True).values_list("_id", flat=True)
        id_map = dict(zip(ids, display_ids))
        for k, v in acm_problems.items():
            v["_id"] = id_map[k]
        for k, v in oi_problems.items():
            v["_id"] = id_map[k]
        profile.save(update_fields=["acm_problems_status", "oi_problems_status"])
        return self.success()


class OpenAPIAppkeyAPI(APIView):
    @login_required
    def post(self, request):
        user = request.user
        if not user.open_api:
            return self.error("OpenAPI function is truned off for you")
        api_appkey = rand_str()
        user.open_api_appkey = api_appkey
        user.save()
        return self.success({"appkey": api_appkey})


class SSOAPI(CSRFExemptAPIView):
    @login_required
    def get(self, request):
        token = rand_str()
        request.user.auth_token = token
        request.user.save()
        return self.success({"token": token})

    @method_decorator(csrf_exempt)
    @validate_serializer(SSOSerializer)
    def post(self, request):
        try:
            user = User.objects.get(auth_token=request.data["token"])
        except User.DoesNotExist:
            return self.error("User does not exist")
        return self.success({"username": user.username, "avatar": user.userprofile.avatar, "admin_type": user.admin_type})


class UserStreakAPI(APIView):
    @login_required
    def get(self, request):
        """Get user's streak information"""
        try:
            user = request.user
            
            # Get or create user streak
            streak, created = UserStreak.objects.get_or_create(user=user)
            
            # Get check-in days for current month
            today = date.today()
            first_day = today.replace(day=1)
            check_ins = DailyCheckIn.objects.filter(
                user=user,
                check_in_date__gte=first_day
            ).values_list('check_in_date', flat=True)
            
            return self.success({
                'current_streak': streak.current_streak,
                'best_streak': streak.best_streak,
                'last_check_in': streak.last_check_in.isoformat() if streak.last_check_in else None,
                'check_in_days': [d.isoformat() for d in check_ins]
            })
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in user streak API: {str(e)}")
            return self.error(f"An error occurred: {str(e)}")


class DailyCheckInAPI(APIView):
    @login_required
    def post(self, request):
        """Record daily check-in"""
        try:
            user = request.user
            today = date.today()
            
            # Log the attempt
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Check-in attempt for user: {user.username} on {today}")
            
            # Check if already checked in today
            existing_checkin = DailyCheckIn.objects.filter(user=user, check_in_date=today).exists()
            if existing_checkin:
                logger.info(f"User {user.username} already checked in today")
                return self.error('Already checked in today')
            
            # Create check-in record
            checkin = DailyCheckIn.objects.create(user=user, check_in_date=today)
            logger.info(f"Created check-in for user {user.username}: ID={checkin.id}, date={checkin.check_in_date}")
            
            # Update streak
            streak, created = UserStreak.objects.get_or_create(user=user)
            
            # Check if streak continues
            yesterday = today - timedelta(days=1)
            
            # Check if user checked in yesterday to continue the streak
            yesterday_checkin_exists = DailyCheckIn.objects.filter(
                user=user,
                check_in_date=yesterday
            ).exists()
            
            if yesterday_checkin_exists and streak.current_streak > 0:
                # Continue streak
                streak.current_streak += 1
            else:
                # Start new streak
                streak.current_streak = 1
            
            # Update best streak if needed
            if streak.current_streak > streak.best_streak:
                streak.best_streak = streak.current_streak
            
            # Update last check-in time
            streak.last_check_in = now()
            streak.save()
            
            logger.info(f"Updated streak for user {user.username}: current={streak.current_streak}, best={streak.best_streak}")
            
            # Get updated check-in days
            first_day = today.replace(day=1)
            check_ins = DailyCheckIn.objects.filter(
                user=user,
                check_in_date__gte=first_day
            ).values_list('check_in_date', flat=True)
            
            logger.info(f"Check-in days for {user.username} this month: {[d.isoformat() for d in check_ins]}")
            
            return self.success({
                'current_streak': streak.current_streak,
                'best_streak': streak.best_streak,
                'last_check_in': streak.last_check_in.isoformat() if streak.last_check_in else None,
                'check_in_days': [d.isoformat() for d in check_ins]
            })
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in daily check-in: {str(e)}")
            return self.error(f"An error occurred: {str(e)}")


class CheckAuthAPI(APIView):
    def get(self, request):
        """Debug endpoint to check authentication status"""
        if request.user.is_authenticated:
            return self.success({
                'authenticated': True,
                'username': request.user.username,
                'user_id': request.user.id
            })
        else:
            return self.success({
                'authenticated': False,
                'message': 'User is not authenticated'
            })


class UserAvatarAPI(APIView):
    def get(self, request):
        """Get user avatar by username"""
        username = request.GET.get('username')
        if not username:
            return self.error("Username is required")
        
        try:
            user = User.objects.get(username=username)
            avatar_url = user.userprofile.avatar
            return self.success({
                'username': username,
                'avatar': avatar_url
            })
        except User.DoesNotExist:
            return self.error("User not found")


class UserStatusAPI(APIView):
    @login_required
    def get(self, request):
        """Get current user's status"""
        profile = request.user.userprofile
        return self.success({
            'status': profile.status,
            'status_message': profile.status_message,
            'mood_emoji': profile.mood_emoji,
            'mood_clear_at': profile.mood_clear_at.isoformat() if profile.mood_clear_at else None,
            'status_color': profile.status_color
        })
    
    @login_required
    @validate_serializer(EditUserProfileSerializer)
    def put(self, request):
        """Update user's status"""
        data = request.data
        profile = request.user.userprofile
        
        # Update only status-related fields
        status_fields = ['status', 'status_message', 'mood_emoji', 'mood_clear_at', 'status_color']
        
        for field in status_fields:
            if field in data:
                setattr(profile, field, data[field])
        
        profile.save()
        
        return self.success({
            'status': profile.status,
            'status_message': profile.status_message,
            'mood_emoji': profile.mood_emoji,
            'mood_clear_at': profile.mood_clear_at.isoformat() if profile.mood_clear_at else None,
            'status_color': profile.status_color
        })
