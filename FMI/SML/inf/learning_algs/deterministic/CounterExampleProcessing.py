from FMI.SML.inf.base import SUL
from FMI.SML.inf.utils.HelperFunctions import all_suffixes, all_prefixes


def longest_prefix_cex_processing(s_union_s_dot_a: list, cex: tuple, closedness='suffix'):
    prefixes = s_union_s_dot_a
    prefixes.reverse()
    trimmed_suffix = None

    for p in prefixes:
        if p == cex[:len(p)]:
            trimmed_suffix = cex[len(p):]
            break

    trimmed_suffix = trimmed_suffix if trimmed_suffix else cex
    suffixes = all_suffixes(trimmed_suffix) if closedness == 'suffix' else all_prefixes(trimmed_suffix)
    suffixes.reverse()
    return suffixes

def rs_cex_processing(sul: SUL, cex: tuple, hypothesis, suffix_closedness=True, closedness='suffix'):

    cex_out = sul.query(cex)
    cex_input = list(cex)

    lower = 1
    upper = len(cex_input) - 2

    while True:
        hypothesis.reset_to_initial()
        mid = (lower + upper) // 2

        for s_p in cex_input[:mid]:
            hypothesis.step(s_p)
        s_bracket = hypothesis.current_state.prefix

        d = tuple(cex_input[mid:])
        mq = sul.query(s_bracket + d)

        if mq[-1] == cex_out[-1]:  # only check if the last element is the same as the cex
            lower = mid + 1
            if upper < lower:
                suffix = tuple(d[1:])
                break
        else:
            upper = mid - 1
            if upper < lower:
                suffix = d
                break

    if suffix_closedness:
        suffixes = all_suffixes(suffix) if closedness == 'suffix' else all_prefixes(suffix)
        suffixes.reverse()
        suffix_to_query = suffixes
    else:
        suffix_to_query = [suffix]
    return suffix_to_query
