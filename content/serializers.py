from rest_framework import serializers

from content.models import AnalysisTemplate, Article, Meeting, TGChat, TGMessage, TGPost, Recipe
from content.utils import generate_article_video_src, generate_meeting_src_link
from srbc.serializers.general import UserProfileSerializer


class TGChatSerializer(serializers.ModelSerializer):
    members = UserProfileSerializer(many=True)

    class Meta:
        model = TGChat
        fields = (
            "id",
            "code",
            "title",
            "start_date", "end_date",
            "chat_type",
            "members"
        )


class TGChatSerializerShort(serializers.ModelSerializer):
    class Meta:
        model = TGChat
        fields = (
            "id",
            "code",
            "title",
            "start_date", "end_date",
            "chat_type",
        )


class TGPostSerializer(serializers.ModelSerializer):
    author = UserProfileSerializer()
    channel = TGChatSerializerShort()

    class Meta:
        model = TGPost
        fields = (
            "id", "text", "author", "created_at", "posted_at",
            "channel_id", "is_private", "is_global", "is_posted", "image_url", "channel"
        )


class TGPostShortSerializer(serializers.ModelSerializer):
    author = UserProfileSerializer()
    channel = TGChatSerializerShort()

    class Meta:
        model = TGPost
        fields = (
            "id", "author", "created_at", "posted_at",
            "is_private", "is_global", "is_posted",
            "channel"
        )


class TGMessageSerializer(serializers.ModelSerializer):
    author = UserProfileSerializer()
    assigned = UserProfileSerializer()
    answer = TGPostSerializer()

    class Meta:
        model = TGMessage
        fields = ("id", "text", "author", "assigned", "created_at", "answer", "message_type", "status",)


class MeetingSerializer(serializers.ModelSerializer):
    src_link = serializers.SerializerMethodField(method_name='generate_src_link')

    def generate_src_link(self, obj):
        return generate_meeting_src_link(obj=obj)

    class Meta:
        model = Meeting
        fields = ("id", "title", "type", "date", "description", "src_link", "duration", "audio_author", "audio_album")


class ArticlesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ("id", "title", "main_image")


class ArticleSerializer(serializers.ModelSerializer):
    video_src = serializers.SerializerMethodField(method_name='generate_video_links')

    def generate_video_links(self, obj):
        return generate_article_video_src(obj=obj)

    class Meta:
        model = Article
        fields = ("id", "title", "main_image", "text", "has_video", "video_src")


class AnalysisTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisTemplate
        fields = ('id', 'title', 'text', 'display_mode', 'adjust_calories', 'adjust_protein', 'add_fat',
                  'adjust_fruits', 'adjust_carb_bread_min', 'adjust_carb_bread_late', 'adjust_carb_carb_vegs',
                  'adjust_carb_sub_breakfast', 'adjust_carb_mix_vegs')
        
class RecipesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'title', 'body', 'comment', 'tags')

