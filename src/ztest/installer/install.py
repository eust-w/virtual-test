from utils import bash, misc
import os
import psutil
import sys


DOCKER_REPO = 'http://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo'
TOOLS_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'tools')


def start_ignited_if_not():
    is_running = False

    for p in psutil.process_iter():
        cmdline = p.cmdline()
        if 'ignited' in cmdline:
            is_running = True
            break

    if not is_running:
        bash.call_with_screen_output('nohup ignited daemon --log-level debug &')

        @misc.retry(5, 0.5)
        def wait_for_start():
            bash.call('ignite ps')

        wait_for_start()


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
        bash.call_with_screen_output('tar xzf %s -C /usr/bin' % self.get_ignite_tar_file_path())

    def configure(self):
        bash.call_with_screen_output('systemctl enable docker')
        bash.call_with_screen_output('systemctl start docker')
        bash.call_with_screen_output('systemctl enable containerd')
        bash.call_with_screen_output('systemctl start containerd')

    def check(self):
        bash.call('docker ps')
        start_ignited_if_not()

    def install(self):
        self.check_root()
        self.check_virtualization()
        self.check_kvm()
        self.install_dependencies()
        self.install_cni()
        self.install_ignite()
        self.configure()
        self.check()

        sys.stdout.write("""
        
ztest has been successfully installed!
""")


class X64Installer(Installer):
    CNI_TAR = os.path.join(TOOLS_DIR, 'cni-x64.tar.gz')
    IGNITE_TAR = os.path.join(TOOLS_DIR, 'ignite-x64.tar.gz')

    def install_dependencies(self):
        bash.call_with_screen_output('yum install -y e2fsprogs openssh-clients yum-utils git')
        bash.call_with_screen_output('which containerd || ( yum-config-manager --add-repo %s && yum install -y containerd.io )' % DOCKER_REPO)
        bash.call_with_screen_output('yum -y install docker-ce')

    def check_virtualization(self):
        r, _, _ = bash.run('lscpu | grep Virtualization')
        if r != 0:
            raise InstallError('virtualization not opened, run "lscpu" to check')

    def get_cni_tar_file_path(self):
        return self.CNI_TAR

    def get_ignite_tar_file_path(self):
        return self.IGNITE_TAR


class ArmInstaller(Installer):
    # TODO: implemented it
    pass


def install():
    arch = bash.call('[ $(uname -m) = "x86_64" ] && echo amd64 || echo arm64').strip('\n\t\r ')

    try:
        if arch == 'amd64':
            X64Installer().install()
        else:
            ArmInstaller().install()
    except InstallError as e:
        sys.stderr.write("ERROR: %s" % e.message)
