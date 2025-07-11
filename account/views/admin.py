import os
import re
import xlsxwriter

from django.db import transaction, IntegrityError
from django.db.models import Q
from django.http import HttpResponse
from django.contrib.auth.hashers import make_password

from submission.models import Submission
from utils.api import APIView, validate_serializer
from utils.shortcuts import rand_str

from ..decorators import super_admin_required
from ..models import AdminType, ProblemPermission, User, UserProfile
from ..serializers import EditUserSerializer, UserAdminSerializer, GenerateUserSerializer, CreateUserSerializer
from ..serializers import ImportUserSeralizer, SimpleCreateUserSerializer


class UserAdminAPI(APIView):
    @validate_serializer(ImportUserSeralizer)
    @super_admin_required
    def post(self, request):
        """
        Import User
        """
        data = request.data["users"]

        user_list = []
        for user_data in data:
            if len(user_data) != 4 or len(user_data[0]) > 32:
                return self.error(f"Error occurred while processing data '{user_data}'")
            user_list.append(User(username=user_data[0], password=make_password(user_data[1]), email=user_data[2]))

        try:
            with transaction.atomic():
                ret = User.objects.bulk_create(user_list)
                UserProfile.objects.bulk_create([UserProfile(user=ret[i], real_name=data[i][3]) for i in range(len(ret))])
            return self.success()
        except IntegrityError as e:
            # Extract detail from exception message
            #    duplicate key value violates unique constraint "user_username_key"
            #    DETAIL:  Key (username)=(root11) already exists.
            return self.error(str(e).split("\n")[1])

    @validate_serializer(EditUserSerializer)
    @super_admin_required
    def put(self, request):
        """
        Edit user api
        """
        data = request.data
        try:
            user = User.objects.get(id=data["id"])
        except User.DoesNotExist:
            return self.error("User does not exist")
        if User.objects.filter(username=data["username"].lower()).exclude(id=user.id).exists():
            return self.error("Username already exists")
        if User.objects.filter(email=data["email"].lower()).exclude(id=user.id).exists():
            return self.error("Email already exists")

        pre_username = user.username
        user.username = data["username"].lower()
        user.email = data["email"].lower()
        user.admin_type = data["admin_type"]
        user.is_disabled = data["is_disabled"]

        if data["admin_type"] == AdminType.ADMIN:
            user.problem_permission = data["problem_permission"]
        elif data["admin_type"] == AdminType.SUPER_ADMIN:
            user.problem_permission = ProblemPermission.ALL
        else:
            user.problem_permission = ProblemPermission.NONE

        if data["password"]:
            user.set_password(data["password"])

        if data["open_api"]:
            # Avoid reset user appkey after saving changes
            if not user.open_api:
                user.open_api_appkey = rand_str()
        else:
            user.open_api_appkey = None
        user.open_api = data["open_api"]

        if data["two_factor_auth"]:
            # Avoid reset user tfa_token after saving changes
            if not user.two_factor_auth:
                user.tfa_token = rand_str()
        else:
            user.tfa_token = None

        user.two_factor_auth = data["two_factor_auth"]

        user.save()
        if pre_username != user.username:
            Submission.objects.filter(username=pre_username).update(username=user.username)

        UserProfile.objects.filter(user=user).update(real_name=data["real_name"])
        return self.success(UserAdminSerializer(user).data)

    @super_admin_required
    def get(self, request):
        """
        User list api / Get user by id
        """
        user_id = request.GET.get("id")
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return self.error("User does not exist")
            return self.success(UserAdminSerializer(user).data)

        user = User.objects.all().order_by("-create_time")

        keyword = request.GET.get("keyword", None)
        if keyword:
            user = user.filter(Q(username__icontains=keyword) |
                               Q(userprofile__real_name__icontains=keyword) |
                               Q(email__icontains=keyword))
        return self.success(self.paginate_data(request, user, UserAdminSerializer))

    @super_admin_required
    def delete(self, request):
        id = request.GET.get("id")
        if not id:
            return self.error("Invalid Parameter, id is required")
        ids = id.split(",")
        if str(request.user.id) in ids:
            return self.error("Current user can not be deleted")
        User.objects.filter(id__in=ids).delete()
        return self.success()


