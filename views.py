from django.db.models import Q
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from apps.api.exceptions import BadRequest
from apps.api.filters import CommonProfileFilter, CommonCommunityFilter, CommonAudioFilter, CommonVideoFilter, \
    CommonTextFilter
from apps.communities.models import Community
from apps.communities.api.serializers import CommunityBriefSerializer
from apps.galleries.api.serializers import VideoItemBriefSerializer, AudioItemBriefSerializer, TextItemBriefSerializer
from apps.galleries.models import VideoItem, AudioItem, TextItem
from apps.posts.api.serializers import PostSerializer
from apps.posts.models import Post
from apps.userprofile.api.serializers import UserProfileRelationsBriefSerializer
from apps.userprofile.models import UserProfile


class CommonSearchAPI(generics.ListAPIView):

    permission_classes = (IsAuthenticated,)

    SERIALIZER_CLASSES_BY_SCOPE = {
        'profiles': UserProfileRelationsBriefSerializer,
        'communities': CommunityBriefSerializer,
        'video': VideoItemBriefSerializer,
        'audio': AudioItemBriefSerializer,
        'text': TextItemBriefSerializer,
        'posts': PostSerializer,
    }

    def get_filter_dict(self):
        name = self.request.query_params.get('name')
        filter_dict = self.request.GET.copy()
        filter_dict['name'] = name
        return filter_dict

    def get_serializer(self, key, *args, **kwargs):
        serializer_class = self.SERIALIZER_CLASSES_BY_SCOPE.get(key)
        if serializer_class is None:
            raise BadRequest("Unexpected scope: {}".format(key))
        kwargs['context'] = self.get_serializer_context()
        return serializer_class(*args, **kwargs)

    def get_profiles_queryset(self):
        queryset = UserProfile.objects.all()
        scope_2 = self.request.query_params.get('scope_2')
        if scope_2:
            queryset = {
                'friends': queryset.filter(
                    user__in=self.request.user.userprofile.friends.all()
                ),
                'others': queryset.exclude(
                    Q(user__in=self.request.user.userprofile.friends.all()) |
                    Q(user=self.request.user)
                ),
                'followeds': queryset.filter(
                    user__in=self.request.user.userprofile.followed.all()
                ).exclude(
                    user__in=self.request.user.userprofile.friends.all()
                ),
                'followers': self.request.user.followers.all().exclude(
                    user__in=self.request.user.userprofile.friends.all()
                )
            }.get(scope_2)
            if queryset is None:
                raise BadRequest("Unexpected scope_2: {}".format(scope_2))

        return CommonProfileFilter(self.get_filter_dict(), queryset=queryset).qs

    def get_communities_queryset(self):
        queryset = Community.objects.not_deleted()
        return CommonCommunityFilter(self.get_filter_dict(), queryset=queryset).qs

    def get_video_queryset(self):
        return CommonVideoFilter(
            self.get_filter_dict(), queryset=VideoItem.objects.visible_to_all()
        ).qs.order_by('-date_created')

    def get_audio_queryset(self):
        return CommonAudioFilter(
            self.get_filter_dict(), queryset=AudioItem.objects.visible_to_all()
        ).qs.order_by('-date_created')

    def get_text_queryset(self):
        return CommonTextFilter(
            self.get_filter_dict(), queryset=TextItem.objects.visible_to_all()
        ).qs.order_by('-date_created')

    def get_posts_queryset(self):
        return Post.objects.not_deleted().filter(
            title__istartswith=self.request.query_params.get('name')
        )

    def list(self, request, *args, **kwargs):
        name = self.request.query_params.get('name')
        scope = self.request.query_params.get('scope')
        if scope:
            if scope not in ['profiles', 'communities', 'video', 'audio', 'text', 'posts']:
                raise BadRequest("Unexpected scope: {}".format(scope))

            qs_function = getattr(self, 'get_{}_queryset'.format(scope))
            if scope != 'posts':
                return Response({
                    'found_items': self.get_serializer(scope, qs_function(), many=True).data,
                    'found_items_count': qs_function().count()
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'found_posts': self.get_serializer(
                        'posts',
                        Post.objects.not_deleted().filter(title__istartswith=name),
                        many=True
                    ).data,
                    'found_items_count': len(qs_function())
                }, status=status.HTTP_200_OK)
        else:
            kwargs = {}
            for key in ['profiles', 'communities', 'video', 'audio', 'text']:
                qs_function = getattr(self, 'get_{}_queryset'.format(key))
                kwargs['found_{}'.format(key)] = self.get_serializer(key, qs_function(), many=True).data
                kwargs['found_{}_count'.format(key)] = qs_function().count()
            kwargs['found_posts'] = self.get_serializer(
                'posts',
                self.get_posts_queryset(),
                many=True
            ).data
            kwargs['found_posts_count'] = self.get_posts_queryset().count()
            return Response(kwargs, status=status.HTTP_200_OK)
