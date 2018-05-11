# Python Agent for AI Bird

A Python interface to control the [AIBird software](https://aibirds.org)

## Getting Started

### Prerequisites

* jdk
* ant
* python

### Running
The server side
```bash
$ cd server
$ ant
```
The client side
```python
import aibird_client
abc = aibird_client.AIBirdClient()
abc.connect()
# Do whatever you want to do
img = abc.screenshot()
process_screenshot(img)         # A user defined code
```
