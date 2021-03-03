from utils import bash


DOCKER_REPO = 'http://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo'


class InstallError(Exception):
    pass


class Installer(object):
    def check_root(self):
        r, _, _ = bash.run('whoami | grep root')
        if r != 0:
            raise InstallError('please run as root user or use sudo')

    def check_kvm(self):
        r, _, _ = bash.run('lsmod | grep kvm')
        if r != 0:
            raise InstallError('kvm module is not loaded, run "lsmod" to check')

    def check_virtualization(self):
        raise NotImplementedError('not implemented')

    def install_dependencies(self):
        raise NotImplementedError('not implemented')

    def get_cni_tar_file_path(self):
        raise NotImplementedError('not implemented')

    def get_ignite_tar_file_path(self):
        raise NotImplementedError('not implemented')

    def install_cni(self):
        bash.call_with_screen_output('mkdir -p /opt/cni/bin')
        bash.call_with_screen_output('tar xzf %s -C /opt/cni/bin' % self.get_cni_tar_file_path())

    def install_ignite(self):
        bash.call_with_screen_output('tar xzf %s -C /user/bin' % self.get_ignite_tar_file_path())

    def install(self):
        self.check_root()
        self.check_virtualization()
        self.check_kvm()
        self.install_dependencies()
        self.install_cni()
        self.install_ignite()


class X64Installer(Installer):
    def install_dependencies(self):
        bash.call_with_screen_output('yum install -y e2fsprogs openssh-clients')
        bash.call_with_screen_output('which containerd || ( yum-config-manager --add-repo %s && yum install -y containerd.io )' % DOCKER_REPO)
        bash.call_with_screen_output('yum -y install docker-ce')

    def check_virtualization(self):
        r, _, _ = bash.run('lscpu | grep Virtualization')
        if r != 0:
            raise InstallError('virtualization not opened, run "lscpu" to check')


class ArmInstaller(Installer):
    # TODO: implemented it
    pass


def install():
    arch = bash.call('[ $(uname -m) = "x86_64" ] && echo amd64 || echo arm64').strip('\n\t\r ')
    if arch == 'amd64':
        X64Installer().install()
    else:
        ArmInstaller().install()