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
import gevent
from gevent import monkey


monkey.patch_all()


def poll_zqm(zmq_module):
    output = []

    def poll():
        with zmq_module.Context.instance() as ctx:
            addr = f"ipc:///tmp/test_{zmq_module.__name__}"
            socket = ctx.socket(zmq_module.ROUTER)
            socket.connect(addr)
            output.append(f"pre socket.poll: {ctx}")
            socket.poll(100)
            output.append("post socket.poll")
            socket.close()

    def other():
        output.append("other")

    gevent.joinall([gevent.spawn(poll), gevent.spawn(other)])

    assert len(output) == 3
    return output


def test_zmq_blocking():
    from appdynamics.agent.core import transport

    result = poll_zqm(transport.zmq)

    assert result[1] == "other", "socket.poll() is expected to yield to 'other()'"


def test_zmq_green():
    from appdynamics.agent.core import transport
    from appdynamics_bindeps.zmq import green as green_zmq

    result = poll_zqm(green_zmq)

    assert result[1] == "other", "socket.poll() is expected to yield to 'other()'"


def test_zmq_module():
    from appdynamics.agent.core.transport import zmq

    assert zmq.__name__.split(".")[-1] == "green", f"{zmq.__name__} is not 'green'"
