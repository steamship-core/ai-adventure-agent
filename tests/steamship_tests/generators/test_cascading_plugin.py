import pytest
from steamship import PluginInstance, Block

from generators.cascading_plugin import CascadingPlugin, ExhaustedPluginsException


class DummyInstance(PluginInstance):
    count: int = 0
    throw: bool = False

    def generate(self, *args, **kwargs):
        if self.throw:
            raise Exception(f"{self.count}")
        self.count += 1
        return Block(text=f"{self.plugin_id}_{self.count}")


def test_cascade_with_failures():
    instance_1 = DummyInstance(plugin_id="Instance1")
    instance_2 = DummyInstance(plugin_id="Instance2")
    providers = [
        lambda: instance_1,
        lambda: instance_2
    ]

    pi: PluginInstance = CascadingPlugin(instance_providers=providers)
    assert pi.generate(text="First Call") == Block(text="Instance1_1")
    assert pi.generate(text="Second Call") == Block(text="Instance1_2")
    instance_1.throw = True
    assert pi.generate(text="Third Call") == Block(text="Instance2_1")
    assert pi.generate(text="Fourth Call") == Block(text="Instance2_2")
    instance_2.throw = True
    with pytest.raises(ExhaustedPluginsException) as e:
        pi.generate(text="Fifth Call")
    assert e.value.exceptions.keys() == set(["Instance1", "Instance2"])
    # Test that we can still generate after that
    instance_1.throw = False
    assert pi.generate(text="Sixth Call") == Block(text="Instance1_3")
