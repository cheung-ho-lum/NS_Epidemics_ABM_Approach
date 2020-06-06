from Parameters import AgentParams
from mesa import Agent

class SEIR_Agent(Agent):
    """Base Agent type"""
    def __init__(self, unique_id, model, location=-1, population=0,
                 epi_characteristics=None):
        super().__init__(unique_id, model)
        self._location = location
        if population == 0:
            print('creating agent with 0 population?')
        self._population = {
            AgentParams.STATUS_SUSCEPTIBLE: population,
            AgentParams.STATUS_EXPOSED: 0,
            AgentParams.STATUS_INFECTED: 0,
            AgentParams.STATUS_RECOVERED: 0,
        }


        if epi_characteristics == None:
            self._epi_characteristics = {'alpha': AgentParams.DEFAULT_ALPHA,
                                         'gamma': AgentParams.DEFAULT_GAMMA,
                                         'beta': AgentParams.DEFAULT_BETA}
        else:
            self._epi_characteristics = epi_characteristics

    def move(self):
        # For now, agents do not move!
        return None

    def update_agent_health(self):
        # Sick are infected based on viral load
        # Everyone else ignores viral load and follows alpha/gamma.
        # If exposed, move to next stage given enough time has passed
        #TODO: maybe we should be using fractions all along? Reference ODE materials

        coeff_beta = self._epi_characteristics['beta']
        coeff_alpha = self._epi_characteristics['alpha']
        coeff_gamma = self._epi_characteristics['gamma']

        susceptible = self._population[AgentParams.STATUS_SUSCEPTIBLE]
        exposed = self._population[AgentParams.STATUS_EXPOSED]
        infected = self._population[AgentParams.STATUS_INFECTED]
        recovered = self._population[AgentParams.STATUS_RECOVERED]
        normalization_factor = susceptible + exposed + infected + recovered
        terminal_velocity = 10
        if infected > 0:
            terminal_velocity = normalization_factor / infected #TODO: lol? the idea is someetimes alpha is too high
        coeff_beta = min(terminal_velocity, coeff_beta)

        self._population[AgentParams.STATUS_SUSCEPTIBLE] -= susceptible * infected * coeff_beta / normalization_factor

        self._population[AgentParams.STATUS_EXPOSED] += susceptible * infected * coeff_beta / normalization_factor - \
                                                    exposed * coeff_alpha
        self._population[AgentParams.STATUS_INFECTED] += exposed * coeff_alpha - infected * coeff_gamma
        self._population[AgentParams.STATUS_RECOVERED] += infected * coeff_gamma

        return None

    def step(self):
        # viral load modeling now moved to model level.
        self.update_agent_health()

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, value):
        self._location = value

    @property
    def population(self):
        return self._population

    @population.setter
    def population(self, value):
        self._population = value

    @property
    def epi_characteristics(self):
        return self._epi_characteristics

    @epi_characteristics.setter
    def epi_characteristics(self, value):
        self._epi_characteristics = value
