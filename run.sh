mkdir ~/ML_TMP
pip --cache-dir=~/ML_TMP install sentence-transformers==2.2.2
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --worker-class gevent --worker-connections 1000 --timeout 120 --log-file -
