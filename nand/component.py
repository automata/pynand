"""DSL for defining components in the style of Nand to Tetris.

See project_01.py and test_01.py for examples of how to use it. This code uses all sorts of hacks
to try to provide a nice HDL syntax.
"""

import collections

class NodeSeq:
    def __init__(self):
        self.seq = 0

    def next(self):
        tmp, self.seq = self.seq, self.seq+1
        return tmp

NODE_SEQ = NodeSeq()

class Component:
    def __init__(self, builder):
        self.builder = builder

    def __call__(self, **args):
        return Instance(self, **args)

    def root(self):
        return RootInstance(self)

class Args:
    def __init__(self, inst):
        self.inst = inst

    def __getattr__(self, name):
        """Called when the builder asks for an input to hand to an internal component."""
        return self.inst.args[name]

class InputRef:
    def __init__(self, inst, name, bit=None):
        self.inst = inst
        self.name = name
        self.bit = bit

    def __getitem__(self, key):
        """Called when the builder asks for a bit slice of an input."""
        return InputRef(self.inst, self.name, key)

    def __repr__(self):
        if self.bit is not None:
            return f"Ref({self.inst}.{self.name}[{self.bit}])"
        else:
            return f"Ref({self.inst}.{self.name})"

    def __eq__(self, other):
        return self.inst == other.inst and self.name == other.name and self.bit == other.bit

    def __hash__(self):
        return hash((self.inst, self.name, self.bit))

class Outputs:
    def __init__(self, comp):
        self.comp = comp
        self.dict = {}  # local output name -> child InputRef

    def __setattr__(self, name, value):
        """Called when the builder wires an internal component's output as an output of this component."""
        if name in ('comp', 'dict'):   # hack for initialization-time
            return object.__setattr__(self, name, value)

        # TODO: trap conflicting wiring (including with inputs)
        self.dict[(name, None)] = value

    def __getattr__(self, name):
        """Called when the builder is going to assign to a bit slice of an output."""
        return OutputSlice(self, name)

class OutputSlice:
    def __init__(self, outputs, name):
        self.outputs = outputs
        self.name = name

    def __setitem__(self, key, value):
        """Value is an int between 0 and 15, or (eventually) a slice object with
        .start and .step on the same interval.
        """
        self.outputs.dict[(self.name, key)] = value


class Instance:
    def __init__(self, comp, **args):
        self.comp = comp
        self.args = args
        self.seq = NODE_SEQ.next()

        inputs = Args(self)
        self.outputs = Outputs(self)

        comp.builder(inputs, self.outputs)

    def __getattr__(self, name):
        return InputRef(self, name)

    def refs(self):
        return set(self.outputs.dict.values())

    def __repr__(self):
        builder_name = self.comp.builder.__name__
        if builder_name.startswith("<"):  # as in "<lambda>", for example
            name = "instance"
        elif builder_name.startswith("mk"):
            name = builder_name[2:]
        else:
            name = builder_name
        return f"{name}_{self.seq}"


class RootInstance:
    def __init__(self, comp):
        self.comp = comp

        self.inputs = Inputs(self)
        self.outputs = Outputs(self)
        comp.builder(self.inputs, self.outputs)

    # FIXME: copied from Instance
    def refs(self):
        return set(self.outputs.dict.values())

    def __repr__(self):
        return "root"

class Inputs:
    def __init__(self, inst):
        self.inst = inst

    def __getattr__(self, name):
        """Called when the builder asks for an input to hand to an internal component."""
        return InputRef(self.inst, name)

class NandComponent:
    def __call__(self, a, b):
        return NandInstance(a, b)

    def root(self):
        return NandRootInstance()

class NandInstance:
    def __init__(self, a, b):
        self.a, self.b = a, b
        self.out = InputRef(self, 'out')
        self.seq = NODE_SEQ.next()

    def refs(self):
        return set([self.a, self.b])

    def __repr__(self):
        return f"Nand_{self.seq}"

class NandRootInstance:
    """Instance used when the chip is a single Nand gate. Mostly a hack to get gate_count to work."""
    
    def __init__(self):
        self.a = InputRef(self, "a")
        self.b = InputRef(self, "b")
        self.outputs = {('out', None): None}

    def refs(self):
        return set([self.a, self.b])

    def __repr__(self):
        return f"Nand"


Nand = NandComponent()


class Const:
    def __init__(self, value):
        self.value = value
        self.inst = self

    def refs(self):
        return set()

    def __getitem__(self, key):
        if key < 0 or key > 15:
            raise Exception(f"Bit slice out of range: {key}")
        return self

    def __eq__(self, other):
        return isinstance(other, Const) and self.value == other.value

    def __hash__(self):
        return hash(self.value)

    def __repr__(self):
        return f"const({self.value})"


