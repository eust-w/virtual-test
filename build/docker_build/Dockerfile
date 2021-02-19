FROM centos:centos7.6.1810

RUN yum -y install openssh-server passwd rsync iproute python-virtualenv git libvirt libvirt-devel libvirt-python gcc gdb qemu-kvm
RUN ln -snf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && echo "Asia/Shanghai" > /etc/timezone

RUN echo 'password' | passwd --stdin root
RUN systemctl enable sshd.service
RUN systemctl enable libvirtd.service

RUN mkdir -p /root/.ssh
RUN chmod 0700 /root/.ssh
COPY ssh/id_rsa.pub /root
RUN cat /root/id_rsa.pub > /root/.ssh/authorized_keys
RUN chmod 0600 /root/.ssh/authorized_keys

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
