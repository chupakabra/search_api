from django.core.urlresolvers import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from apps.abstract.utils import print_response, JSON_TS, create_user_with_profile
from apps.communities.models import Community, CommunitySubject
from apps.galleries.models import VideoItem, AudioItem, TextItem
from apps.posts.models import Post


class CommonSearchAPITest(TestCase):

    def setUp(self):
        self.c = APIClient()

        self.user01, self.user01p = create_user_with_profile('user01@test.com')

    def create_search_items(self):
        self.found_user, self.found_userp = create_user_with_profile(
            'found_user@test.com',
            first_name="Found",
            last_name="User"
        )
        self.other_user, self.other_userp = create_user_with_profile(
            'other_user@test.com',
            first_name="Other",
            last_name="User"
        )

        self.community_subject = CommunitySubject.objects.create(
            name="whatever",
            code="whatever"
        )
        self.found_community = Community.objects.create(
            name="Found community",
            subject=self.community_subject,
            author=self.user01
        )
        self.other_community = Community.objects.create(
            name="Other community",
            subject=self.community_subject,
            author=self.user01
        )

        self.found_video_item = VideoItem.objects.create(
            author=self.user01,
            gallery=None,
            title="Found video",
            content_object=self.user01p,
            source="youtube",
            source_id="Youtube video",
            source_duration=43,
            source_cover_url='/home/rp/env/project/public/media/no_image.png',
            submitted=True
        )
        self.other_video_item = VideoItem.objects.create(
            author=self.user01,
            gallery=None,
            title="Other video",
            content_object=self.user01p,
            source="youtube",
            source_id="Youtube video",
            source_duration=43,
            source_cover_url='/home/rp/env/project/public/media/no_image.png',
            submitted=True
        )

        self.found_audio_item = AudioItem.objects.create(
            author=self.user01,
            gallery=None,
            title="Found audio",
            content_object=self.user01p,
            submitted=True
        )
        self.other_audio_item = AudioItem.objects.create(
            author=self.user01,
            gallery=None,
            title="Other audio",
            content_object=self.user01p,
            submitted=True
        )

        self.found_text_item = TextItem.objects.create(
            author=self.user01,
            gallery=None,
            title="Found text",
            content_object=self.user01p,
            submitted=True
        )
        self.other_text_item = TextItem.objects.create(
            author=self.user01,
            gallery=None,
            title="Other text",
            content_object=self.user01p,
            submitted=True
        )

        self.found_post = Post.objects.create(
            title="Found post",
            text="Found post text",
            author=self.user01,
            content_object=self.user01p
        )
        self.other_post = Post.objects.create(
            title="Other post",
            text="Other post text",
            author=self.user01,
            content_object=self.user01p
        )

    def search(self, **kwargs):
        return self.c.get(reverse('api_common_search'), kwargs)

    def get_uuids(self, data):
        return [i['uuid'] for i in data]

    def test_bad_scope(self):

        self.c.login(username=self.user01.username, password='111')

        response = self.search(name="Found", scope="bad_scope")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {
            'detail': "Unexpected scope: bad_scope"
        })

    def test_profiles_search(self):

        self.create_search_items()

        self.c.login(username=self.user01.username, password='111')

        response = self.search(name="Found", scope="profiles")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {
            'found_items_count': 1,
            'found_items': [
                {
                    'user': {
                        'uuid': self.found_userp.uuid_str(),
                        'first_name': "Found",
                        'last_name': "User",
                        'gender': "M",
                        'avatar': None
                    },
                    'status': {
                        'is_friend': False,
                        'is_follower': False,
                        'is_followed': False,
                        'is_blocked': False,
                        'is_inbox_request': False,
                        'is_outbox_request': False
                    }
                }
            ]
        })

    def test_bad_scope_2(self):

        self.c.login(username=self.user01.username, password='111')

        response = self.search(name="Found", scope="profiles", scope_2="bad_scope_2")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {
            'detail': "Unexpected scope_2: bad_scope_2"
        })

    def test_profiles_friends_search(self):
        self.c.login(username=self.user01.username, password='111')

        found_friend_user, found_friend_userp = create_user_with_profile(
            'found_friend_user@test.com',
            first_name="Found Friend",
            last_name="User"
        )
        other_friend_user, other_friend_userp = create_user_with_profile(
            'other_friend_user@test.com',
            first_name="Other Friend",
            last_name="User"
        )
        self.user01p.friend_user(found_friend_user)
        self.user01p.friend_user(other_friend_user)

        response = self.search(name="Found", scope="profiles", scope_2="friends")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {
            'found_items_count': 1,
            'found_items': [
                {
                    'user': {
                        'uuid': found_friend_userp.uuid_str(),
                        'first_name': "Found Friend",
                        'last_name': "User",
                        'gender': "M",
                        'avatar': None
                    },
                    'status': {
                        'is_friend': True,
                        'is_follower': False,
                        'is_followed': False,
                        'is_blocked': False,
                        'is_inbox_request': False,
                        'is_outbox_request': False
                    }
                }
            ]
        })

    def test_profiles_others_search(self):

        self.create_search_items()

        self.c.login(username=self.user01.username, password='111')

        found_friend_user, found_friend_userp = create_user_with_profile(
            'found_friend_user@test.com',
            first_name="Found Friend",
            last_name="User"
        )

        self.user01p.friend_user(found_friend_user)

        response = self.search(name="Found", scope="profiles", scope_2="others")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {
            'found_items_count': 1,
            'found_items': [
                {
                    'user': {
                        'uuid': self.found_userp.uuid_str(),
                        'first_name': "Found",
                        'last_name': "User",
                        'gender': "M",
                        'avatar': None
                    },
                    'status': {
                        'is_friend': False,
                        'is_follower': False,
                        'is_followed': False,
                        'is_blocked': False,
                        'is_inbox_request': False,
                        'is_outbox_request': False
                    }
                }
            ]
        })

    def test_profiles_followeds_search(self):
        self.c.login(username=self.user01.username, password='111')

        found_friend_user, found_friend_userp = create_user_with_profile(
            'found_friend_user@test.com',
            first_name="Found Friend",
            last_name="User"
        )
        self.user01p.friend_user(found_friend_user)

        found_followed_user, found_followed_userp = create_user_with_profile(
            'found_followed_user@test.com',
            first_name="Found Followed",
            last_name="User"
        )
        other_followed_user, other_followed_userp = create_user_with_profile(
            'other_followed_user@test.com',
            first_name="Other Followed",
            last_name="User"
        )
        self.user01p.follow_user(found_followed_user)
        self.user01p.follow_user(other_followed_user)

        response = self.search(name="Found", scope="profiles", scope_2="followeds")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {
            'found_items_count': 1,
            'found_items': [
                {
                    'user': {
                        'uuid': found_followed_userp.uuid_str(),
                        'first_name': "Found Followed",
                        'last_name': "User",
                        'gender': "M",
                        'avatar': None
                    },
                    'status': {
                        'is_friend': False,
                        'is_follower': False,
                        'is_followed': True,
                        'is_blocked': False,
                        'is_inbox_request': False,
                        'is_outbox_request': False
                    }
                }
            ]
        })

    def test_profiles_followers_search(self):
        self.c.login(username=self.user01.username, password='111')

        found_friend_user, found_friend_userp = create_user_with_profile(
            'found_friend_user@test.com',
            first_name="Found Friend",
            last_name="User"
        )
        self.user01p.friend_user(found_friend_user)

        found_follower_user, found_follower_userp = create_user_with_profile(
            'found_follower_user@test.com',
            first_name="Found Follower",
            last_name="User"
        )
        other_follower_user, other_follower_userp = create_user_with_profile(
            'other_follower_user@test.com',
            first_name="Other Follower",
            last_name="User"
        )
        found_follower_userp.follow_user(self.user01)
        other_follower_userp.follow_user(self.user01)

        response = self.search(name="Found", scope="profiles", scope_2="followers")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {
            'found_items_count': 1,
            'found_items': [
                {
                    'user': {
                        'uuid': found_follower_userp.uuid_str(),
                        'first_name': "Found Follower",
                        'last_name': "User",
                        'gender': "M",
                        'avatar': None
                    },
                    'status': {
                        'is_friend': False,
                        'is_follower': True,
                        'friendship_request_sent': False,
                        'is_followed': False,
                        'is_blocked': False,
                        'is_inbox_request': False,
                        'is_outbox_request': False
                    }
                }
            ]
        })

    def test_communities_search(self):

        self.create_search_items()

        self.c.login(username=self.user01.username, password='111')

        response = self.search(name="Found", scope="communities")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data, {
            'found_items_count': 1,
            'found_items': [
                {
                    'uuid': self.found_community.uuid_str(),
                    'name': "Found community",
                    'avatar': None,
                    'date_created': self.found_community.date_created.strftime(JSON_TS),
                    'closed': False,
                    'members_count': 1,
                    'official': False
                }
            ]
        })

    def test_video_search(self):

        self.create_search_items()

        self.c.login(username=self.user01.username, password='111')

        response = self.search(name="Found", scope="video")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {
            'found_items_count': 1,
            'found_items': [
                {
                    'uuid': self.found_video_item.uuid_str(),
                    'author': {
                        'uuid': self.user01p.uuid_str(),
                        'first_name': "FirstName",
                        'last_name': "LastName",
                        'gender': "M",
                        'avatar': None
                    },
                    'title': "Found video",
                    'description': None,
                    'gallery_uuid': None,
                    'date_created': self.found_video_item.date_created.strftime(JSON_TS),
                    'submitted': True,
                    'hidden': False,
                    'is_liked': False,
                    'target_type': 'profile',
                    'target_uuid': self.user01p.uuid_str(),
                    'source': "youtube",
                    'source_id': "Youtube video",
                    'source_title': None,
                    'source_description': None,
                    'source_duration': 43,
                    'source_cover_url': "/home/rp/env/project/public/media/no_image.png",
                    'language': "en",
                    'religion_stream': None,
                    'cover_image_url': None
                }
            ]
        })

    def test_audio_search(self):

        self.create_search_items()

        self.c.login(username=self.user01.username, password='111')

        response = self.search(name="Found", scope="audio")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {
            'found_items_count': 1,
            'found_items': [
                {
                    'uuid': self.found_audio_item.uuid_str(),
                    'author': {
                        'uuid': self.user01p.uuid_str(),
                        'first_name': "FirstName",
                        'last_name': "LastName",
                        'gender': "M",
                        'avatar': None
                    },
                    'title': "Found audio",
                    'description': None,
                    'gallery_uuid': None,
                    'date_created': self.found_audio_item.date_created.strftime(JSON_TS),
                    'submitted': True,
                    'hidden': False,
                    'is_liked': False,
                    'target_type': 'profile',
                    'target_uuid': self.user01p.uuid_str(),
                    'source': "",
                    'source_id': "",
                    'source_duration': None,
                    'language': "en",
                    'religion_stream': None,
                    'cover_image_url': None
                }
            ]
        })

    def test_text_search(self):

        self.create_search_items()

        self.c.login(username=self.user01.username, password='111')

        response = self.search(name="Found", scope="text")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {
            'found_items_count': 1,
            'found_items': [
                {
                    'uuid': self.found_text_item.uuid_str(),
                    'author': {
                        'uuid': self.user01p.uuid_str(),
                        'first_name': "FirstName",
                        'last_name': "LastName",
                        'gender': "M",
                        'avatar': None
                    },
                    'title': "Found text",
                    'description': None,
                    'gallery_uuid': None,
                    'date_created': self.found_text_item.date_created.strftime(JSON_TS),
                    'submitted': True,
                    'hidden': False,
                    'is_liked': False,
                    'target_type': 'profile',
                    'target_uuid': self.user01p.uuid_str(),
                    'category': "",
                    'source_file': None,
                    'source_author': None,
                    'source_issue_date': None,
                    'language': "en",
                    'religion_stream': None,
                    'cover_image_url': None
                }
            ]
        })

    def test_posts_search(self):

        self.create_search_items()

        self.c.login(username=self.user01.username, password='111')

        response = self.search(name="Found", scope="posts")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {
            'found_items_count': 1,
            'found_posts': [
                {
                    'uuid': self.found_post.uuid_str(),
                    'date_created': self.found_post.date_created.strftime(JSON_TS),
                    'author': {
                        'uuid': self.user01p.uuid_str(),
                        'first_name': "FirstName",
                        'last_name': "LastName",
                        'gender': "M",
                        'avatar': None
                    },
                    'title': "Found post",
                    'text': "Found post text",
                    'picture_items': [],
                    'video_items': [],
                    'audio_items': [],
                    'text_items': [],
                    'comments': [],
                    'comments_count': 0,
                    'is_liked': False,
                    'likes_count': 0,
                    'recent_likes': [],
                    'reposts': [],
                    'reposts_count': 0
                }
            ]
        })

    def test_all_search(self):

        self.create_search_items()

        self.c.login(username=self.user01.username, password='111')

        response = self.search(name="Found")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {
            'found_profiles_count': 1,
            'found_profiles': [
                {
                    'user': {
                        'uuid': self.found_userp.uuid_str(),
                        'first_name': "Found",
                        'last_name': "User",
                        'gender': "M",
                        'avatar': None
                    },
                    'status': {
                        'is_friend': False,
                        'is_follower': False,
                        'is_followed': False,
                        'is_blocked': False,
                        'is_inbox_request': False,
                        'is_outbox_request': False
                    }
                }
            ],
            'found_communities_count': 1,
            'found_communities': [
                {
                    'uuid': self.found_community.uuid_str(),
                    'name': "Found community",
                    'avatar': None,
                    'date_created': self.found_community.date_created.strftime(JSON_TS),
                    'closed': False,
                    'members_count': 1,
                    'official': False
                }
            ],
            'found_video_count': 1,
            'found_video': [
                {
                    'uuid': self.found_video_item.uuid_str(),
                    'author': {
                        'uuid': self.user01p.uuid_str(),
                        'first_name': "FirstName",
                        'last_name': "LastName",
                        'gender': "M",
                        'avatar': None
                    },
                    'title': "Found video",
                    'description': None,
                    'gallery_uuid': None,
                    'date_created': self.found_video_item.date_created.strftime(JSON_TS),
                    'submitted': True,
                    'hidden': False,
                    'is_liked': False,
                    'target_type': 'profile',
                    'target_uuid': self.user01p.uuid_str(),
                    'source': "youtube",
                    'source_id': "Youtube video",
                    'source_title': None,
                    'source_description': None,
                    'source_duration': 43,
                    'source_cover_url': "/home/rp/env/project/public/media/no_image.png",
                    'language': "en",
                    'religion_stream': None,
                    'cover_image_url': None
                }
            ],
            'found_audio_count': 1,
            'found_audio': [
                {
                    'uuid': self.found_audio_item.uuid_str(),
                    'author': {
                        'uuid': self.user01p.uuid_str(),
                        'first_name': "FirstName",
                        'last_name': "LastName",
                        'gender': "M",
                        'avatar': None
                    },
                    'title': "Found audio",
                    'description': None,
                    'gallery_uuid': None,
                    'date_created': self.found_audio_item.date_created.strftime(JSON_TS),
                    'submitted': True,
                    'hidden': False,
                    'is_liked': False,
                    'target_type': 'profile',
                    'target_uuid': self.user01p.uuid_str(),
                    'source': "",
                    'source_id': "",
                    'source_duration': None,
                    'language': "en",
                    'religion_stream': None,
                    'cover_image_url': None
                }
            ],
            'found_text_count': 1,
            'found_text': [
                {
                    'uuid': self.found_text_item.uuid_str(),
                    'author': {
                        'uuid': self.user01p.uuid_str(),
                        'first_name': "FirstName",
                        'last_name': "LastName",
                        'gender': "M",
                        'avatar': None
                    },
                    'title': "Found text",
                    'description': None,
                    'gallery_uuid': None,
                    'date_created': self.found_text_item.date_created.strftime(JSON_TS),
                    'submitted': True,
                    'hidden': False,
                    'is_liked': False,
                    'target_type': 'profile',
                    'target_uuid': self.user01p.uuid_str(),
                    'category': "",
                    'source_file': None,
                    'source_author': None,
                    'source_issue_date': None,
                    'language': "en",
                    'religion_stream': None,
                    'cover_image_url': None
                }
            ],
            'found_posts_count': 1,
            'found_posts': [
                {
                    'uuid': self.found_post.uuid_str(),
                    'date_created': self.found_post.date_created.strftime(JSON_TS),
                    'author': {
                        'uuid': self.user01p.uuid_str(),
                        'first_name': "FirstName",
                        'last_name': "LastName",
                        'gender': "M",
                        'avatar': None
                    },
                    'title': "Found post",
                    'text': "Found post text",
                    'picture_items': [],
                    'video_items': [],
                    'audio_items': [],
                    'text_items': [],
                    'comments': [],
                    'comments_count': 0,
                    'is_liked': False,
                    'likes_count': 0,
                    'recent_likes': [],
                    'reposts': [],
                    'reposts_count': 0
                }
            ]
        })
