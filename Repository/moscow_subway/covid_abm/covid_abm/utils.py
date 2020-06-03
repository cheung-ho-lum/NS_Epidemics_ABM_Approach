from enum import Enum


class State(Enum):
    SUSCEPTIBLE = 0
    INFECTED = 1
    ERADICATED = 2


def number_state(model, state):
    return sum([1 for a in model.grid.get_all_cell_contents() if a.state is state])


def number_infected(model):
    return number_state(model, State.INFECTED)


def number_susceptible(model):
    return number_state(model, State.SUSCEPTIBLE)


def number_eradicated(model):
    return number_state(model, State.ERADICATED)
