from ansible.module_utils.basic import AnsibleModule
import requests

def iboot_off(ip, user, password):
    url = f'http://{ip}?u={user}&p={password}&s=1&c=1'
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an exception for HTTP errors

        if response.status_code == 200:
            return True, response.content.decode('utf-8')
        else:
            return False, response.content.decode('utf-8')

    except requests.RequestException as e:
        return False, str(e)

def main():
    module = AnsibleModule(
        argument_spec=dict(
            ip=dict(type='str', required=True),
            user=dict(type='str', required=True),
            password=dict(type='str', required=True, no_log=True),
        )
    )

    ip = module.params['ip']
    user = module.params['user']
    password = module.params['password']

    success, message = iboot_off(ip, user, password)

    if success:
        module.exit_json(changed=True, msg=message)
    else:
        module.fail_json(msg=message)

if __name__ == '__main__':
    main()