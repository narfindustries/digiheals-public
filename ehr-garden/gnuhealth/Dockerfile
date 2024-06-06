FROM alpine:3.18
ENV TRYTON_DATABASE=health
ENV POSTGRES_HOSTNAME=db-gnuhealth
ENV GNUHEALTH_VERSION=4.4.0
ENV PIP_BREAK_SYSTEM_PACKAGES=1
RUN apk add --no-cache ca-certificates wget bash freetype tesseract-ocr python3 py3-numpy py3-pip py3-defusedxml jpeg-dev libarchive-tools git nodejs npm mercurial && \
    pip3 install --upgrade pip setuptools wheel && \
    apk add --no-cache --virtual .build-deps pkgconfig libxml2-dev libxslt-dev python3-dev postgresql-dev gcc g++ zlib-dev make python3-dev py3-numpy-dev libpng-dev jpeg-dev freetype-dev musl-dev linux-headers libffi-dev patch
RUN adduser -D gnuhealth
SHELL ["/bin/bash", "-c"]
WORKDIR /home/gnuhealth
RUN npm install -g grunt-cli bower
RUN wget https://downloads.tryton.org/6.0/tryton-sao-6.0.36.tgz
RUN mkdir sao && tar xzf tryton-sao-6.0.36.tgz -C sao --strip-components 1
RUN cd sao && npm install --legacy-peer-deps && grunt dev
USER gnuhealth
RUN wget https://ftp.gnu.org/gnu/health/gnuhealth-${GNUHEALTH_VERSION}.tar.gz 
RUN mkdir gnuhealth-latest && tar xzf gnuhealth-${GNUHEALTH_VERSION}.tar.gz -C gnuhealth-latest --strip-components 1
WORKDIR gnuhealth-latest/
COPY trytond.conf config/trytond.conf
RUN sed -i "s/ln \-si/ln -s/g" gnuhealth-setup
RUN bash ./gnuhealth-setup install
USER root
RUN apk del .build-deps
USER gnuhealth
WORKDIR /home/gnuhealth
RUN echo "ehrgarden" > /tmp/pass
ENTRYPOINT bash -ic 'sleep 5; export TRYTONPASSFILE=/tmp/pass; source .gnuhealthrc; cdexe && python3 ./trytond-admin --all --database=${TRYTON_DATABASE} --email=admin@example.com' && ./start_gnuhealth.sh
