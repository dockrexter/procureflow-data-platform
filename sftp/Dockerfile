FROM ubuntu:24.04
RUN apt-get update && apt-get install -y --no-install-recommends openssh-server && rm -rf /var/lib/apt/lists/* && useradd -m -u 1001 source && passwd -d source && mkdir -p /run/sshd /home/source/outbound /etc/ssh/authorized_keys
COPY sshd_config /etc/ssh/sshd_config
CMD ["sh", "-c", "ssh-keygen -A && exec /usr/sbin/sshd -D -e"]
