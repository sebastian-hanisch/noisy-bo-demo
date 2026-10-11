"""Das Terminal als Simulator: Kosten je Stunde aus Geräten, Stellplätzen und Wartezeit (nur für den Tabellengenerator und die Orakel-Tests)."""

import nbo_constants as C
import nbo_formulas as F
import nbo_network as N


def stack_means(speed):
    """Mittlere Dauer je Station (Gate, Kran, Stapel) bei Stapeltempo `speed`."""
    return [C.GATE_MEAN, C.KRAN_BASE_MEAN / C.KRAN_SPEED, C.STAPEL_BASE_MEAN / speed]


def device_cost(places, speed):
    """Gerätekosten (EUR/h); das Tempo geht quadratisch ein."""
    return C.K_GATE * C.GATE_SERVERS + C.K_KRAN * C.KRAN_SERVERS * C.KRAN_SPEED ** 2 + C.K_STAPEL * C.STAPEL_SERVERS * speed ** 2 + C.K_PLACE * places


def total_cost(places, speed, total_time):
    """Gesamtkosten (EUR/h) = Gerätekosten + Wartekosten (V_WAIT je Lkw-Stunde, γ Lkw je Stunde)."""
    return device_cost(places, speed) + C.V_WAIT * C.GAMMA_PER_HOUR * total_time / 60.0


def simulate_time(places, speed, trucks, seed):
    """Eine Simulation: mittlere Gesamtzeit eines Lkw in Minuten, bei Überlast auf C.T_CAP gekappt."""
    m = stack_means(speed)
    servers = [C.GATE_SERVERS, C.KRAN_SERVERS, C.STAPEL_SERVERS]
    gamma = C.GAMMA_PER_HOUR / 60.0
    if max(gamma * m[i] / servers[i] for i in range(3)) >= 1.0:
        return C.T_CAP
    res = N.simulate(gamma, servers, m, C.CS2, F.routing_matrix(0.0), trucks, seed, cap=[None, None, places])
    return min(res.mean_sojourn, C.T_CAP)


def simulate_cost(places, speed, trucks, seed):
    return total_cost(places, speed, simulate_time(places, speed, trucks, seed))