class ForwardInstance:
    """A component that just forwards all interactions to a component that is provided later,
    allowing circular references to be created.
    """

    def __init__(self):
        self.ref = None

    def set(self, ref):
        # print(f"set: {ref}")
        if self.ref is not None:
            raise Exception(f"Tried to re-assign lazy ref: {self} -> {self.ref} to {ref}")
        self.ref = ref

    def refs(self):
        # FIXME: other instance types and multi-bit outputs?
        if isinstance(self.ref, Instance):
            return set([InputRef(self.ref, name) for name in self.ref.outputs.dict.keys()])
        elif isinstance(self.ref, DynamicDFFInstance):
            return set([InputRef(self.ref, "out")])
        else:
            raise Exception(f"Unexpected node in lazy reference: {self} -> {self.ref}")

    def __getattr__(self, name):
        """Note: this gets called _before_ ref is assigned, so it has to yield a reference to
        _this_ instance, even though what we want ultimately is to refer to ref after it's wired.
        """
        return InputRef(self, name)

    def __repr__(self):
        return f"Forward({self.ref})"

def lazy():
    """Syntax for creating late-bound (potentially circular) references."""
    return ForwardInstance()


class CommonInstance:
    """Pseudo-instance that forms a namespace for signals which can be referenced from any component.
    """
    
    def __init__(self):
        pass

    def refs(self):
        return set()
        
    def __repr__(self):
        return "common"
    
clock = InputRef(CommonInstance(), "clock")
"""Pre-defined signal which gets special treatment: it's available in every component, and special 
functions are provided to manipulate its state.
"""


class DynamicDFFComponent:
    def __call__(self, in_):
        return DynamicDFFInstance(in_)

    def root(self):
        return DynamicDFFRootInstance()

class DynamicDFFInstance:
    def __init__(self, in_):
        self.in_ = in_
        self.out = InputRef(self, 'out')
        self.seq = NODE_SEQ.next()

    def refs(self):
        return set([self.in_, clock])

    def __repr__(self):
        return f"DynamicDFF_{self.seq}"

class DynamicDFFRootInstance:
    """Instance used when the chip is a single DynamicDFF. Mostly a hack to get gate_count to work."""
    
    def __init__(self):
        self.in_ = InputRef(self, "in_")
        self.outputs = {('out', None): None}

    def refs(self):
        return set([self.in_, clock])

    def __repr__(self):
        return f"DynamicDFF"

DynamicDFF = DynamicDFFComponent()


class MemoryComponent:
    def __call__(self, address_bits, in_, load, address):
        """A component which provides a memory as a peripheral, costing zero gates, but adding 
        a fixed overhead of about 48 traces.

        address_bits: the number of traces allocated to address bits, e.g. 14 bits for 16K cells.
        
        TODO: support using one as a ROM: make in_ and load optional, and allow the contents
        to be initialized when it's constructed.
        """

        return MemoryInstance(address_bits, in_, load, address)

    def root(self):
        """When used as the root component, the memory is treated as having 14 address bits.
        """
        
        return MemoryRootInstance()

class MemoryInstance:
    def __init__(self, address_bits, in_, load, address):
        self.address_bits = address_bits
        
        self.in_ = in_
        self.load = load
        self.address = address
        
        self.out = InputRef(self, 'out')
        self.seq = NODE_SEQ.next()

    def refs(self):
        return set(
            [self.in_[i] for i in range(16)]
            + [self.load]
            + [self.address[i] for i in range(self.address_bits)]
            + [clock])

    def __repr__(self):
        return f"Memory({self.address_bits})_{self.seq}"

class MemoryRootInstance:
    def __init__(self):
        self.address_bits = 14
        
        self.in_ = InputRef(self, "in_")
        self.load = InputRef(self, "load")
        self.address = InputRef(self, "address")
        
        self.outputs = {('out', None): None}

    def refs(self):
        return set(
            [self.in_[i] for i in range(16)]
            + [self.load]
            + [self.address[i] for i in range(14)]
            + [clock])

    def __repr__(self):
        return f"Memory"

Memory = MemoryComponent()


def gate_count(comp):
    nodes = sorted_nodes(comp.root())
    return { k: v 
        for (k, v) in [
            ('nands', sum(1 for n in nodes if isinstance(n, (NandInstance, NandRootInstance)))),
            ('flip_flops', sum(1 for n in nodes if isinstance(n, (DynamicDFFInstance, DynamicDFFRootInstance)))),
            ('memories', sum(1 for n in nodes if isinstance(n, (MemoryInstance, MemoryRootInstance)))),
        ] 
        if v > 0
    }

def delay(self):
    raise NotImplemented()

# TODO: also answer questions about fan-out
# TODO: any other interesting properties?


def extend_sign(x):
    if x & 0x8000 != 0:
        return (-1 & ~0xffff) | x
    else:
        return x

def unsigned(x):
    return x & 0xffff

def sorted_nodes(inst):
    """List of unique nodes, in topological order (so that evaluating them once
    from left to right produces the correct result in the absence of cycles.)
    """
    # Note: a set for fast tests, and a list to remember the order
    visited = []
    visited_set = set()
    
    # The stack is never as deep as the full set of nods, so just a list seems to fast enough for now.
    stack = []
    
    def loop(n):
        if n not in visited_set and n not in stack:
            stack.append(n)
            for r in n.refs():
                loop(r.inst)
            stack.remove(n)
            visited.append(n)
            visited_set.add(n)
    loop(inst)
    return visited
