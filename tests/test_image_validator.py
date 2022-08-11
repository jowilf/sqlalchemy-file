import base64
import tempfile

import pytest
from sqlalchemy import Column, Integer, String, select
from sqlalchemy.orm import Session, declarative_base
from sqlalchemy_file.exceptions import (
    AspectRatioValidationError,
    DimensionValidationError,
)
from sqlalchemy_file.storage import StorageManager
from sqlalchemy_file.types import ImageField
from sqlalchemy_file.validators import ImageValidator

from tests.utils import get_test_container, get_test_engine

engine = get_test_engine()
Base = declarative_base()


@pytest.fixture
def fake_image_low_width():  # width=5, height=10
    file = tempfile.NamedTemporaryFile(suffix=".png")
    data = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAUAAAAKCAYAAAB8OZQwAAAAAXNSR0IArs4c6QAAAHNJREFUGFd9zkEHhCEUheHTJiIRtYyW/f9"
        "/0q5NRNpFJKLNHc2Y1XzmLh+u87IYIxlj8L3eO9hF5xy01hhjoNYKlnOmcw5CCEgpgXMO1lqjOSeklFhrQSn1QSEESinw3mPv/Qd/3h"
        "+HHpMuWmtBRO/+G/8CjIpct7mYGLEAAAAASUVORK5CYII="
    )
    file.write(data)
    file.seek(0)
    return file


@pytest.fixture
def fake_image_low_height():  # width=10, height=7
    file = tempfile.NamedTemporaryFile(suffix=".png")
    data = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAHCAYAAAAxrNxjAAAAAXNSR0IArs4c6QAAAKNJREFUKFNtj8sKhCAYhU+LsOiy0YVIBr3/y"
        "/gGQam0qI0UES4KHWZqhvlXB/6Pc0mUUmeWZaiqCv/OOYfjOJBorU/vPfZ9h5QSZVlGfl1XjOOIPM"
        "+RpikSY8wphMA8z9Bag3MewWma0DQNGGOw1t5geIaYvu8j2HUd6rqO+gtcliVGPR1DFUrpC3x2bNsWRVFEl23bMAzD3TGsJoR8Yn6Xv1df"
        "/fReRqm21woAAAAASUVORK5CYII="
    )
    file.write(data)
    file.seek(0)
    return file


@pytest.fixture
def fake_image_huge_width():  # width=20, height=10
    file = tempfile.NamedTemporaryFile(suffix=".png")
    data = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAABQAAAAKCAYAAAC0VX7mAAAAAXNSR0IArs4c6QAAAPJJREFUOE+lkjEKg0AQRf"
        "+CFoKNWghWgnZ2Nh7AztJbWHkJ72AhHsFOsPIMIngEFaxsBC2EDa4oScBEkqmW4f+3"
        "/JkhVVXRMAyRJAlEUcQvtSwLpmliVtJ1HY3jGI7jwDRNqKoKSZJuccdxxDAMTLv55nnegUVRQNd12Lb9IrgCv4MOXd/3O7AsSyiKAs"
        "/z2G9Xhqv+EecE5nkOwzDguu5L1AOwrivrcxz3cSQnME1T+L4Py7L+B7ZtS4MgQJZl4Hn+/8iyLDNgFEWXs3tf"
        "+celNE1DNU27td1vYHY2dV3TTbgdtSAIoJSCEMK82/tOPR/2A3aLsV8FPmE1AAAAAElFTkSuQmCC"
    )
    file.write(data)
    file.seek(0)
    return file


@pytest.fixture
def fake_image_huge_height():  # width=10, height=17
    file = tempfile.NamedTemporaryFile(suffix=".png")
    data = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAoAAAARCAYAAADkIz3lAAAAAXNSR0IArs4c6QAAAQpJREFUKFOVkj2LhEAMhjOF2wgq6xfa2CiK+P9"
        "/h4WIooUWKqIuq2CjxRzJsR5y3t1eqiF5JnnfzLA4jrlhGMA5h59iGAZgSZJwTdPANM1Lru97GMcRWFVVfJomiKIIbrfbCd62DZIkAVV"
        "VgTVNQzP3fQfHcU5gXdcgCALlCLQsi24iKEkSFZZlAQRxUtd1n6Bt2/B4PABF+75PYJ7noOs63O93aNv2C8RiURQgyzKB8zyD53l0/"
        "gau6wplWVLRdV0QRfEaxGyaplQMw/AwdtkRx2Pg2FfHk5mXRkVRCHw+n4fGE4hLR9dBEBCYZRm5xmUf4Nt7/OtlGGP/eOt3fg/qZ/gf"
        "UfRvgSY/AOhSyq08LXSPAAAAAElFTkSuQmCC"
    )
    file.write(data)
    file.seek(0)
    return file


