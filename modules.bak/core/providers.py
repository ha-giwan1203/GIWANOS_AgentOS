
from dependency_injector import containers, providers
from modules.core.fixed_memory import FixedMemory
from modules.core.context_aware_decision_engine import ContextAwareDecisionEngine
from modules.core.master_loop import MasterLoop

class Container(containers.DynamicContainer):
    memory_db = providers.Singleton(FixedMemory)
    context_engine = providers.Singleton(ContextAwareDecisionEngine, memory_db=memory_db)
    master_loop   = providers.Singleton(MasterLoop, context_engine=context_engine)

container = Container()


