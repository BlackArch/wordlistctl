FROM python:alpine

LABEL version="0.8.8" \
    author="Author BlackArch (https://github.com/BlackArch)" \
    docker_build="docker build -t blackarch/wordlistctl:0.8.8 ." \
    docker_run_basic="docker run --rm blackarch/wordlistctl:0.8.8 -h"

COPY [".", "/wordlistctl"]

ENV PATH=${PATH}:/wordlistctl

RUN pip install -r /wordlistctl/requirements.txt && \
    mkdir -p /usr/share/wordlists/{usernames,passwords,discovery,fuzzing,misc} && \
    addgroup wordlistctl && \
    adduser -G wordlistctl -g "Wordlistctl user" -s /bin/sh -D wordlistctl && \
    chown -R wordlistctl.wordlistctl /wordlistctl /usr/share/wordlists && \
    export RANDOM_PASSWORD=$(tr -dc A-Za-z0-9 </dev/urandom | head -c44) && \
    echo "root:$RANDOM_PASSWORD" | chpasswd && \
    unset RANDOM_PASSWORD && \
    passwd -l root

USER wordlistctl

ENTRYPOINT ["wordlistctl.py"]

CMD ["-h"]
