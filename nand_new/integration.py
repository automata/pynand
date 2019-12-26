import collections
from pprint import pprint  # HACK

from nand.evaluator import NandVector
from nand_new.component import Component

class IC:
    """An integrated circuit assembles one or more components by recording how their
    inputs and outputs are connected.

    An IC also acts as a component when it is assembled with other components into a
    larger chip.
    """

    def __init__(self, label, inputs, outputs):
        self.label = label
        self._inputs = inputs
        self._outputs = outputs
        self.root = Root(self)
        self.components = {}
        self.wires = {}

    def inputs(self):
        return self._inputs

    def outputs(self):
        return self._outputs

    def wire(self, from_output, to_input):
        """Connect a single trace from an output of one component to an input of another.

        Note that the IC's inputs act as outputs to feed the inputs of components, and vice versa.
        Yes, that does seem confusing.

        Each input can be connected to exactly one output; an output may feed any number of
        inputs, or none at all. A new wiring overwrites any previous wiring to the same input.

        Both components become part of this circuit.

        The connection is checked on both ends to ensure that it specifies a valid name and bit.
        Note: if a WiringError is thrown, both components are nevertheless tracked as being part
        of the IC. TODO: maybe clean that up after the fact?
        """

        self._add_component(from_output.comp)
        self._add_component(to_input.comp)

        if from_output.name not in from_output.comp.outputs():
            raise WiringError(f"Component {self._comp_label(from_output.comp)} has no output '{from_output.name}'")
        elif from_output.bit < 0 or from_output.bit >= from_output.comp.outputs()[from_output.name]:
            raise WiringError(f"Tried to connect bit {from_output.bit} of {from_output.comp.outputs()[from_output.name]}-bit output {self._comp_label(from_output.comp)}.{from_output.name}")
        elif to_input.name not in to_input.comp.inputs():
            raise WiringError(f"Component {self._comp_label(to_input.comp)} has no input '{to_input.name}'")
        elif to_input.bit < 0 or to_input.bit >= to_input.comp.inputs()[to_input.name]:
            raise WiringError(f"Tried to connect bit {to_input.bit} of {to_input.comp.inputs()[to_input.name]}-bit input {self._comp_label(to_input.comp)}.{to_input.name}")

        self.wires[to_input] = from_output

    def _add_component(self, comp):
        if comp != self.root and comp not in self.components:
            self.components[comp] = len(self.components)

    def _comp_label(self, comp):
        if comp == self.root:
            return "Root"
        else:
            num = self.components.get(comp, "unknown")
            if isinstance(comp, IC):
                return f"{comp.label}_{num}"
            else:
                return f"{comp.__class__.__name__}_{num}"

    def _connection_label(self, conn):
        comp = "" if conn.comp == self.root else f"{self._comp_label(conn.comp)}."
        bit = "" if conn.bit == 0 else f"[{conn.bit}]"  # TODO: include [0] if other bits exist for same name
        return f"{comp}{conn.name}{bit}"

    def flatten(self):
        """Construct a new IC which has the same structure as this one, but no nested ICs.
        That is, the wiring of all child ICs has been "inlined" into a single flat assembly.
        """

        ic = IC(f"{self.label}[flat]", self._inputs, self._outputs)

        flat_children = {}

        # Add all the internal wiring of child ICs:
        for comp in self.components:
            if isinstance(comp, IC):
                child = comp.flatten()
                flat_children[comp] = child
                for to_input, from_output in child.wires.items():
                    if to_input.comp != child.root and from_output.comp != child.root:
                        ic.wire(from_output, to_input)

        for to_input, from_output in self.wires.items():
            if from_output.comp == self.root:
                from_output = from_output._replace(comp=ic.root)
            if to_input.comp == self.root:
                to_input = to_input._replace(comp=ic.root)

            # If "from" is a child's output, just rewrite it to the actual component:
            if from_output.comp in flat_children:
                flat = flat_children[from_output.comp]
                from_output = flat.wires[from_output._replace(comp=flat.root)]

            # If "to" is a child's input, it may need to be connected to more than one actual component:
            if to_input.comp in flat_children:
                flat = flat_children[to_input.comp]
                conn = to_input._replace(comp=flat.root)
                for child_in, child_out in flat.wires.items():
                    if child_out == conn:
                        ic.wire(from_output, child_in)
            else:
                ic.wire(from_output, to_input)

        return ic

    def synthesize(self):
        """Compile the chip down to traces and ops for evaluation.

        Returns a NandVector.
        """
        return self.flatten()._synthesize()

    def _synthesize(self):
        # check for missing wires?
        # check for unused components?

        # Assign a bit for each output connection:
        next_bit = 0
        all_bits = {}
        for conn in set(self.wires.values()): # TODO: sort by the order the components were added?
            all_bits[conn] = next_bit
            next_bit += 1

        # Construct map of IC inputs, directly from all_bits:
        inputs = {
            (name, bit): 1 << all_bits[Connection(self.root, name, bit)]
            for name, bits in self._inputs.items()
            for bit in range(bits)  # TODO: None if single bit?
        }

        # Construct map of IC ouputs, mapped to all_bits via wires:
        outputs = {
            (name, bit): 1 << all_bits[self.wires[Connection(self.root, name, bit)]]
            for name, bits in self._outputs.items()
            for bit in range(bits)  # TODO: None if single bit?
        }

        internal = {}  # TODO

        # Construct a map of the traces for each single component, and ask it for its ops:
        # TODO: sort components topologically based on wires, starting with Root?
        ops = []
        for comp in self.components:
            traces = {}
            for name, bits in comp.inputs().items():
                traces[name] = [1 << all_bits[self.wires[Connection(comp, name, bit)]] for bit in range(bits)]
            for name, bits in comp.outputs().items():
                traces[name] = [1 << all_bits[Connection(comp, name, bit)] for bit in range(bits)]
            cops = comp.combine(**traces)
            sops = comp.sequence(**traces)
            # TEMP: need to refactor NandVector a little
            class Op:
                def __init__(self):
                    self.cops = cops
                    self.sops = sops

                def propagate(self, traces):
                    for f in self.cops:
                        traces = f(traces)
                    return traces
                def flop(self, traces):
                    for f in self.sops:
                        traces = f(traces)
                    return traces
            ops.append(Op())

        return NandVector(inputs, outputs, internal, ops)


    def __str__(self):
        # HACK
        return '\n'.join(
            [self.label] +
            [ f"  {self._connection_label(from_output)} -> {self._connection_label(to_input)}"
              for to_input, from_output in self.wires.items()
            ])

    def __repr__(self):
        # HACK
        return self.label


class Root:
    """Pseudo-component providing access to an IC's inputs and outputs (under the opposite names).
    """

    def __init__(self, ic):
        self.ic = ic

    def inputs(self):
        return self.ic.outputs()

    def outputs(self):
        return self.ic.inputs()


Connection = collections.namedtuple('Connection', ('comp', 'name', 'bit'))


class WiringError(Exception):
    pass
