"""
# appdynamics' zmq is not "green" when using gevent

Although there is a `green` module in appdynamics_bindeps/zmq we cannot find a clean way to use it in our application.
By default appdynamics.agent.core.transport uses `import appdynamics_bindeps.zmq as zmq` which is blocking on `PollBindConnectionStrategy` in a gevent environment.

How can we use the `green` zmq module without monkey patching transport.zqm?

requires:
* gevent
* pytest
* appdynamics
"""

from gevent import monkey

monkey.patch_all()
import gevent

from appdynamics.agent.core import transport
import sys

if len(sys.argv) == 2 and sys.argv[1] == "green":
    from appdynamics_bindeps.zmq import green as green_zmq
    transport.zmq = green_zmq

from appdynamics.agent.core.transport import zmq

print(f"using zmq lib: at {transport.zmq.__file__}")

MSG = ["ZMQ", "is", "NOT", "green!"]


def test_green():
    ctx = zmq.Context.instance()
    addr = f"ipc:///tmp/{__file__}"
    socket = ctx.socket(zmq.ROUTER)
    socket.connect(addr)
    socket.poll(100, zmq.POLLBIND)
    print(" ".join(MSG))
    socket.close()


def set_green():
    MSG.pop(2)


jobs = [gevent.spawn(test_green), gevent.spawn(set_green)]
gevent.joinall(jobs)
    
    
    
    
# python test_appdynamics_blocking.py vs python test_appdynamics_blocking.py green
# it seems that we can monkey patch it by replacing the zmq import in appdynamics.agent.core.transport
# the whole zmq stuff is a little strange as you cannot import anything from appdynamics_bindeps.zmq unless you have imported appdynamics.agent.core.transport directly or indirectly
# so my summary on testing appdynamics is that its zmq is blocking.
# they use a patched version of zmq with an extra zmq flag zmq.POLLBIND which has a commented # appd custom
# not sure what it does, but if it doesnt magically turns a blocking in a not blocking operation i am pretty sure its blocking
