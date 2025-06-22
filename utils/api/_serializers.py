from rest_framework import serializers
from django.conf import settings


class UsernameSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    real_name = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        self.need_real_name = kwargs.pop("need_real_name", False)
        super().__init__(*args, **kwargs)

    def get_real_name(self, obj):
        return obj.userprofile.real_name if self.need_real_name else None
    
    def get_avatar(self, obj):
        if hasattr(obj, 'userprofile') and obj.userprofile.avatar:
            avatar_path = obj.userprofile.avatar
            # If we have a request context, build absolute URL
            request = self.context.get('request')
            if request and not avatar_path.startswith('http'):
                return request.build_absolute_uri(avatar_path)
            return avatar_path
        return None
