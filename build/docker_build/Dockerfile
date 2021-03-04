FROM centos:centos7.6.1810

######### Basic System Install #########
COPY repo/* /etc/yum.repos.d/
RUN yum --disablerepo=* --enablerepo=zstack-base,zstack-kvm -y install openssh-server passwd rsync iproute \
    python-virtualenv git libvirt libvirt-devel libvirt-python gcc gdb qemu-kvm net-tools wget
RUN ln -snf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && echo "Asia/Shanghai" > /etc/timezone

RUN echo 'password' | passwd --stdin root
RUN systemctl enable sshd.service
RUN systemctl enable libvirtd.service

RUN mkdir -p /root/.ssh
RUN chmod 0700 /root/.ssh
COPY ssh/id_rsa.pub /root
RUN cat /root/id_rsa.pub > /root/.ssh/authorized_keys
RUN chmod 0600 /root/.ssh/authorized_keys

######### End Basic System Install #########

# preapare KVM
RUN mkdir -p /root/test_root/images
COPY zstack-image-1.4.qcow2 /root/test_root/images
COPY kvm/libvirtd.conf /etc/libvirt
COPY kvm/qemu.conf /etc/libvirt
COPY kvm/libvirtd /etc/sysconfig/

COPY pip-20.3.4.tar.gz /root
RUN easy_install /root/pip-20.3.4.tar.gz

RUN mkdir -p /root/.pip
COPY pip.conf /root/.pip/

COPY {{ztest_pkg_path}} /root/
RUN pip install /root/{{ztest_pkg}}
RUN pip install pystack-debugger

COPY {{test_source_path}}/* /root/{{test_source_name}}
RUN zguest venv

ENTRYPOINT ["/usr/sbin/init"]
