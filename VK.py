import os
import requests
import time


class VK_User:
    def __init__(self, token, id_name=None):
        self.token = token
        self.user_id = -1
        self.error_msg = ""
        if id_name is None:
            id_name = self._get_user_id()
        user_info = self._get_user_info(id_name)
        if len(user_info) == 1 and type(user_info) is list:
            self.user_id = user_info[0]['id']
        else:
            self.error_msg = user_info['error']['error_msg']
            print(self.error_msg)

    def _get_user_id(self):
        if os.path.exists('user_id.txt'):
            with open('user_id.txt') as f:
                return f.read()
        else:
            return input('Введите имя пользователя или его id в ВК: ')

    def _executor(f):
        def wrapper(self, *args, **kwargs):
            result = f(self, *args, **kwargs)
            if 'error' in result:
                if result['error']['error_code'] in (7, 18):  # User was deleted or banned
                    return {'items': []}
                elif result['error']['error_code'] == 6:  # Too many requests per second
                    time.sleep(0.5)
                    return wrapper(self, *args, **kwargs)
                else:
                    self.error_msg = result['error']['error_msg']
                    return result
            else:
                return result['response']

        return wrapper

    @_executor
    def get_user_groups(self, user_id=None, detailed=False):
        if user_id is None:
            user_id = self.user_id
        params = {'access_token': self.token,
                  'user_id': user_id,
                  'v': '5.80'}
        if detailed:
            params['extended'] = 1
            params['fields'] = 'members_count'
        response = requests.get('https://api.vk.com/method/groups.get',
                                params,
                                verify=False)
        return response.json()

    @_executor
    def get_friends(self):
        params = {'access_token': self.token,
                  'user_id': self.user_id,
                  'fields': 'nickname',
                  'v': '5.80'}
        response = requests.get('https://api.vk.com/method/friends.get',
                                params,
                                verify=False)
        return response.json()

    @_executor
    def _get_user_info(self, id_name):
        params = {'access_token': self.token,
                  'user_ids': id_name,
                  'fields': 'nickname',
                  'v': '5.80'}
        response = requests.get('https://api.vk.com/method/users.get',
                                params,
                                verify=False)
        return response.json()

    @_executor
    def get_friends_in_group(self, group_id):
        params = {'access_token': self.token,
                  'group_id': group_id,
                  'filter': 'friends',
                  'v': '5.80'}
        response = requests.get('https://api.vk.com/method/groups.getMembers',
                                params,
                                verify=False)
        return response.json()

    def get_exclusive_groups(self, max_friends=0):
        groups = self.get_user_groups(self.user_id, True)['items']
        friends = self.get_friends()['items']
        if max_friends == 0:
            group_ids = self._get_exclusive_groups_using_sets(groups,
                                                              friends)
        else:
            group_ids = self._get_exclusive_groups_using_dicts(groups,
                                                               friends,
                                                               max_friends)
        result = []
        for group in groups:
            if group['id'] in group_ids:
                result.append(group)
        return result

    def _progress_bar(self, iteration, total):
        length = 100
        fill = '#'
        percent = "{0:.1f}".format(100 * (iteration / float(total)))
        current_length = int(length * iteration // total)
        bar = fill * current_length + '-' * (length - current_length)
        print('\r |%s| %s%%' % (bar, percent), end='\r')
        if iteration == total:
            print()

    def _get_exclusive_groups_using_sets(self, groups, friends):
        exclusive_groups = set([i['id'] for i in groups])
        count_friends = len(friends)
        friend_number = 1
        for friend in friends:
            self._progress_bar(friend_number, count_friends)
            friend_groups = self.get_user_groups(friend['id'])['items']
            groups_for_current_friend_set = set(friend_groups)
            exclusive_groups -= groups_for_current_friend_set
            friend_number += 1
        return exclusive_groups

    def _update_group_count(self, friend_groups, friends_in_group_count):
        for group in friend_groups:
            if group in friends_in_group_count:
                friends_in_group_count[group] += 1

    def _get_exclusive_groups_using_dicts(self, groups, friends, max_friends):
        exclusive_groups = [i['id'] for i in groups]
        friends_in_group_count = dict.fromkeys(exclusive_groups, 0)
        exclusive_groups = set()
        count_friends = len(friends)
        friend_number = 1
        for friend in friends:
            self._progress_bar(friend_number, count_friends)
            friend_groups = self.get_user_groups(friend['id'])['items']
            self._update_group_count(friend_groups,
                                     friends_in_group_count)
            friend_number += 1
        for group_id, friends_count in friends_in_group_count.items():
            if friends_count <= max_friends:
                exclusive_groups.add(group_id)
        return exclusive_groups
