FROM python:3
ADD config.py /
ADD BinanceAPI.py /
ADD trader.py /
RUN pip install requests
CMD [ "python", "./trader.py" ]
