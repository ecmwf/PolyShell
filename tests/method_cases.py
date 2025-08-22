from polyshell.reducer import ReductionMethods


def case_visvalingam_whyatt() -> ReductionMethods:
    return ReductionMethods.VisvalingamWhyatt


def case_charshape() -> ReductionMethods:
    return ReductionMethods.Charshape

def case_ramer_douglas_peucker() -> ReductionMethods:
    return ReductionMethods.RamerDouglasPeucker