xivo-lib-rest-client
====================

[![Build Status](https://travis-ci.org/xivo-pbx/xivo-lib-rest-client.svg?branch=master)](https://travis-ci.org/xivo-pbx/xivo-lib-rest-client)

The base library used by XiVO's REST clients.


## Usage

Create a new REST client:

```python
from xivo_lib_rest_client import make_client

Client = make_client('my_application.commands')
```

This creates a new Class object that can be used to instantiate a client using
commands from the *my_application.commands* namespace.

To add a new command, subclass the BaseHTTPCommand:

```python
from xivo_lib_rest_client import BaseHTTPCommand

class FooCommand(BaseHTTPCommand):

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
client = Client(host='localhost', port=9487, version='42')
c.foo.get()  # returns the result of GET http://localhost:9487/42/foo
```

## Testing

Running the tests require an installed copy of the library.

```
% pip install -r requirements.txt
% pip install -r test-requirements.txt
% python setup.py install
% nosetests
```
