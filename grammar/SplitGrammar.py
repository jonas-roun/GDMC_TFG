from .GrammarBox import BoundingBox
from .GrammarStorage import RULES, CONTEXT, MATERIALS
import random


class Constraint:
    def __init__(self, a, b, op):
        self.a = a
        self.b = b
        self.op = op

    def evaluate(self, ctx):
        if self.op == "else": return False
        if self.op == "true": return True
        if self.op == "and":
            return self.a.evaluate(ctx) and self.b.evaluate(ctx)
        if self.op == "or":
            return self.a.evaluate(ctx) or self.b.evaluate(ctx)
        aval = ctx.get_value(self.a)
        bval = ctx.get_value(self.b)
        if self.op == "lt":
            return aval < bval
        if self.op == "gt":
            return aval > bval
        if self.op == "le":
            return aval <= bval
        if self.op == "ge":
            return aval >= bval
        if self.op == "eq":
            return aval == bval
        if self.op == "neq":
            return aval != bval
        return False

    def __repr__(self):
        return str(self.a) + " " + self.op + " " + str(self.b)

    def __bool__(self):
        return self.evaluate(CONTEXT[-1])

    def __and__(self, other):
        return Constraint(self, other, "and")

    def __or__(self, other):
        return Constraint(self, other, "or")


try:
    _ = Constraint.ELSE
except AttributeError:
    Constraint.ELSE = Constraint(None, None, "else")
    Constraint.TRUE = Constraint(None, None, "true")


class Comparer:
    def __init__(self, value, repr):
        self.value = value
        self.repr = repr

    def is_composite(self):
        return False

    def __eq__(self, other):
        return Constraint(self, other, "eq")

    def __lt__(self, other):
        return Constraint(self, other, "lt")

    def __gt__(self, other):
        return Constraint(self, other, "gt")

    def __le__(self, other):
        return Constraint(self, other, "le")

    def __ge__(self, other):
        return Constraint(self, other, "ge")

    def __neq__(self, other):
        return Constraint(self, other, "neq")

    def __mod__(self, other):
        return CompositeComparer(self, other, "%")

    def __add__(self, other):
        return CompositeComparer(self, other, "+")

    def __sub__(self, other):
        return CompositeComparer(self, other, "-")

    def __mul__(self, other):
        return CompositeComparer(self, other, "*")

    def __floordiv__(self, other):
        return CompositeComparer(self, other, "//")

    def __rmod__(self, other):
        return CompositeComparer(other, self, "%")

    def __radd__(self, other):
        return CompositeComparer(other, self, "+")

    def __rsub__(self, other):
        return CompositeComparer(other, self, "-")

    def __rmul__(self, other):
        return CompositeComparer(other, self, "*")

    def __rfloordiv__(self, other):
        return CompositeComparer(other, self, "//")

    def eq(self, other):
        if other is None: return False
        return self.value == other.value

    def __str__(self):
        return str(self.repr)

    def __repr__(self):
        return str(self.repr)


class CompositeComparer(Comparer):
    def __init__(self, a, b, op):
        self.a = a
        self.b = b
        self.op = op

    def is_composite(self):
        return True

    def __str__(self):
        return str(self.a) + self.op + str(self.b)

    def __repr__(self):
        return str(self.a) + self.op + str(self.b)

    def apply(self, aval, bval):
        if self.op == "%":
            return aval % bval
        if self.op == "+":
            return aval + bval
        if self.op == "-":
            return aval - bval

        if self.op == "*":
            return aval * bval

        if self.op == "//":
            return aval // bval

        if self.op == "max":
            return max(aval, bval)
        return aval


class Direction:
    X = Comparer(0, "X")
    Y = Comparer(1, "Y")
    Z = Comparer(2, "Z")


class Dimension(Direction):
    SMALLEST = Comparer(3, "SMALLEST")
    LARGEST = Comparer(4, "LARGEST")
    WORLD_X = Comparer(5, "WORLD_X")
    WORLD_Y = Comparer(6, "WORLD_Y")
    WORLD_Z = Comparer(7, "WORLD_Z")
    SPLIT = Comparer(8, "SPLIT")


class Rounding:
    TRUNCATE = 0
    START = 1
    END = 2
    MIDDLE = 3


