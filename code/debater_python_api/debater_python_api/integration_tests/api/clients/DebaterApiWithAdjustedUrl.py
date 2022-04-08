from enum import Enum

from debater_python_api.api.debater_api import DebaterApi


def production_host(original_host):
    return original_host


def production_backdoor_host(original_host):
    return original_host.replace('debater.res.ibm.com', 'ris2-debater-event.us-east.containers.appdomain.cloud')


def staging_host(original_host):
    return original_host.replace('https://', 'https://staging-')

def test_host(original_host):
    return original_host.replace('https://', 'https://test-')


def experiments_host(original_host):
    return original_host.replace('https://keypoint-matching-', 'https://kp-')


def production2_host(original_host):
    return original_host.replace('https://keypoint-matching-', 'https://experiments-kp-')


def local_host(_):
    return 'http://localhost:9004'


def staging_backdoor_host(original_host):
    if __name__ == '__main__':
        return original_host.replace('debater.res.ibm.com', 'ris2-debater-event.us-east.containers.appdomain.cloud').\
            replace('https://', 'https://staging-')


def default_host(original_host):
    return original_host.replace('https://', 'https://default-')


def default_backdoor_host(original_host):
    if __name__ == '__main__':
        return original_host.replace('debater.res.ibm.com', 'ris2-debater-event.us-east.containers.appdomain.cloud').\
            replace('https://', 'https://default-')


def decorator(func, host_modifier):
    def inner_function(*args, **kwargs):
        client = func(*args, **kwargs)
        client.host = host_modifier(client.host)
        return client

    return inner_function


class Domains(Enum):
    production = (1, production_host)
    production2 = (2, production2_host)
    staging = (3, staging_host)
    test = (4, test_host)
    production_backdoor = (5, production_backdoor_host)
    staging_backdoor = (6, staging_backdoor_host)
    default = (7, default_host)
    default_backdoor = (8, default_backdoor_host)
    local = (9, local_host)
    experiments = (10, experiments_host)

class DebaterApiWithAdjustedUrl(DebaterApi):

    def __init__(self, apikey, domain):
        super().__init__(apikey)

        self.url_modifier = domain.value[1]
        for attr in dir(self):
            if str(attr).startswith('get_') and str(attr).endswith('client'):
                setattr(self, attr, decorator(getattr(self, attr), self.url_modifier))


def main():
    debater_api = DebaterApiWithAdjustedUrl('PUT_YOUR_API_KEY_HERE', Domains.test)
    client = debater_api.get_evidence_detection_client()
    print('host {}'.format(client.host))
    client = debater_api.get_keypoints_client()
    print('host {}'.format(client.host))


if __name__ == '__main__':
    main()
