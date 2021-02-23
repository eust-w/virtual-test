FROM centos:centos7.6.1810

######### Basic System Install #########
COPY epel-release-latest-7.noarch.rpm /root
RUN yum -y install /root/epel-release-latest-7.noarch.rpm
RUN yum -y install openssh-server qemu-kvm systemd python-setuptools openssh-clients
RUN ln -snf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && echo "Asia/Shanghai" > /etc/timezone

RUN echo 'password' | passwd --stdin root
RUN systemctl enable sshd.service

RUN mkdir -p /root/.ssh
RUN chmod 0700 /root/.ssh
RUN ssh-keygen -N "" -f /root/.ssh/id_rsa
RUN cat /root/.ssh/id_rsa.pub > /root/.ssh/authorized_keys
RUN chmod 0600 /root/.ssh/authorized_keys

COPY pip-20.3.4.tar.gz /root
RUN easy_install /root/pip-20.3.4.tar.gz

RUN mkdir -p /root/.pip
COPY pip.conf /root/.pip/


######### Install Ceph ###########
COPY ceph.repo /etc/yum.repos.d
RUN yum -y install ceph-common-14.2.16 ceph-mon-14.2.16
RUN pip install ceph-deploy


ENTRYPOINT ["/usr/sbin/init"]