class Scope(object):
    NUMBER = 0

    def __init__(self, box, parent=None, x=0, y=1, z=2, source="", rotation=0,
                 x_inverted=False, z_inverted=False):
        self.box = box
        self.children = []
        self.parent = parent
        self.x = x  # índice físico del eje X lógico (0, 1, o 2)
        self.y = y  # índice físico del eje Y lógico (siempre 1)
        self.z = z  # índice físico del eje Z lógico (0, 1, o 2)
        self.x_inverted = x_inverted  # True si X crece en dirección negativa
        self.z_inverted = z_inverted  # True si Z crece en dirección negativa
        self.source = source
        self.number = Scope.NUMBER
        self.rotation = rotation
        Scope.NUMBER += 1
        self.entered = None
        self.iterating = False
        self.status = "Whole"

    def to_json(self, small=False):
        if small:
            result = {
                "scope": str(list(self.box.origin)) + " to " + str(list(self.box.maximum)) + " (size " + str(
                    list(self.box.size)) + ")",
                "status": self.status,
                "rotation": self.rotation,
                "x_inverted": self.x_inverted,
                "z_inverted": self.z_inverted
            }
            if self.children:
                result["children"] = list([c.to_json(True) for c in self.children])
            return result
        result = {}
        result["origin"] = list(self.box.origin)
        result["size"] = list(self.box.size)
        result["max"] = list(self.box.maximum)
        result["status"] = self.status
        result["x"] = self.x
        result["y"] = self.y
        result["z"] = self.z
        result["x_inverted"] = self.x_inverted
        result["z_inverted"] = self.z_inverted
        result["source"] = self.source
        result["number"] = self.number
        result["rotation"] = self.rotation
        if self.children:
            result["children"] = list([c.to_json() for c in self.children])
        return result

    def leave(self):
        CONTEXT.pop()

    def enter(self):
        CONTEXT.extend(reversed(self.children))
        return self

    def __enter__(self):
        self.entered = CONTEXT[-1]
        return self.enter()

    def __exit__(self, exc_type, exc_value, traceback):
        if CONTEXT[-1] != self.entered:
            print("Leaving different context!")
            print("   Me:", self)
            print("   Should be:", self.entered)
            print("   Actual:", CONTEXT[-1])
        self.leave()

    def __str__(self):
        return "Scope %d: %s (rotation: %d°, x_inv=%s, z_inv=%s)" % (
            self.number, self.source, self.rotation, self.x_inverted, self.z_inverted)

    def add_children(self, children):
        self.children.extend(children)

    def fill(self, material):
        if not material:
            self.status = "empty"
        else:
            self.status = "filled " + str(material)
        self.set_material(material)

    def set_material(self, material):
        for (x, y, z) in self.box.positions:
            print("filling", (x, y, z), "with material", material)

    def split(self, direction, sizes, rounding_mode=Rounding.TRUNCATE, x=None, y=None, z=None, repeat=False):
        self.status = "split " + str(direction) + " in " + str(sizes)

        # Determinar qué eje físico y si está invertido
        if Direction.X.eq(direction):
            idx = self.x
            inverted = self.x_inverted
        elif Direction.Y.eq(direction):
            idx = self.y
            inverted = False  # Y nunca se invierte
        elif Direction.Z.eq(direction):
            idx = self.z
            inverted = self.z_inverted
        else:
            idx = self.x
            inverted = self.x_inverted

        if Dimension.SPLIT.eq(x):
            x = direction
        if Dimension.SPLIT.eq(y):
            y = direction
        if Dimension.SPLIT.eq(z):
            z = direction
        assignment = self.calculate_reorientation(x, y, z)

        self.source = "Split"
        a = self.box.origin[idx]
        b = self.box.origin[idx] + self.box.size[idx]

        # Si el tamaño es 0, no hacer split
        if a == b:
            return []

        # Generar splits
        splits = make_split(a, b, sizes, rounding_mode, repeat)

        # Si el eje está invertido, invertir los splits
        if inverted:
            # Invertir el orden y reflejar las posiciones
            new_splits = []
            for (fr, to) in reversed(splits):
                # Reflejar: si iba de a+x a a+y, ahora va de b-y a b-x
                new_fr = b - (to - a)
                new_to = b - (fr - a)
                new_splits.append((new_fr, new_to))
            splits = new_splits

        ox = self.box.origin[self.x]
        oy = self.box.origin[self.y]
        oz = self.box.origin[self.z]
        xsize = self.box.size[self.x]
        ysize = self.box.size[self.y]
        zsize = self.box.size[self.z]
        children = []

        for i, split_range in enumerate(splits):
            (fr, to) = split_range
            size = to - fr

            origin = [0, 0, 0]
            sizet = [0, 0, 0]
            origin[self.x] = ox
            origin[self.y] = oy
            origin[self.z] = oz
            origin[idx] = fr

            sizet[self.x] = xsize
            sizet[self.y] = ysize
            sizet[self.z] = zsize
            sizet[idx] = size

            children.append(self.make_child(BoundingBox(tuple(origin), tuple(sizet)), x=assignment[0], y=assignment[1],
                                            z=assignment[2], rotation=self.rotation, x_inverted=self.x_inverted, z_inverted=self.z_inverted,
                                            source="Piece %d/%d of context %d" % (i + 1, len(splits), self.number)))

        # Si el eje está invertido, invertir el orden de los hijos
        # para que las operaciones se apliquen de forma espejada
        if inverted:
            children = list(reversed(children))

        self.add_children(children)

        return children

    def calculate_reorientation(self, x=None, y=None, z=None):
        nones = 0
        if x is None:
            nones += 1
        if y is None:
            nones += 1
        if z is None:
            nones += 1
        if nones == 3: return (self.x, self.y, self.z)

        current = [self.x, self.y, self.z]
        desired = [x, y, z]
        remaining = [0, 1, 2]
        assigned = [None, None, None]
        origin = [None, None, None]
        for i, d in enumerate(desired):
            if Dimension.X.eq(d):
                assigned[i] = self.x
                if self.x in remaining:
                    remaining.remove(self.x)
                origin[i] = 0
            elif Dimension.WORLD_X.eq(d):
                assigned[i] = 0
                if 0 in remaining:
                    remaining.remove(0)
                origin[i] = current.index(0)
            elif Dimension.Y.eq(d):
                assigned[i] = self.y
                if self.y in remaining:
                    remaining.remove(self.y)
                origin[i] = 1
            elif Dimension.WORLD_Y.eq(d):
                assigned[i] = 1
                if 1 in remaining:
                    remaining.remove(1)
                origin[i] = current.index(1)
            elif Dimension.Z.eq(d):
                assigned[i] = self.z
                if self.z in remaining:
                    remaining.remove(self.z)
                origin[i] = self.z
            elif Dimension.WORLD_Z.eq(d):
                assigned[i] = 2
                if 2 in remaining:
                    remaining.remove(2)
                origin[i] = current.index(2)

        if not remaining: return assigned

        largest_idx = None
        smallest_idx = None
        for r in remaining:
            size = self.box.size[r]
            if largest_idx is None or size > self.box.size[largest_idx]:
                largest_idx = r
            if smallest_idx is None or size < self.box.size[smallest_idx]:
                smallest_idx = r

        for i, d in enumerate(desired):
            if Dimension.SMALLEST.eq(d):
                assigned[i] = smallest_idx
                if smallest_idx in remaining:
                    remaining.remove(smallest_idx)
                origin[i] = current.index(smallest_idx)
            elif Dimension.LARGEST.eq(d):
                assigned[i] = largest_idx
                if largest_idx in remaining:
                    remaining.remove(largest_idx)
                origin[i] = current.index(largest_idx)

        for i, d in enumerate(desired):
            if d is None:
                if i in origin and origin.index(i) in remaining:
                    assigned[i] = origin.index(i)
                    remaining.remove(origin.index(i))
                    origin[i] = origin.index(i)
                elif i in remaining:
                    assigned[i] = i
                    remaining.remove(i)
                    origin[i] = i
                elif len(remaining) == 1:
                    assigned[i] = remaining[0]
                    origin[i] = remaining[0]
                    remaining = []

        return assigned

    def reorient(self, x=None, y=None, z=None):
        self.status = "Reoriented to " + str(x) + ", " + str(y) + ", " + str(z)
        assigned = self.calculate_reorientation(x, y, z)
        ctx = self.make_child(self.box, x=assigned[0], y=assigned[1], z=assigned[2],rotation=self.rotation, x_inverted=self.x_inverted, z_inverted=self.z_inverted,
                              source="Reorientation of context " + str(self.number))
        self.add_children([ctx])
        return [ctx]

    def rotate(self, degrees):
        """
        Rota el scope alrededor del eje Y (vertical).
        Rotación horaria vista desde arriba (mirando hacia -Y).

        Pensando en un sistema donde:
        - X positivo = Este
        - Z positivo = Sur
        - Rotación horaria vista desde arriba

        0°:   X→Este,  Z→Sur   (sin cambios)
        90°:  X→Sur,   Z→Oeste (X va hacia donde iba Z, Z va hacia donde iba -X)
        180°: X→Oeste, Z→Norte (ambos invertidos)
        270°: X→Norte, Z→Este  (X va hacia donde iba -Z, Z va hacia donde iba X)
        """
        degrees = degrees % 360
        if degrees not in [0, 90, 180, 270]:
            raise ValueError(f"Rotation must be 0, 90, 180, or 270 degrees, got {degrees}")

        self.status = f"Rotated {degrees}°"
        new_rotation = (self.rotation +  degrees) % 360

        # Calcular nuevo mapeo de ejes
        if degrees == 0:
            new_x = self.x
            new_z = self.z
            new_x_inverted = self.x_inverted
            new_z_inverted = self.z_inverted
        elif degrees == 90:
            # Rotación 90° horaria: X→Z, Z→-X
            # El nuevo X es el antiguo Z
            # El nuevo Z es el antiguo X pero invertido
            new_x = self.z
            new_z = self.x
            new_x_inverted = self.z_inverted
            new_z_inverted = not self.x_inverted  # Se invierte porque -X
        elif degrees == 180:
            # Rotación 180°: X→-X, Z→-Z
            # Los ejes se mantienen pero ambos invertidos
            new_x = self.x
            new_z = self.z
            new_x_inverted = not self.x_inverted
            new_z_inverted = not self.z_inverted
        elif degrees == 270:
            # Rotación 270° horaria (= 90° antihoraria): X→-Z, Z→X
            # El nuevo X es el antiguo Z pero invertido
            # El nuevo Z es el antiguo X
            new_x = self.z
            new_z = self.x
            new_x_inverted = not self.z_inverted  # Se invierte porque -Z
            new_z_inverted = self.x_inverted

        ctx = self.make_child(
            self.box,
            x=new_x,
            y=self.y,
            z=new_z,
            rotation=new_rotation,
            x_inverted=new_x_inverted,
            z_inverted=new_z_inverted,
            source=f"Rotation {degrees}° of context {self.number}"
        )
        self.add_children([ctx])
        return [ctx]

    def make_child(self, box, **kwargs):
        if 'rotation' not in kwargs:
            kwargs['rotation'] = self.rotation
        if 'x_inverted' not in kwargs:
            kwargs['x_inverted'] = self.x_inverted
        if 'z_inverted' not in kwargs:
            kwargs['z_inverted'] = self.z_inverted
        child = Scope(box, parent=self, **kwargs)
        return child

    def __bool__(self):
        if self.entered is None:
            self.entered = CONTEXT[-1]
            self.enter()
        result = (CONTEXT[-1] != self.entered)
        if not result:
            self.leave()
        return result

    def get_value(self, which):
        if isinstance(which, int): return which
        if which.is_composite():
            a = self.get_value(which.a)
            b = self.get_value(which.b)
            return which.apply(a, b)
        if Dimension.X.eq(which): return self.box.size[self.x]
        if Dimension.Y.eq(which): return self.box.size[self.y]
        if Dimension.Z.eq(which): return self.box.size[self.z]
        if Dimension.WORLD_X.eq(which): return self.box.size[0]
        if Dimension.WORLD_Y.eq(which): return self.box.size[1]
        if Dimension.WORLD_Z.eq(which): return self.box.size[2]
        if Dimension.SMALLEST.eq(which): return min(self.box.size)
        if Dimension.LARGEST.eq(which): return max(self.box.size)
        return None


