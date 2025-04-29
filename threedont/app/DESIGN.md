# Design document

At the moment the design of the application
is becoming very complex. The number of components
and actors, the interactions between them, the
complex nature of the communications needs some
explanations.

I will start saying that it's not completely
my fault, the developers of `pptk` have chosen
to use a TCP socket for communication between
the viewer and the server.

First of all, you will need to be familiar with
the concept of signals and slots in qt, and also
with the fact that the event loop is signal threaded
and blocking.

A new tcp connection sends a signal to the application,
so when sending data to the viewer this cannot be done
from the event loop, this would create a deadlock where
the sender waits for the connection to be established
but it cannot be established until the sender finishes
to send data. So, the python logic runs in another
thread, see [controller.py](controller.py).

The gui needs to send data to the python part,
so a GuiWrapper is created, it's a python class
written in c++ bridging python and qt. This class
is then wrapped in the `ActionController`, which
sends the functions calls to the python thread
with a `Queue`. This is necessary for the multithreading
python design, we need to call the methods asynchronously
from the event loop.

The `Controller` listens to the `Queue` and
dispatch his methods.

But now the `Controller` needs to modify the ui,
if it's the Viewer it just uses the preexisting
interface, that works well, for other stuff
it was impossible to extend the TCP interface
with new capabilities, so I wrote a wrapper for
the ui that can call ui's slots from another thread.
This is an example of the responsible code:

```
QMetaObject::invokeMethod(mainWindow, "addButton", Qt::QueuedConnection, Q_ARG(QString, "New Button"));
```

With this we can change the ui from another thread safely.
This wrapper is also part of the `GuiWrapper` but it sends
the calls across the threads.