from utils import bash, json


def list_images():
    # type: () -> list[json.DynamicDict]

    o = bash.call('docker image ls --format "{{json .}}"')
    images = []
    for i in o.split('\n'):
        i = i.strip()
        if i:
            images.append(json.DynamicDict.from_json(i))

    return images


def list_containers(included_stopped=False):
    # type: (bool) -> list[json.DynamicDict]

    if included_stopped:
        o = bash.call('docker ps -a --format "{{json .}}"')
    else:
        o = bash.call('docker ps --format "{{json .}}"')

    containers = []
    for i in o.split('\n'):
        i = i.strip()
        if i:
            containers.append(json.DynamicDict.from_json(i))

    return containers


def kill_containers(container_ids):
    # type: (list[str]) -> None

    if not container_ids:
        return

    bash.call_with_screen_output('docker kill %s' % ' '.join(container_ids))


def rm_containers(container_ids):
    # type: (list[str]) -> None

    if not container_ids:
        return

    bash.call_with_screen_output('docker rm %s' % ' '.join(container_ids))