def start_symbol(scope):
    CONTEXT.append(scope)
    return scope


def consumer(f):
    def consumer_wrapper(*args, **kwargs):
        result = f(*args, **kwargs)
        ctx = CONTEXT.pop()
        return result

    return consumer_wrapper


def weighted_choice(weights):
    total = sum(weights)
    i = 0
    r = random.random() * total
    current = weights[0]
    while current < r:
        i += 1
        current += weights[i]
    return i


def fst(t):
    return t[0]


def snd(t):
    return t[1]


def trd(t):
    return t[2]


def clearrules(mod):
    todel = []
    for r in RULES:
        if r.startswith(mod + ":"):
            todel.append(r)
    for t in todel:
        del RULES[t]


def rule(probability=1, constraint=None):
    def rule_inner(f):
        key = f.__code__.co_filename + ":" + f.__name__
        if key not in RULES:
            RULES[key] = []
        RULES[key].append((probability, Constraint.TRUE if (constraint is None) else constraint, f))

        def rule_wrapper(*args, **kwargs):
            if len(args) and isinstance(args[0], Scope):
                ctx = args[0]
            else:
                ctx = CONTEXT[-1]
            chosenf = None
            all_options = RULES[key]
            options = list([o for o in all_options if o[1].evaluate(ctx)])
            if not options:
                options = list([o for o in all_options if o[1].op == "else"])
            if not options:
                print("No applicable rule found for", key, "on frame", ctx)
                void()
                return
            i = weighted_choice(list(map(fst, options)))
            chosenf = options[i][2]
            return chosenf(*args, **kwargs)

        return rule_wrapper

    if callable(probability):
        f = probability
        probability = 1
        return rule_inner(f)
    return rule_inner


