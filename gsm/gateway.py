import sys
import time
import threading
import traceback

import Queue

DEFAULT = 'default'

class Gateway(object):
    """The GSM Gateway itself.
    
    Provides a queue which is populated with incoming messages, calls and 
    ussd responses coming from multiple devices, and another queue which is 
    populated with messages intended to be sent from a named or default device.
    """
    def __init__(self, devices_dict):
        self.incoming = Queue.Queue()
        self._ihandler = None
        self.handlers = []
        self.interval = 2
        self.devices_dict = devices_dict
        self.devices = devices_dict.values()
        self.default_device = devices_dict.get(DEFAULT) or self.devices[0]

    def add_handler(self, handler):
        self.handlers.append(handler)

    def send(self, number, text, modem=DEFAULT):
        self.get_modem(modem).send(number, text)

    def clear_read_messages(self):
        for modem in self.devices:
            modem.clear_read_messages(debug=True)
        
    def start(self):
        """Start the gateway."""
        self._ihandler = GatewayIncomingHandler(queue=self.incoming,
                                                gateway=self)
        
        for modem in self.devices:
            modem.start(incoming_queue=self.incoming)
        self._ihandler.start()

    def stop(self):
        """Remove all pending tasks and stop the Gateway."""
        for modem in self.devices:
            modem.stop()

    def get_modem(self, key):
        if key is DEFAULT:
            return self.default_device
        return self.devices_dict.get(key)
    

class GatewayIncomingHandler(threading.Thread):
    """GatewayIncomingHandler thread."""
    def __init__(self, queue, gateway, interval=2):
        self.gateway = gateway
        self.queue = queue
        self.active = True
        self.interval = interval
        threading.Thread.__init__(self)

    def run(self):
        """Keep handling messages while active attribute is set."""
        while self.active:
            print '>>> Handling gateway incoming queue ...'
            try:
                kind, data = self.queue.get()
                for handler in self.gateway.handlers:
                    handler.handle(kind, data)
            except KeyboardInterrupt:
                self.stop() 
            finally:
                time.sleep(self.interval)

    def stop(self):
        self.active = False
        self.queue.put('') 