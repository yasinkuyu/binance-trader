FROM python:3
ADD app/config.py /
ADD app/BinanceAPI.py /
ADD trader.py /
RUN pip install requests
CMD [ "python", "./trader.py" ]