def make_split(a, b, sizes, rounding_mode=Rounding.TRUNCATE, repeat=False):
    abssizes = 0
    relsizes = 0
    for s in sizes:
        if s > 0:
            abssizes += s
        else:
            relsizes += s
    total = b - a
    relsizes = abs(relsizes)
    reltotal = total - abssizes
    if relsizes > 0:
        relperunit = int(reltotal / relsizes)
    else:
        relperunit = 0

    result = []
    current = a
    do_split = True
    while do_split:
        do_split = repeat
        for s in sizes:
            if s > 0:
                to = current + s
            else:
                to = current + (-s) * relperunit

            if to > b:
                print("Split", sizes, "exceeded size when splitting from", a, "to", b)
            if to >= b and repeat:
                to = b
                do_split = False
            result.append((current, to))
            current = to
    return result


def split(direction, sizes, rounding_mode=Rounding.TRUNCATE, x=None, y=None, z=None, repeat=False):
    ctx = CONTEXT[-1]
    ctx.split(direction, sizes, rounding_mode=rounding_mode, x=x, y=y, z=z, repeat=repeat)
    return ctx


def reorient(x=None, y=None, z=None):
    ctx = CONTEXT[-1]
    ctx.reorient(x, y, z)
    return ctx


def rotate(degrees):
    """
    Rota el scope actual alrededor del eje Y.
    Para usar con 'with rotate(90):'
    """
    ctx = CONTEXT[-1]
    ctx.rotate(degrees)
    return ctx


