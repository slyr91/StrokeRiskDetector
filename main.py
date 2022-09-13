import sdetectorapp

from os import environ

if __name__ == "__main__":
    port = environ.get('PORT', 8080)
    host = '127.0.0.1' if port == 8080 else '0.0.0.0'
    sdetectorapp.create_app().run(host=host, port=port, debug=False)
