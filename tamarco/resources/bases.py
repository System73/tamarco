from typing import List

from tamarco.resources.basic.status.status_codes import StatusCodes


class BaseResource:
    """Define the basic interface of a resource.
    All the tamarco resources should inherit from this class.


    Resource start call chain:
        1. bind
        2. configure_settings
        3. pre_start
        4. start
        5. post_start

    Resource stop call chain:
        1. stop
        2. post_stop
    """

    depends_on = []
    loggers_names = []

    def __init__(self):
        self.name = None
        self.microservice = None
        self.settings = None
        self._status = StatusCodes.NOT_STARTED

    async def bind(self, microservice, name):
        """Build method, the microservice binds all its resources. Microservice starts and stops the resources.

        Args:
            microservice (Microservice): Microservice instance managing the resource.
            name (str): Name of the resource instance in the microservice class.
        """
        self.microservice = microservice
        self.name = name

    async def configure_settings(self, settings):
        """Build method, the microservice provides the settings class of each resource.
        The resource should read the settings via this object.

        Args:
            settings (SettingsView): Settings view of the resource.
        """
        self.settings = settings

    async def pre_start(self):
        """Pre start stage of the resource lifecycle."""
        pass

    async def start(self):
        """Start stage of the resource lifecycle."""
        self._status = StatusCodes.STARTED

    async def post_start(self):
        """Post start stage of the resource lifecycle."""
        pass

    async def stop(self):
        """Stop stage of the resource lifecycle."""
        self._status = StatusCodes.STOPPED

    async def post_stop(self):
        """Post stop stage of the resource lifecycle."""
        pass

    async def status(self) -> dict:
        """Return information about the state of the resource."""
        return {"status": self._status}

    def __repr__(self):
        return f"<{self.__class__} name={self.name}>"


class StreamBase:
    def __init__(self, name, codec=None, resource=None):
        """
        Args:
            name (str): Name of the stream.
            codec (CodecInterface): Used to decode the input and output from the stream.
            resource (BaseResource): Owner resource of the stream.
        """
        self.name = name
        self.codec = codec
        self.resource = resource


class InputBase(StreamBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.on_message_callback = None
        if self.resource:
            self.resource.add_input(self)

    def __call__(self, callback):
        """Allow the input to behave as a decorator."""
        self.on_message_callback = callback
        return self

    def __aiter__(self):
        """Allow the input to behave as an asyncronous iterator."""
        return self

    def __anext__(self):
        """Allow the input to behave as an asyncronous iterator."""
        raise NotImplementedError("The __anext__ method should be implemented in the child class.")

    def __repr__(self):
        return f"Tamarco Input {self.name} from resource {self.resource}"


class OutputBase(StreamBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.resource:
            self.resource.add_output(self)

    def __repr__(self):
        return f"Tamarco Output {self.name} from resource {self.resource}"


class IOResource(BaseResource):
    """Extended resource that manages I/O streams, like Kafka and AMQP."""

    def __init__(self, inputs: List = None, outputs: List = None):
        super().__init__()
        self.inputs = {}
        self.outputs = {}
        inputs = [] if inputs is None else inputs
        outputs = [] if outputs is None else outputs

        for input_element in inputs:
            self.add_input(input_element)
        for output_element in outputs:
            self.add_output(output_element)

    def add_input(self, input_to_add):
        """Add one input.

        Args:
            input_to_add (InputBase): Input to add.
        """
        assert input_to_add.name not in self.inputs, "Error two inputs with the same name"
        self.inputs[input_to_add.name] = input_to_add

    def add_output(self, output):
        """Add one output.

        Args:
            output (OutputBase): Output to add.
        """
        assert output.name not in self.outputs, "Error two outputs with the same name"
        self.outputs[output.name] = output


class DatabaseResource(BaseResource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = None

    async def start(self, clean_database=False, register_scripts=True):
        await self.connect()
        await self.init_db(clean_database=clean_database, register_scripts=register_scripts)
        await super().start()

    async def stop(self):
        self._status = StatusCodes.STOPPING
        await self.disconnect()
        await super().stop()

    async def connect(self, *args, **kwargs):
        pass

    async def disconnect(self, *args, **kwargs):
        pass

    async def init_db(self, *args, **kwargs):
        pass

    def clear(self):
        pass

    async def status(self):
        return {"status": self._status}
