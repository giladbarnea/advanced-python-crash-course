from typing import Type, Generic, TypeVar


def requests_get(url: str) -> dict:
    return {
        "cache_invalidation": {
            "id":           "000",
            "status":       "in_review",
            "started":      "long time ago",
            "story_points": 1,
            "priority":     "high",
            },
        "raising_ami":        {
            "id":           "001",
            "status":       "in_progress",
            "started":      "10 months ago",
            "story_points": 999999,
            "priority":     "critical",
            },
        }


def get_tasks(user) -> dict:
    return requests_get(f"www.jira.com/{user}/tasks")


class cached_property:
    def __init__(self, function):
        self.function = function

    def __get__(self, instance, cls):
        if instance is None:
            return self
        value = self.function(instance)
        instance.__dict__[self.function.__name__] = value  # Removes its own reference! 🤯
        return value


TInstance = TypeVar("TInstance")
TProperty = TypeVar("TProperty", bound=Type)


class StronglyTypedProperty(Generic[TInstance, TProperty]):
    """Yells at you if you set the wrong type"""

    def __init__(self, name: str = None, type: TProperty = None):
        self.name = name
        self.type = type

    def __get__(self, instance: TInstance, cls: Type[TInstance]):
        return instance.__dict__[self.name]

    def __set__(self, instance: TInstance, value: TProperty):
        if not isinstance(value, self.type):
            raise TypeError(f"Property '{self.name}' must be of type {self.type} (got {type(value)})")
        instance.__dict__[self.name] = value

    def __delete__(self, instance: TInstance):
        raise TypeError(f"{self.name} cannot be deleted, it is strong! 💪")

    def __set_name__(self, cls: Type[TInstance], property_name: str):
        self.name = property_name
        self.type = cls.__annotations__[property_name]


class StronglyTypedMetaClass(type):
    """Automatically makes your `field: type` a StronglyTypedProperty"""

    def __init__(cls, cls_name: str, bases: tuple, namespace: dict):
        for property_name, type_annotation in cls.__annotations__.items():
            existing_field = getattr(cls, property_name, None)
            if not isinstance(existing_field, StronglyTypedProperty):
                strongly_typed_property = StronglyTypedProperty(property_name, type_annotation)
                setattr(cls, property_name, strongly_typed_property)
        super().__init__(cls_name, bases, namespace)


class Dictionary(dict):
    """
    this.is.better
    this['is']['annoying']
    """

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError:
            raise AttributeError(key)

    __dict__ = property(lambda self: self)


class Task(Dictionary, metaclass=StronglyTypedMetaClass):
    id: str
    status: str
    started: str
    story_points: int
    priority: str

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return self.id == other.id

    def __gt__(self, other):
        return self.priority == "critical" and other.priority == "high"


class Teammate:
    name: str = StronglyTypedProperty()
    tasks: Dictionary[str, Task]
    tired = False

    def __init__(self, name: str):
        self.name = name

    @cached_property
    def tasks(self):
        tasks_regular_dict = get_tasks(self.name)
        cast_tasks = {task_name: Task(task) for task_name, task in tasks_regular_dict.items()}
        cool_dictionary_of_tasks = Dictionary(cast_tasks)
        return cool_dictionary_of_tasks

    def tell_everyone_what_im_working_on(self):
        print(f"Working on {self.tasks}")

    def __str__(self):
        return f"{self.name} has {len(self.tasks)} tasks. He is {'tired' if self.tired else 'not tired'}."

    def __repr__(self):
        return f"{self.__class__.__name__}('{self.name}')"

    def __bool__(self):
        return not self.tired

    def __enter__(self):
        if self.tired:
            raise BrokenPipeError("I need to sleep")
        return self

    def __exit__(self, exception_type, exception_instance, traceback):
        self.tired = True  # regardless. lol

    def __call__(self, tasks: dict):
        self.tasks.update(tasks)


class Team:
    members: list[Teammate] = []

    def __init__(self, *team_members) -> None:
        self.members = list(map(Teammate, team_members))

    def __contains__(self, item):
        return item in self.members

    def __iter__(self):
        return iter(self.members)

    def __getitem__(self, slice):
        return self.members[slice]

    def start_daily(self):
        print(f'Starting daily!')
        for member in self:
            print(member, end=' ')
            if member:
                member.tell_everyone_what_im_working_on()


bob = Team("Einstein", "Newton", "Tesla")
bob.start_daily()
einstein = bob[0]
print(einstein in bob)  # True
print(type(einstein.tasks))
# einstein.name = 3
with einstein as yalla_einstein:
    yalla_einstein({
        "general_relativity":
            Task(id="003", status="to_do", started="1905", story_points=3, priority="high")
        })
print(einstein)
# with einstein as ein:
#     ein({"002": Task(id="002", status="in_progress", started="10 months ago", story_points=999999, priority="critical")})
print(einstein.tasks.raising_ami.story_points)
# del einstein.name
bob.start_daily()
