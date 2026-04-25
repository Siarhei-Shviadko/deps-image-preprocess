from uuid import uuid4

import factory

from deps_image_preprocess.domain.entities import UnifiedImage


class UnifiedImageFactory(factory.Factory):
    class Meta:
        model = UnifiedImage

    id = factory.LazyAttribute(lambda o: uuid4().hex)
    blob_name = factory.Faker("file_path", depth=3, category="image")
