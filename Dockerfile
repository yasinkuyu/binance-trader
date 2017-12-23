FROM python:3

ADD trader.py /

RUN pip install requests

CMD [ "python", "./trader.py" ]