class GenerateUserAPI(APIView):
    @super_admin_required
    def get(self, request):
        """
        download users excel
        """
        file_id = request.GET.get("file_id")
        if not file_id:
            return self.error("Invalid Parameter, file_id is required")
        if not re.match(r"^[a-zA-Z0-9]+$", file_id):
            return self.error("Illegal file_id")
        file_path = f"/tmp/{file_id}.xlsx"
        if not os.path.isfile(file_path):
            return self.error("File does not exist")
        with open(file_path, "rb") as f:
            raw_data = f.read()
        os.remove(file_path)
        response = HttpResponse(raw_data)
        response["Content-Disposition"] = "attachment; filename=users.xlsx"
        response["Content-Type"] = "application/xlsx"
        return response

    @validate_serializer(GenerateUserSerializer)
    @super_admin_required
    def post(self, request):
        """
        Generate User
        """
        data = request.data
        number_max_length = max(len(str(data["number_from"])), len(str(data["number_to"])))
        if number_max_length + len(data["prefix"]) + len(data["suffix"]) > 32:
            return self.error("Username should not more than 32 characters")
        if data["number_from"] > data["number_to"]:
            return self.error("Start number must be lower than end number")

        file_id = rand_str(8)
        filename = f"/tmp/{file_id}.xlsx"
        workbook = xlsxwriter.Workbook(filename)
        worksheet = workbook.add_worksheet()
        worksheet.set_column("A:B", 20)
        worksheet.write("A1", "Username")
        worksheet.write("B1", "Password")
        i = 1

        user_list = []
        for number in range(data["number_from"], data["number_to"] + 1):
            raw_password = rand_str(data["password_length"])
            user = User(username=f"{data['prefix']}{number}{data['suffix']}", password=make_password(raw_password))
            user.raw_password = raw_password
            user_list.append(user)

        try:
            with transaction.atomic():

                ret = User.objects.bulk_create(user_list)
                UserProfile.objects.bulk_create([UserProfile(user=user) for user in ret])
                for item in user_list:
                    worksheet.write_string(i, 0, item.username)
                    worksheet.write_string(i, 1, item.raw_password)
                    i += 1
                workbook.close()
                return self.success({"file_id": file_id})
        except IntegrityError as e:
            # Extract detail from exception message
            #    duplicate key value violates unique constraint "user_username_key"
            #    DETAIL:  Key (username)=(root11) already exists.
            return self.error(str(e).split("\n")[1])


class CreateUserAPI(APIView):
    @validate_serializer(CreateUserSerializer)
    @super_admin_required
    def post(self, request):
        """
        Create user directly
        """
        data = request.data
        
        # Check if username already exists
        if User.objects.filter(username=data["username"].lower()).exists():
            return self.error("Username already exists")
            
        # Check if email already exists
        if User.objects.filter(email=data["email"].lower()).exists():
            return self.error("Email already exists")

        # Create user
        user = User(
            username=data["username"].lower(),
            email=data["email"].lower(),
            admin_type=data["admin_type"],
            problem_permission=data["problem_permission"],
            open_api=data["open_api"],
            two_factor_auth=data["two_factor_auth"],
            is_disabled=data["is_disabled"]
        )
        user.set_password(data["password"])
        
        # Set TFA token if two factor auth is enabled
        if data["two_factor_auth"]:
            user.tfa_token = rand_str()
            
        # Set API key if open_api is enabled
        if data["open_api"]:
            user.open_api_appkey = rand_str()
            
        try:
            with transaction.atomic():
                user.save()
                # Create user profile
                UserProfile.objects.create(
                    user=user,
                    real_name=data["real_name"]
                )
            return self.success(UserAdminSerializer(user).data)
        except IntegrityError as e:
            return self.error(str(e).split("\n")[1])


class SimpleCreateUserAPI(APIView):
    @validate_serializer(SimpleCreateUserSerializer)
    @super_admin_required
    def post(self, request):
        """
        Simple create user API - only username, password, and real name required
        No authentication methods (2FA, API key) are enabled
        """
        data = request.data
        
        # Check if username already exists
        if User.objects.filter(username=data["username"].lower()).exists():
            return self.error("Username already exists")
        
        # Generate a default email if not provided
        default_email = f"{data['username'].lower()}@example.com"
        
        # Create user with minimal settings
        user = User(
            username=data["username"].lower(),
            email=default_email,
            admin_type=AdminType.REGULAR_USER,  # Default to regular user
            problem_permission=ProblemPermission.NONE,  # No special permissions
            open_api=False,  # No API access
            two_factor_auth=False,  # No 2FA
            is_disabled=False  # Account is active
        )
        user.set_password(data["password"])
        
        try:
            with transaction.atomic():
                user.save()
                # Create user profile with real name
                UserProfile.objects.create(
                    user=user,
                    real_name=data.get("real_name", "")
                )
            return self.success({
                "username": user.username,
                "email": user.email,
                "real_name": data.get("real_name", ""),
                "message": "User created successfully"
            })
        except IntegrityError as e:
            return self.error(f"Database error: {str(e)}")


class AdminListAPI(APIView):
    """Get list of admin users for assignment purposes"""
    
    @super_admin_required
    def get(self, request):
        """Get all admin users"""
        # Get all users with admin privileges
        admins = User.objects.filter(
            admin_type__in=[AdminType.ADMIN, AdminType.SUPER_ADMIN]
        ).select_related('userprofile').order_by('username')
        
        admin_data = []
        for admin in admins:
            # Count students assigned to this admin
            # Import here to avoid circular import
            try:
                from homework.models import AdminStudentRelation
                student_count = AdminStudentRelation.objects.filter(
                    admin=admin, 
                    is_active=True
                ).count()
            except ImportError:
                # If homework app is not available, just set count to 0
                student_count = 0
            
            admin_data.append({
                'id': admin.id,
                'username': admin.username,
                'email': admin.email,
                'real_name': admin.userprofile.real_name if hasattr(admin, 'userprofile') else '',
                'admin_type': admin.admin_type,
                'student_count': student_count
            })
        
        return self.success(admin_data)
