from steamship import PluginInstance, Steamship, Tag, Task
from steamship.agents.schema import AgentContext

from generators.image_generator import ImageGenerator
from generators.music_generator import MusicGenerator
from schema.objects import Item


class DummyGenerator(MusicGenerator, ImageGenerator):
    plugin_instance: PluginInstance

    def __init__(self, client: Steamship):
        super().__init__(plugin_instance=client.use_plugin("test-image-generator"))

    def dummy_generation(self) -> Task:
        return self.plugin_instance.generate(text="Dummy", tags=[Tag(kind="dummy")])

    def request_item_image_generation(self, item: Item, context: AgentContext) -> Task:
        return self.dummy_generation()

    def request_profile_image_generation(self, context: AgentContext) -> Task:
        return self.dummy_generation()

    def request_scene_image_generation(
        self, description: str, context: AgentContext
    ) -> Task:
        return self.dummy_generation()

    def request_camp_image_generation(self, context: AgentContext) -> Task:
        return self.dummy_generation()

    def request_scene_music_generation(
        self, description: str, context: AgentContext
    ) -> Task:
        return self.dummy_generation()

    def request_camp_music_generation(self, context: AgentContext) -> Task:
        return self.dummy_generation()

    def request_adventure_image_generation(self, context: AgentContext) -> Task:
        return self.dummy_generation()
