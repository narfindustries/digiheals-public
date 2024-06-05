FROM worldvista/vehu:201911-syn-fhir

WORKDIR /home/vehu

# copy code for json endpoint
COPY src/JSON.m ./r/

# copy special version of SYNINIT.m with json endpoint added
COPY SYNINIT.m ./r/

# compile added mumps files
RUN  /opt/yottadb/r1.28_x86_64/mumps /home/vehu/r/JSON.m
RUN  /opt/yottadb/r1.28_x86_64/mumps /home/vehu/r/SYNINIT.m

# must -run ^JSON at staratup to load endpoint
# RUN echo 'echo running JSON inside mumps'  >> /home/vehu/bin/start.sh
# insert into line 23, before reading from pipe
RUN sed -i '23 i source /home/vehu/etc/env && /opt/yottadb/r1.28_x86_64/mumps -run ^JSON' /home/vehu/bin/start.sh
WORKDIR /opt/vista




