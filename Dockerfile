from python:2
WORKDIR /ansible
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
ENV PATH $PATH:/ansible/bin
ENV ANSIBLE_HOME /ansible
ENV PYTHONPATH /ansible/lib
