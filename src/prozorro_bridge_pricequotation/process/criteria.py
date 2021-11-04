requirement_keys = ("minValue", "maxValue", "expectedValue")


async def get_criteria(criterias: list) -> list:
    for criterion in criterias:
        criterion.pop("code", None)
        for rq_group in criterion.get("requirementGroups", []):
            for rq in rq_group.get("requirements", []):
                if rq.get("dataType") == 'string':
                    continue
                for key in requirement_keys:
                    if key in rq:
                        rq[key] = str(rq[key])
    return criterias