@pytest.fixture
def fake_image_invalid_ratio():  # width=10, height=15
    file = tempfile.NamedTemporaryFile(suffix=".png")
    data = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAPCAYAAADd/14OAAAAAXNSR0IArs4c6QAAAMFJREFUKFOdUrEKhDAUy3N1EMEuou76/x"
        "/iVHetToI4dG2PVMop54F32UpDkpf3pO97r5TCN3jvsa4rRGvt0zRF0zS33HEcYa2FGGP8tm2o6xpZll3I"
        "+75jmibkeQ6Z5zkoGmPQti2SJAlk5xyGYUBVVYciiWVZghZEjHB+L8vyJlJBax0iELTsui44XIj8ZCYqicgl8weRZKoSVIu4VaQlu2PW2MJ"
        "/GR9NzR7PU8YeYwu/bebxrnk9RVGE7u4Qr+cFO529ZB6GXB0AAAAASUVORK5CYII= "
    )
    file.write(data)
    file.seek(0)
    return file


@pytest.fixture
def fake_valid_image():  # width=14, height=15
    file = tempfile.NamedTemporaryFile(suffix=".png")
    data = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAA4AAAAPCAYAAADUFP50AAAAAXNSR0IArs4c6QAAASpJREFUOE+tU0GLglAYHIs0hAg0KjO82cn//y"
        "+8eUq6iJZKCiJEGuUyH7Sxm0UsOyd5fsN8M2+e4vt+Z5omRqMRPkHbtijLEsput+vquobrutB1"
        "/S33dDohDENMJhMoSZJ0qqoiTVMha5rWS26aRkjL5RJUFeJqtUKe5zgej0L+vfblchHSbDbDfD7Hfr9"
        "/EClzOBxQVRU2mw0Gg4Eo3243bLdbTKdTWJYlZ09EHiZJAnqhMkElerdt+9tCL5F/oygC1yO4tuM4P3y/JHIqCAIZ9jzvKaz"
        "/VYzjWDwyIILB0ON6vX7t8Z4qgxkOhzJ4vV4loJepZlmGoije3iOruVgsHtfBttAwlcbjcW9zzuezKLMsbNHfu8rXYRiGdLTrOiiKIor87sP9"
        "dXwBhJXeghs+f/MAAAAASUVORK5CYII="
    )
    file.write(data)
    file.seek(0)
    return file


class Book(Base):
    __tablename__ = "book"

    id = Column(Integer, autoincrement=True, primary_key=True)
    title = Column(String(100), unique=True)
    cover = Column(
        ImageField(
            image_validator=ImageValidator(
                min_wh=(10, 10),
                max_wh=(15, 15),
                min_aspect_ratio=12 / 15,
                max_aspect_ratio=1,
            )
        )
    )

    def __repr__(self):
        return "<Book: id %s ; name: %s; cover %s;>" % (
            self.id,
            self.title,
            self.cover,
        )  # pragma: no cover


class TestImageValidator:
    def setup(self) -> None:
        Base.metadata.create_all(engine)
        StorageManager._clear()
        StorageManager.add_storage("test", get_test_container("test-image-validator"))

    def test_min_width_validation(self, fake_image_low_width) -> None:
        with Session(engine) as session:
            session.add(Book(title="Pointless Meetings", cover=fake_image_low_width))
            with pytest.raises(
                DimensionValidationError,
                match="Minimum allowed width is: 10, but 5 is given",
            ):
                session.flush()

    def test_min_height_validation(self, fake_image_low_height) -> None:
        with Session(engine) as session:
            session.add(Book(title="Pointless Meetings", cover=fake_image_low_height))
            with pytest.raises(
                DimensionValidationError,
                match="Minimum allowed height is: 10, but 7 is given.",
            ):
                session.flush()

    def test_max_width_validation(self, fake_image_huge_width) -> None:
        with Session(engine) as session:
            session.add(Book(title="Pointless Meetings", cover=fake_image_huge_width))
            with pytest.raises(
                DimensionValidationError,
                match="Maximum allowed width is: 15, but 20 is given",
            ):
                session.flush()

    def test_max_height_validation(self, fake_image_huge_height) -> None:
        with Session(engine) as session:
            session.add(Book(title="Pointless Meetings", cover=fake_image_huge_height))
            with pytest.raises(
                DimensionValidationError,
                match="Maximum allowed height is: 15, but 17 is given.",
            ):
                session.flush()

    def test_invalid_aspect_ratio(self, fake_image_invalid_ratio) -> None:
        with Session(engine) as session:
            session.add(
                Book(title="Pointless Meetings", cover=fake_image_invalid_ratio)
            )
            with pytest.raises(AspectRatioValidationError):
                session.flush()

    def test_valid_image(self, fake_valid_image) -> None:
        with Session(engine) as session:
            session.add(Book(title="Pointless Meetings", cover=fake_valid_image))
            session.flush()
            book = session.execute(
                select(Book).where(Book.title == "Pointless Meetings")
            ).scalar_one()
            assert book.cover.file is not None

    def teardown(self):
        for obj in StorageManager.get().list_objects():
            obj.delete()
        StorageManager.get().delete()
        Base.metadata.drop_all(engine)
