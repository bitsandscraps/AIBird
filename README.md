# Python Agent for AI Bird

A Python interface to control the [AIBird software](https://aibirds.org)

## Getting Started

### Prerequisites

* jdk
* ant
* python
* [AIBird Chrome Plugin](https://aibirds.org/basic-game-playing-software/getting-started.html)

### Running
1. Start chrome
2. The server side
```bash
$ cd server
$ ant
```
3. The client side
```python
import aibird_client
abc = aibird_client.AIBirdClient()
abc.connect()
# Do whatever you want to do
img = abc.screenshot()
process_screenshot(img)         # A user defined code
```

## Issues
The AIBird software parsed the in game score by evaluating the MD5 hash of the numbers.
The following is an excerpt from [server/src/ab/vision/GameStateExtractor.java](server/src/ab/vision/GameStateExtractor.java)
```java
int value = 0;
if (letterHash.equals("12908cffd382ed43a990cc413f9c4aa6")) {
        value = 1;
} else if (letterHash.equals("1a2913c65f17ea2ad3de7b883a38f130")) {
        value = 2;
} else if (letterHash.equals("4a02d237a153b396546059d00a9c31c9")) {
        value = 3;
} else if (letterHash.equals("db413d970283c7fabe5f1c8e60b29c7d")) {
        value = 4;
} else if (letterHash.equals("d1539590da35f4350a785250424bcba7")) {
        value = 5;
} else if (letterHash.equals("c7c2bd28cc81c1604cf263a162bf6b68")) {
        value = 6;
} else if (letterHash.equals("2c2b6b0493a25fcbb7482f6affacb9da")) {
        value = 7;
} else if (letterHash.equals("357589065a43445cae8fc14c1c3eb41c")) {
        value = 8;
} else if (letterHash.equals("13849e06f884988983e71bfe3a318d4d")) {
        value = 9;
}
```
I am not sure why but the hash values in the original AIBird software did not work on my machine.
So I have changed the values. You may also need to do that.
