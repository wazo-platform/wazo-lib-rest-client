wazo-lib-rest-client
====================

[![Build Status](https://jenkins.wazo.community/buildStatus/icon?job=wazo-lib-rest-client)](https://jenkins.wazo.community/job/wazo-lib-rest-client)

The base library used by Wazo's REST clients.


Usage
-----

Create a new REST client:

```python
from wazo_lib_rest_client import new_client_factory

port = 5433
version = '1.2'
Client = new_client_factory('my_application.commands', port, version)
```

This creates a new Class object that can be used to instantiate a client using
commands from the *my_application.commands* namespace.

To add a new command, subclass the RESTCommand:

```python
from wazo_lib_rest_client import RESTCommand

class FooCommand(RESTCommand):

      resource = 'foo'  # This is the resource used to execute the query

      def get(self, **kwargs):
          result = self.session.get(self.base_url, params=kwargs)
          # Deserialization/validation here if needed
          return result.content
```

Add the new command to the namespace in setup.py:

```python
setup(
    entry_points={
        'my_application.commands': [  # namespace used in make_client
            'foo = path.to.foo.module:FooCommand',
        ]
    }
)
```

Using the client:

```python
client = Client(host='localhost')
c.foo.get()  # returns the result of GET http://localhost:5433/1.2/foo
```

Certificates:

If the user wants to verify the certificate when using HTTPS the
verify_certificate argument can be passed to the client.

Valid values include True, False or the path to a CA bundle containing the chain
of trust leading to the certificate used by the server.

```python
client_1 = Client(https=True, verify_certificate=True)
client_2 = Client(https=True, verify_certificate='<path/to/bundle/file>')
```


Running unit tests
------------------

```
apt-get install python3-dev libffi-dev libssl-dev
pip install tox
tox --recreate -e py37
```
