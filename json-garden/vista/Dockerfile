FROM worldvista/vehu:201911-syn-fhir

# copy code for json endpoint
COPY src/JSON.m /home/vehu/r/

# compile added mumps file
RUN  /opt/yottadb/r1.28_x86_64/mumps /home/vehu/r/JSON.m

# must -run ^JSON at staratup to load endpoint
# insert into line 23, before reading from pipe
RUN sed -i '23 i source /home/vehu/etc/env && /opt/yottadb/r1.28_x86_64/mumps -run ^JSON' /home/vehu/bin/start.sh

WORKDIR /opt/vista

