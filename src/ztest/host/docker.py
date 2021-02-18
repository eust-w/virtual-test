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


def find_image(tag):
    # type: (str) -> json.DynamicDict

    images = list_images()
    for i in images:
        if '%s:%s' % (i.Repository, i.Tag) == tag:
            return i

    return None


def rm_old_docker_image(tag):
    # type: (str) -> None

    target_image = find_image(tag)
    if not target_image:
        return

    containers = list_containers(included_stopped=True)
    container_ids_to_kill = []
    for c in containers:
        if c.Image == tag:
            container_ids_to_kill.append(c.ID)

    if container_ids_to_kill:
        kill_containers(container_ids_to_kill)

    if container_ids_to_kill:
        rm_containers(container_ids_to_kill)

    if target_image:
        bash.call_with_screen_output('docker image rm %s' % target_image.ID)


def cp_in(container_id, src, dst):
    # type: (str, str, str) -> None

    bash.call_with_screen_output('docker cp %s %s:%s' % (src, container_id, dst))


def bash_run(container_id, cmd):
    # type: (str, str) -> (r, str, str)

    return bash.run('docker exec %s %s' % (container_id, cmd))


def bash_call(container_id, cmd):
    # type: (str, str) -> str

    return bash.call('docker exec %s %s' % (container_id, cmd))


def bash_call_with_screen_output(container_id, cmd):
    # type: (str, str) -> None

    return bash.call_with_screen_output('docker exec %s %s' % (container_id, cmd))


def commit(container_id, new_tag):
    # type: (str, str) -> None

    bash.call_with_screen_output('docker commit %s %s' % (container_id, new_tag))


def run(options):
    # type: (str) -> str

    return bash.call('docker run %s' % options).strip('\n\t\r ')

