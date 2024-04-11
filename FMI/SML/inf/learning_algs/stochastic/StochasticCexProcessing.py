from FMI.SML.inf.automata import Mdp
from FMI.SML.inf.base import SUL


def stochastic_longest_prefix(cex, prefixes):

    prefixes = list(prefixes)
    prefixes.sort(key=len, reverse=True)

    trimmed_cex = None
    trimmed = False
    for p in prefixes:
        if p[1::2] == cex[:len(p)][1::2]:
            trimmed_cex = cex[len(p):]
            trimmed = True
            break
    trimmed_cex = trimmed_cex if trimmed else cex
    trimmed_cex = list(trimmed_cex)

    if not trimmed_cex:
        return ()

    suffixes = [tuple(trimmed_cex[len(trimmed_cex) - i - 1:]) for i in range(0, len(trimmed_cex), 2)]

    return suffixes

def stochastic_rs(sul: SUL, cex: tuple, hypothesis):
    if isinstance(hypothesis, Mdp):
        cex = cex[1:]

    inputs = tuple(cex[::2])
    outputs = tuple(cex[1::2])

    lower = 1
    upper = len(inputs) - 2

    while True:
        hypothesis.reset_to_initial()
        mid = (lower + upper) // 2

        for i, o in zip(inputs[:mid], outputs[:mid]):
            hypothesis.step_to(i, o)

        s_bracket = hypothesis.current_state.prefix


        prefix_inputs = s_bracket[1::2] if isinstance(hypothesis, Mdp) else s_bracket[::2]

        not_same = False

        prefix_reached = False
        while not prefix_reached:
            hypothesis.reset_to_initial()
            sul.post()
            sul.pre()

            repeat = False
            for inp in prefix_inputs:
                o_sul = sul.step(inp)
                o_hyp = hypothesis.step_to(inp, o_sul)

                if o_hyp is None:
                    repeat = True
                    break

            prefix_reached = not repeat

        for inp in inputs[mid:]:

            o_sul = sul.step(inp)
            o_hyp = hypothesis.step_to(inp, o_sul)

            if o_hyp is None:
                not_same = True
                break

        if not not_same:
            lower = mid + 1
            if upper < lower:
                suffix = cex[(mid + 1) * 2:]
                break
        else:
            upper = mid - 1
            if upper < lower:
                suffix = cex[mid * 2:]
                break

    suffixes = [tuple(suffix[len(suffix) - i - 1:]) for i in range(0, len(suffix), 2)]

    return suffixes
