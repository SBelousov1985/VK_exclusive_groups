import json
from pprint import pprint
import sys
import urllib3
from VK import VK_User


def get_token():
    with open('token.txt') as f:
        return f.read()


def format_groups(groups_info):
    result = []
    for group in groups_info:
        members_count = 0
        if 'deactivated' not in group:
            members_count = group['members_count']
        result.append({'name': group['name'],
                       'gid': group['id'],
                       'members_count': members_count})
    return result


def save_to_file(data, file_name):
    with open(file_name, "w", encoding="utf-8") as file:
        json.dump(data, file)


def get_user_id():
    if len(sys.argv) > 1:
        return sys.argv[1]


if __name__ == '__main__':
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  # иначе антивирус Касперского мешает
    vk = VK_User(get_token(), get_user_id())
    if vk.user_id != -1:
        exclusive_groups = vk.get_exclusive_groups(3)
        exclusive_groups_data = format_groups(exclusive_groups)
        save_to_file(exclusive_groups_data, 'groups.json')
        pprint(exclusive_groups_data)
