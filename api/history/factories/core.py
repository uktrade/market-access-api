from .assessments import EconomicAssessmentHistoryFactory
from .assessments.resolvability import ResolvabilityAssessmentHistoryFactory
from .assessments.strategic import StrategicAssessmentHistoryFactory
from .barriers import BarrierHistoryFactory
from .notes import NoteHistoryFactory
from .public_barrier_notes import PublicBarrierNoteHistoryFactory
from .public_barriers import PublicBarrierHistoryFactory
from .team_members import TeamMemberHistoryFactory
from .wto import WTOHistoryFactory

from ..exceptions import HistoryFactoryNotFound
from ..utils import get_model_name


class HistoryItemFactory:
    """
    Proxy class for specific factory classes
    """
    class_lookup = {}
    history_factory_classes = (
        EconomicAssessmentHistoryFactory,
        BarrierHistoryFactory,
        NoteHistoryFactory,
        PublicBarrierHistoryFactory,
        PublicBarrierNoteHistoryFactory,
        ResolvabilityAssessmentHistoryFactory,
        StrategicAssessmentHistoryFactory,
        TeamMemberHistoryFactory,
        WTOHistoryFactory,
    )

    @classmethod
    def get_factory_class(cls, record):
        if not cls.class_lookup:
            cls.init_class_lookup()

        model_name = get_model_name(record)
        history_factory_class = cls.class_lookup.get(model_name)
        if not history_factory_class:
            raise HistoryFactoryNotFound
        return history_factory_class

    @classmethod
    def create(cls, field, new_record, old_record):
        factory_class = cls.get_factory_class(new_record)
        return factory_class.create(field, new_record, old_record)

    @classmethod
    def create_history_items(cls, new_record, old_record, fields=()):
        try:
            factory_class = cls.get_factory_class(new_record)
        except HistoryFactoryNotFound:
            return []
        return factory_class.create_history_items(new_record, old_record, fields)

    @classmethod
    def init_class_lookup(cls):
        """
        Initialise the class lookup so classes can be quickly fetched based on model
        """
        for factory_class in cls.history_factory_classes:
            cls.class_lookup[factory_class.get_model()] = factory_class
