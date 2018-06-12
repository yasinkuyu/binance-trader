FROM python:3
ADD app/ /app
ADD db/ /db
ADD trader.py /app
ADD balance.py /app
RUN pip install requests
CMD [ "python", "/app/trader.py" ]
