from shared.domain.value_objects.selection_strategy import SelectionStrategy
from contexts.retrofit_workflow.domain.value_objects.task_priority import PriorityConditionType
from optimizer.parameter_model import DiscreteParameter, GroupParameter, ListParameter

collection_to_retrofit_parameter = GroupParameter(
    params={
        "base_priority": DiscreteParameter((1, 2, 3)),
        "hold_until": GroupParameter(
            params={
                "condition": DiscreteParameter((PriorityConditionType.TARGET_FILL_BELOW,)),
                "threshold": DiscreteParameter((0.7, 0.85)),
            },
            optional=True,
        ),
        "max_hold_time": DiscreteParameter((None, 30.0)),
        "rules": ListParameter(
            slots=(
                GroupParameter(
                    params={
                        "condition": DiscreteParameter((PriorityConditionType.SOURCE_FILL_ABOVE,)),
                        "threshold": DiscreteParameter((0.4, 0.7)),
                        "priority": DiscreteParameter((1,)),
                    },
                    optional=True,
                ),
                GroupParameter(
                    params={
                        "condition": DiscreteParameter((PriorityConditionType.SOURCE_FILL_ABOVE,)),
                        "threshold": DiscreteParameter((0.7, 0.9)),
                        "priority": DiscreteParameter((0,)),
                    },
                    optional=True,
                ),
            )
        ),
    },
    optional=True,
)

retrofit_to_workshop_parameter = GroupParameter(
    params={
        "base_priority": DiscreteParameter((2, 3)),
        "rules": ListParameter(
            slots=(
                GroupParameter(
                    params={
                        "condition": DiscreteParameter((PriorityConditionType.TARGET_IDLE,)),
                        "threshold": DiscreteParameter((0.0,)),
                        "priority": DiscreteParameter((0,)),
                    },
                    optional=True,
                ),
                GroupParameter(
                    params={
                        "condition": DiscreteParameter((PriorityConditionType.SOURCE_FILL_BELOW,)),
                        "threshold": DiscreteParameter((0.1, 0.2)),
                        "priority": DiscreteParameter((5,)),
                    },
                    optional=True,
                ),
            )
        ),
    },
    optional=True,
)

workshop_to_retrofitted_parameter = GroupParameter(
    params={
        "base_priority": DiscreteParameter((1, 2)),
    },
    optional=True,
)

retrofitted_to_parking_parameter = GroupParameter(
    params={
        "base_priority": DiscreteParameter((2, 3)),
        "hold_until": GroupParameter(
            params={
                "condition": DiscreteParameter((PriorityConditionType.SOURCE_FILL_ABOVE,)),
                "threshold": DiscreteParameter((0.15, 0.35)),
            },
            optional=True,
        ),
        "max_hold_time": DiscreteParameter((None, 45.0)),
        "rules": ListParameter(
            slots=(
                GroupParameter(
                    params={
                        "condition": DiscreteParameter((PriorityConditionType.SOURCE_FILL_ABOVE,)),
                        "threshold": DiscreteParameter((0.4, 0.65)),
                        "priority": DiscreteParameter((1,)),
                    },
                    optional=True,
                ),
                GroupParameter(
                    params={
                        "condition": DiscreteParameter((PriorityConditionType.SOURCE_FILL_ABOVE,)),
                        "threshold": DiscreteParameter((0.7, 0.85)),
                        "priority": DiscreteParameter((0,)),
                    },
                    optional=True,
                ),
            )
        ),
    },
    optional=True,
)

selection_strategy_parameter = DiscreteParameter((
    SelectionStrategy.LEAST_OCCUPIED,
    # SelectionStrategy.MOST_AVAILABLE, semantically equivalent to LEAST_OCCUPIED, so not needed in search space
    SelectionStrategy.FIRST_AVAILABLE,
    SelectionStrategy.ROUND_ROBIN,
    SelectionStrategy.RANDOM,
    SelectionStrategy.BEST_FIT,
    SelectionStrategy.SHORTEST_QUEUE,
))

parameter_config = GroupParameter(
    optional=False,
    params={
        # "collection_track_strategy": selection_strategy_parameter,
        # "retrofit_selection_strategy": selection_strategy_parameter,
        # "retrofitted_selection_strategy": selection_strategy_parameter,
        # "workshop_selection_strategy": selection_strategy_parameter,
        # "parking_selection_strategy": selection_strategy_parameter,
        "task_priorities": GroupParameter(
            optional=False,
            params={
                "collection_to_retrofit": collection_to_retrofit_parameter,
                "retrofit_to_workshop": retrofit_to_workshop_parameter,
                "workshop_to_retrofitted": workshop_to_retrofitted_parameter,
                "retrofitted_to_parking": retrofitted_to_parking_parameter,
            }
        )
    }
)