def empty(dimension=None):
    """
    Returns true if the current context has size 0 in the given dimension. If dimension=None (default), return true if the current context has size 0 in all dimensions.
    """
    context = CONTEXT[-1]
    if dimension is None:
        return (abs(context.box.volume) == 0)
    elif Dimension.X.eq(dimension):
        return (abs(context.box.size[context.x]) == 0)
    elif Dimension.Y.eq(dimension):
        return (abs(context.box.size[context.y]) == 0)
    elif Dimension.Z.eq(dimension):
        return (abs(context.box.size[context.z]) == 0)
    raise "Invalid Dimension: " + str(dimension)


def unit(dimension=None):
    """
    Returns true if the current context has size 1 in the given dimension. If dimension=None (default), return true if the current context has size 1 in all dimensions.
    """
    context = CONTEXT[-1]
    if dimension is None:
        return (abs(context.box.volume) == 1)
    elif Dimension.X.eq(dimension):
        return (abs(context.box.size[context.x]) == 1)
    elif Dimension.Y.eq(dimension):
        return (abs(context.box.size[context.y]) == 1)
    elif Dimension.Z.eq(dimension):
        return (abs(context.box.size[context.z]) == 1)
    raise "Invalid Dimension: " + str(dimension)


def atom(dimension=None):
    """
    Returns true if the current context can not be subdivided any further in the given dimension, or in all dimensions, if dimension is None (default)
    """
    return (empty(dimension) or unit(dimension))


@consumer
def fill(material=-1):
    CONTEXT[-1].fill(MATERIALS.get(material, material))


@consumer
def void():
    CONTEXT[-1].fill(MATERIALS.get(0, 0))


@consumer
def skip():
    pass


def register_material(id, mat):
    MATERIALS[id] = mat


def make_box(origin, size):
    return BoundingBox(tuple(origin), tuple(size))


def box():
    return CONTEXT[-1].box