"""Numerical integrator for geodesic trajectories in curved spacetime.

Provides a robust, validated numerical integration layer for evolving canonical
geodesic equations of motion:
    dy / dlambda = (dH / dp_mu, -dH / dx^mu)
where H(x, p) = 1/2 * g^{mu nu}(x) * p_mu * p_nu is the canonical Hamiltonian.

The vector field dy/dlambda is evaluated strictly via `geodesics.hamiltonian.hamiltonian_rhs`
without duplicating the mathematical equations. The integration backend is built upon
`scipy.integrate.solve_ivp`, defaulting to the high-order explicit Runge-Kutta method
DOP853 (explicit Runge-Kutta method of order 8 with a 7th-order error estimator)
suitable for non-stiff trajectory integration in curved spacetime.

State vector ordering:
    y = (x0, r, theta, phi, p0, pr, ptheta, pphi)
    - y[0:4] = (x0, r, theta, phi): contravariant coordinates with x0 = c*t
    - y[4:8] = (p0, pr, ptheta, pphi): covariant canonical conjugate momenta

Result array orientation:
    states: shape (n_points, 8) where each row states[i, :] is the 8-component state
    at affine parameter lambdas[i].

Units: Geometrized units G = c = 1.
"""

from dataclasses import dataclass
from typing import Any, Callable, Final, Optional, Sequence, Tuple, Union
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq

from geodesics.constants import (
    DEFAULT_ATOL,
    DEFAULT_RTOL,
    IDX_R,
    IDX_THETA,
)
from geodesics.events import GeodesicEvent
from geodesics.hamiltonian import STATE_DIMENSION, hamiltonian_rhs
from geodesics.metrics.base import SpacetimeMetric

DEFAULT_INTEGRATOR_METHOD: Final[str] = "DOP853"
SUPPORTED_METHODS: Final[Tuple[str, ...]] = (
    "DOP853",
    "RK45",
    "RK23",
    "Radau",
    "BDF",
    "LSODA",
)


@dataclass(frozen=True)
class EventTriggerRecord:
    """Record of triggers for a specific event during numerical integration.

    Attributes
    ----------
    event_index : int
        Index of the event in the events sequence provided to the integrator.
    name : str
        Human-readable name of the event.
    lambdas : np.ndarray
        1D array of shape (k,) with affine parameter values where the event occurred.
    states : np.ndarray
        2D array of shape (k, 8) with state vectors y = (x0, r, theta, phi, p0, pr, ptheta, pphi)
        at each event occurrence.
    terminal : bool
        Whether this event was configured as terminal.
    direction : int
        Configured zero-crossing direction (-1, +1, or 0).
    """

    event_index: int
    name: str
    lambdas: np.ndarray
    states: np.ndarray
    terminal: bool
    direction: int


@dataclass(frozen=True)
class GeodesicIntegrationResult:
    """Container for numerical geodesic integration results.

    Attributes
    ----------
    lambdas : np.ndarray
        1D array of shape (n_points,) containing affine parameter values.
    states : np.ndarray
        2D array of shape (n_points, 8) containing the integrated state vectors
        y(lambda) = (x0, r, theta, phi, p0, pr, ptheta, pphi) at each affine parameter.
    success : bool
        Whether the ODE solver completed the integration successfully.
    status : int
        Termination status code returned by scipy.integrate.solve_ivp:
        0: Integration reached the end of the affine span.
        1: A termination event occurred.
        -1: Integration step failed or solver error.
    message : str
        Human-readable description of the termination reason.
    nfev : int
        Total number of evaluations of the right-hand side vector field.
    method : str
        The ODE solver method utilized (e.g. 'DOP853', 'RK45').
    rtol : float
        Relative tolerance used during integration.
    atol : float
        Absolute tolerance used during integration.
    raw_solution : Optional[Any]
        The native OdeResult object from scipy.integrate.solve_ivp, preserving
        all underlying solver diagnostics.
    t_events : Optional[Tuple[np.ndarray, ...]]
        Tuple of 1D arrays of affine parameters where each event occurred, or None
        if events was not supplied.
    y_events : Optional[Tuple[np.ndarray, ...]]
        Tuple of 2D arrays of shape (k, 8) containing the state vectors at each
        event trigger, or None if events was not supplied.
    event_names : Optional[Tuple[str, ...]]
        Names of all registered events, or None if events was not supplied.
    triggered_events : Tuple[EventTriggerRecord, ...]
        Records for all events that triggered at least once during integration.
    terminal_event_occurred : bool
        Whether a terminal event halted integration (sol.status == 1).
    terminal_event_name : Optional[str]
        Name of the event that caused termination if uniquely identified, or None
        if no terminal event occurred or if multiple terminal events coincided.
    terminal_event_index : Optional[int]
        Index of the event that caused termination if uniquely identified, or None
        if no terminal event occurred or if multiple terminal events coincided.
    terminal_event_indices : Tuple[int, ...]
        Tuple of all event indices that triggered or coincided at the termination root.
        When terminal_event_identity_complete is False, this list is not guaranteed to be
        exhaustive because unresolved omitted candidates remain.
    terminal_event_names : Tuple[str, ...]
        Tuple of names of all terminal events that triggered or coincided at the termination root.
    scipy_recorded_terminal_event_indices : Tuple[int, ...]
        Tuple of event indices actually recorded by SciPy at the termination parameter.
    scipy_recorded_terminal_event_names : Tuple[str, ...]
        Tuple of names of event indices actually recorded by SciPy at the termination parameter.
    inferred_coincident_terminal_indices : Tuple[int, ...]
        Tuple of additional terminal event indices whose roots coincided with final_lambda
        over the final accepted integration step, independently inferred via dense interpolant
        root-solving after being omitted by SciPy's internal single-terminal event cut.
    terminal_event_identity_complete : bool
        Whether all registered terminal events have been accounted for under the documented
        numerical identification policy.
        True if no terminal event occurred, or if all registered terminal events have been
        accounted for under the documented numerical root-matching policy (guaranteed when
        a single terminal event is registered and recorded by SciPy, or when all registered
        terminal events are numerically identified as coincident within root_time_atol).
        False if any registered terminal event remains unresolved (e.g. an omitted terminal event
        that cannot be certified non-coincident on a rigorous, scale-invariant basis).
        Note: Distinct mathematical roots closer than root_time_atol = 100 * eps_mach * max(1, |lambda|)
        are numerically indistinguishable in floating-point arithmetic.
    unresolved_terminal_indices : Tuple[int, ...]
        Tuple of registered terminal event indices whose coincident behavior at the termination
        point could not be definitively ruled out or confirmed within numerical comparison tolerances.
    unresolved_terminal_names : Tuple[str, ...]
        Tuple of names of unresolved terminal events.
    """

    lambdas: np.ndarray
    states: np.ndarray
    success: bool
    status: int
    message: str
    nfev: int
    method: str
    rtol: float
    atol: float
    raw_solution: Optional[Any] = None
    t_events: Optional[Tuple[np.ndarray, ...]] = None
    y_events: Optional[Tuple[np.ndarray, ...]] = None
    event_names: Optional[Tuple[str, ...]] = None
    triggered_events: Tuple[EventTriggerRecord, ...] = ()
    terminal_event_occurred: bool = False
    terminal_event_name: Optional[str] = None
    terminal_event_index: Optional[int] = None
    terminal_event_indices: Tuple[int, ...] = ()
    terminal_event_names: Tuple[str, ...] = ()
    scipy_recorded_terminal_event_indices: Tuple[int, ...] = ()
    scipy_recorded_terminal_event_names: Tuple[str, ...] = ()
    inferred_coincident_terminal_indices: Tuple[int, ...] = ()
    terminal_event_identity_complete: bool = False
    unresolved_terminal_indices: Tuple[int, ...] = ()
    unresolved_terminal_names: Tuple[str, ...] = ()

    @property
    def has_events(self) -> bool:
        """Whether any events were triggered during integration."""
        return len(self.triggered_events) > 0

    @property
    def affine_parameters(self) -> np.ndarray:
        """Alias for lambdas array."""
        return self.lambdas

    @property
    def coordinates(self) -> np.ndarray:
        """Array of shape (n_points, 4) with spacetime coordinates (x0, r, theta, phi)."""
        return self.states[:, :4]

    @property
    def momenta(self) -> np.ndarray:
        """Array of shape (n_points, 4) with canonical conjugate momenta (p0, pr, ptheta, pphi)."""
        return self.states[:, 4:]

    @property
    def x0(self) -> np.ndarray:
        """Coordinate time x0 = ct along the trajectory."""
        return self.states[:, 0]

    @property
    def r(self) -> np.ndarray:
        """Radial coordinate r along the trajectory."""
        return self.states[:, 1]

    @property
    def theta(self) -> np.ndarray:
        """Polar angle theta along the trajectory."""
        return self.states[:, 2]

    @property
    def phi(self) -> np.ndarray:
        """Azimuthal angle phi along the trajectory."""
        return self.states[:, 3]

    @property
    def p0(self) -> np.ndarray:
        """Conjugate momentum p0 = -E along the trajectory."""
        return self.states[:, 4]

    @property
    def pr(self) -> np.ndarray:
        """Radial conjugate momentum pr along the trajectory."""
        return self.states[:, 5]

    @property
    def ptheta(self) -> np.ndarray:
        """Polar conjugate momentum ptheta along the trajectory."""
        return self.states[:, 6]

    @property
    def pphi(self) -> np.ndarray:
        """Axial conjugate momentum pphi = Lz along the trajectory."""
        return self.states[:, 7]


def integrate_geodesic(
    initial_state: np.ndarray,
    metric: SpacetimeMetric,
    affine_span: Tuple[float, float],
    rtol: float = DEFAULT_RTOL,
    atol: float = DEFAULT_ATOL,
    max_step: float = np.inf,
    t_eval: Optional[Union[np.ndarray, Sequence[float]]] = None,
    events: Optional[Union[Callable, Sequence[Callable]]] = None,
    method: str = DEFAULT_INTEGRATOR_METHOD,
) -> GeodesicIntegrationResult:
    """Numerically integrates the geodesic equations of motion in curved spacetime.

    Evolves the canonical Hamiltonian system of first-order ordinary differential equations:
        dx^mu / dlambda =  g^{mu nu} * p_nu
        dp_mu / dlambda = -1/2 * (partial_mu g^{alpha beta}) * p_alpha * p_beta
    over the requested affine-parameter interval [lambda_start, lambda_end] using
    scipy.integrate.solve_ivp.

    The right-hand side vector field is evaluated strictly via `geodesics.hamiltonian.hamiltonian_rhs`.

    Parameters
    ----------
    initial_state : np.ndarray or sequence of float
        Initial 8-component state vector y = (x0, r, theta, phi, p0, pr, ptheta, pphi)
        at affine parameter lambda_start. Must contain only finite real numbers.
        The caller's array is never mutated.
    metric : SpacetimeMetric
        An instance implementing the SpacetimeMetric abstract interface (e.g. SchwarzschildMetric).
    affine_span : Tuple[float, float]
        A 2-tuple (lambda_start, lambda_end) specifying the integration interval.
        Supports both forward (lambda_start < lambda_end) and backward
        (lambda_start > lambda_end) integration. Endpoints must be finite and distinct.
    rtol : float, optional
        Relative error tolerance for the adaptive step-size controller.
        Must be a strictly positive and finite scalar float. Must be greater than or
        equal to the solver's minimum effective relative tolerance (100 * eps_mach ~ 2.22e-14).
        Default is 1e-10.
    atol : float, optional
        Absolute error tolerance for the adaptive step-size controller.
        Must be a strictly positive and finite scalar float. Default is 1e-10.
    max_step : float, optional
        Maximum allowed integration step size in affine parameter.
        Must be strictly positive. Default is np.inf (unbounded step size).
    t_eval : array_like, optional
        Specific affine parameter values at which to store the computed solution.
        If None, stores the internal adaptive time steps chosen by the solver.
        If provided, must be strictly monotonic in the direction of integration
        and lie entirely within affine_span. Note: The solver evaluates states strictly
        at the requested t_eval points; lambda_start is not automatically included
        unless explicitly present in t_eval.
    events : callable or sequence of callable, optional
        Event function or sequence of event functions for root-finding and conditional
        termination during integration. Each event callable must have signature
        event(lambda, y) -> float, where y is the 8-component state vector.
        Instances of `geodesics.events.GeodesicEvent` (such as HorizonCutoffEvent,
        EscapeRadiusEvent, RadialTurningPointEvent) or standard callables with
        `terminal` and `direction` attributes are supported. Default is None.
    method : str, optional
        Integration solver method accepted by scipy.integrate.solve_ivp.
        Must be one of {"DOP853", "RK45", "RK23", "Radau", "BDF", "LSODA"}.
        Default is "DOP853" (explicit Runge-Kutta of order 8 with 7th-order error estimator).

    Returns
    -------
    GeodesicIntegrationResult
        Container holding the integration results, including:
        - lambdas: array of affine parameter points, shape (n_points,)
        - states: array of integrated state vectors, shape (n_points, 8)
        - success, status, message: solver status diagnostics
        - nfev, method, rtol, atol: execution statistics and configuration
        - raw_solution: native OdeResult from scipy.integrate.solve_ivp
        - t_events, y_events: arrays of event trigger times and states
        - triggered_events: tuple of EventTriggerRecord for each triggered event
        - terminal_event_occurred, terminal_event_name, terminal_event_index:
          termination diagnostics if an event halted integration

    Raises
    ------
    TypeError
        If metric is not an instance of SpacetimeMetric, initial_state is not array-like,
        events is not a callable or sequence of callables, or method is not a string.
    ValueError
        If initial_state does not have shape (8,), contains non-finite values, or lies
        outside the metric domain; if affine_span does not have exactly 2 distinct finite
        endpoints; if rtol or atol is not positive and finite; if max_step is non-positive
        or NaN; if t_eval is invalid; or if method is not recognized.
    """
    # 1. Validate metric
    if not isinstance(metric, SpacetimeMetric):
        raise TypeError(
            f"metric must be an instance of SpacetimeMetric, got {type(metric).__name__}"
        )

    # 2. Validate and defensively copy initial_state
    if not isinstance(initial_state, np.ndarray):
        y0 = np.asarray(initial_state, dtype=np.float64)
    else:
        y0 = initial_state.astype(np.float64, copy=True)

    if y0.shape != (STATE_DIMENSION,):
        raise ValueError(
            f"initial_state must have shape ({STATE_DIMENSION},), got {y0.shape}"
        )
    if not np.all(np.isfinite(y0)):
        raise ValueError("initial_state contains non-finite values (NaN or Inf)")

    # Coordinate domain validation using metric properties
    r0 = float(y0[IDX_R])
    theta0 = float(y0[IDX_THETA])
    if hasattr(metric, "horizon_radius") and r0 <= metric.horizon_radius:
        raise ValueError(
            f"Initial radial coordinate r0 = {r0} lies on or within event horizon "
            f"r_H = {metric.horizon_radius}"
        )
    if theta0 <= 0.0 or theta0 >= np.pi:
        raise ValueError(
            f"Initial polar coordinate theta0 = {theta0} must be strictly in (0, pi)"
        )

    # 3. Validate affine parameter span
    if not isinstance(affine_span, (tuple, list)) or len(affine_span) != 2:
        raise ValueError(
            f"affine_span must be a 2-tuple of (lambda_start, lambda_end), got {affine_span!r}"
        )
    lambda_start = float(affine_span[0])
    lambda_end = float(affine_span[1])
    if not np.isfinite(lambda_start) or not np.isfinite(lambda_end):
        raise ValueError(
            f"affine_span endpoints must be finite, got ({lambda_start}, {lambda_end})"
        )
    if lambda_start == lambda_end:
        raise ValueError(
            f"affine_span endpoints must be distinct, got lambda_start == lambda_end == {lambda_start}"
        )

    # 4. Validate tolerances
    if (
        isinstance(rtol, bool)
        or not isinstance(rtol, (int, float))
        or not np.isfinite(rtol)
        or rtol <= 0.0
    ):
        raise ValueError(
            f"rtol must be a strictly positive and finite scalar float, got {rtol}"
        )

    # Minimum effective relative tolerance supported by SciPy's step-size controller
    min_rtol = 100.0 * np.finfo(np.float64).eps  # ~2.2204e-14
    if rtol < min_rtol:
        raise ValueError(
            f"rtol = {rtol:.4e} is below the minimum effective relative tolerance "
            f"supported by the numerical solver (100 * eps_mach = {min_rtol:.4e}). "
            f"SciPy cannot resolve local truncation errors below this threshold."
        )

    if (
        isinstance(atol, bool)
        or not isinstance(atol, (int, float))
        or not np.isfinite(atol)
        or atol <= 0.0
    ):
        raise ValueError(
            f"atol must be a strictly positive and finite scalar float, got {atol}"
        )

    rtol = float(rtol)
    atol = float(atol)

    # 5. Validate max_step
    if isinstance(max_step, bool) or max_step <= 0.0 or np.isnan(max_step):
        raise ValueError(f"max_step must be strictly positive, got {max_step}")
    max_step = float(max_step)

    # 6. Validate method
    if not isinstance(method, str):
        raise TypeError(f"method must be a string, got {type(method).__name__}")
    if method not in SUPPORTED_METHODS:
        raise ValueError(
            f"Unsupported method {method!r}. Supported methods are: {SUPPORTED_METHODS}"
        )

    # 7. Validate t_eval if provided
    t_eval_arr: Optional[np.ndarray] = None
    if t_eval is not None:
        t_eval_arr = np.asarray(t_eval, dtype=np.float64)
        if t_eval_arr.ndim != 1 or t_eval_arr.size == 0:
            raise ValueError(
                f"t_eval must be a non-empty 1D array-like sequence, got shape {t_eval_arr.shape}"
            )
        if not np.all(np.isfinite(t_eval_arr)):
            raise ValueError("t_eval contains non-finite values (NaN or Inf)")

        # Verify strict monotonicity in the direction of integration
        is_forward = lambda_end > lambda_start
        diffs = np.diff(t_eval_arr)
        if is_forward:
            if not np.all(diffs > 0.0):
                raise ValueError(
                    "t_eval values must be strictly increasing for forward integration (lambda_start < lambda_end)."
                )
            if t_eval_arr[0] < lambda_start or t_eval_arr[-1] > lambda_end:
                raise ValueError(
                    f"t_eval range [{t_eval_arr[0]}, {t_eval_arr[-1]}] exceeds affine_span "
                    f"[{lambda_start}, {lambda_end}]."
                )
        else:
            if not np.all(diffs < 0.0):
                raise ValueError(
                    "t_eval values must be strictly decreasing for backward integration (lambda_start > lambda_end)."
                )
            if t_eval_arr[0] > lambda_start or t_eval_arr[-1] < lambda_end:
                raise ValueError(
                    f"t_eval range [{t_eval_arr[0]}, {t_eval_arr[-1]}] exceeds affine_span "
                    f"[{lambda_start}, {lambda_end}]."
                )

    # 8. Validate events if provided
    event_list: Optional[list] = None
    if events is not None:
        if callable(events):
            event_list = [events]
        elif isinstance(events, (list, tuple)):
            event_list = list(events)
            for idx, ev in enumerate(event_list):
                if not callable(ev):
                    raise TypeError(
                        f"Each event must be callable, but event at index {idx} "
                        f"is of type {type(ev).__name__}"
                    )
                if hasattr(ev, "direction"):
                    ev_dir = getattr(ev, "direction")
                    if ev_dir not in (-1, 0, 1):
                        raise ValueError(
                            f"Event at index {idx} has invalid direction {ev_dir!r}. "
                            f"Direction must be in {{-1, 0, 1}}."
                        )
        else:
            raise TypeError(
                f"events must be a callable or sequence of callables, got {type(events).__name__}"
            )

    # 9. Define ODE right-hand side function delegating solely to hamiltonian_rhs
    def geodesic_rhs(_lambda: float, y: np.ndarray) -> np.ndarray:
        return hamiltonian_rhs(y, metric)

    # 10. Execute solve_ivp
    sol = solve_ivp(
        fun=geodesic_rhs,
        t_span=(lambda_start, lambda_end),
        y0=y0,
        method=method,
        t_eval=t_eval_arr,
        events=event_list,
        dense_output=(event_list is not None),
        rtol=rtol,
        atol=atol,
        max_step=max_step,
    )

    # 11. Assemble and return public result container
    # sol.y has internal shape (8, n_points); public orientation is (n_points, 8)
    if isinstance(sol.y, np.ndarray) and sol.y.ndim == 2:
        states = sol.y.T.copy()
    else:
        states = np.empty((0, STATE_DIMENSION), dtype=np.float64)

    if isinstance(sol.t, np.ndarray):
        lambdas = sol.t.copy()
    else:
        lambdas = np.array(sol.t, dtype=np.float64)

    t_events_tuple: Optional[Tuple[np.ndarray, ...]] = None
    y_events_tuple: Optional[Tuple[np.ndarray, ...]] = None
    event_names_tuple: Optional[Tuple[str, ...]] = None
    triggered_records: Tuple[EventTriggerRecord, ...] = ()
    terminal_event_occurred = bool(sol.status == 1)
    terminal_event_name: Optional[str] = None
    terminal_event_index: Optional[int] = None
    terminal_event_indices: Tuple[int, ...] = ()
    terminal_event_names: Tuple[str, ...] = ()
    scipy_recorded_terminal_event_indices: Tuple[int, ...] = ()
    scipy_recorded_terminal_event_names: Tuple[str, ...] = ()
    inferred_coincident_terminal_indices: Tuple[int, ...] = ()
    terminal_event_identity_complete: bool = not terminal_event_occurred
    unresolved_terminal_indices: Tuple[int, ...] = ()
    unresolved_terminal_names: Tuple[str, ...] = ()

    if event_list is not None:
        t_ev_list = []
        y_ev_list = []
        names_list = []
        records_list = []

        sol_t_events = getattr(sol, "t_events", None)
        sol_y_events = getattr(sol, "y_events", None)

        for idx, ev in enumerate(event_list):
            raw_name = getattr(ev, "name", None) or getattr(ev, "__name__", None)
            ev_name = str(raw_name).strip() if raw_name else f"event_{idx}"
            names_list.append(ev_name)

            if (
                sol_t_events is not None
                and hasattr(sol_t_events, "__len__")
                and idx < len(sol_t_events)
                and sol_t_events[idx] is not None
            ):
                t_ev = np.asarray(sol_t_events[idx], dtype=np.float64).copy()
            else:
                t_ev = np.empty(0, dtype=np.float64)
            t_ev_list.append(t_ev)

            if (
                sol_y_events is not None
                and hasattr(sol_y_events, "__len__")
                and idx < len(sol_y_events)
                and sol_y_events[idx] is not None
                and getattr(sol_y_events[idx], "ndim", 0) == 2
            ):
                y_ev = np.asarray(sol_y_events[idx], dtype=np.float64).copy()
            else:
                y_ev = np.empty((0, STATE_DIMENSION), dtype=np.float64)
            y_ev_list.append(y_ev)

            if len(t_ev) > 0:
                is_terminal = bool(getattr(ev, "terminal", False))
                ev_dir = int(getattr(ev, "direction", 0))
                records_list.append(
                    EventTriggerRecord(
                        event_index=idx,
                        name=ev_name,
                        lambdas=t_ev,
                        states=y_ev,
                        terminal=is_terminal,
                        direction=ev_dir,
                    )
                )

        t_events_tuple = tuple(t_ev_list)
        y_events_tuple = tuple(y_ev_list)
        event_names_tuple = tuple(names_list)
        triggered_records = tuple(records_list)

        if terminal_event_occurred:
            # 1. Determine actual terminal root parameter and state from SciPy's event records
            # When t_eval is supplied, sol.t contains only requested output samples (and may end
            # before the event or even be empty). The true terminal root is recorded in sol.t_events.
            terminal_recs = [
                rec for rec in triggered_records if rec.terminal and len(rec.lambdas) > 0
            ]
            if len(terminal_recs) > 0:
                if lambda_end >= lambda_start:
                    final_lambda = min(float(rec.lambdas[-1]) for rec in terminal_recs)
                else:
                    final_lambda = max(float(rec.lambdas[-1]) for rec in terminal_recs)

                # Scientific root-matching tolerance: SciPy sets sol.t[-1] directly from the event root,
                # so rec.lambdas[-1] == final_lambda in exact floating point. A safety margin of
                # 100 * eps_mach absorbs any potential precision variance.
                eps = np.finfo(np.float64).eps
                root_time_atol = 100.0 * eps * max(1.0, abs(final_lambda))

                # Initial-point termination check: does the terminal root coincide with lambda_start?
                is_initial_point = abs(final_lambda - float(lambda_start)) <= root_time_atol

                scipy_recorded_indices = []
                scipy_recorded_names = []
                inferred_indices = []
                unresolved_indices_list = []
                unresolved_names_list = []

                for rec in triggered_records:
                    if rec.terminal and len(rec.lambdas) > 0:
                        if abs(rec.lambdas[-1] - final_lambda) <= root_time_atol:
                            scipy_recorded_indices.append(rec.event_index)
                            scipy_recorded_names.append(rec.name)

                scipy_recorded_pairs = sorted(
                    zip(scipy_recorded_indices, scipy_recorded_names),
                    key=lambda p: p[0],
                )
                scipy_recorded_terminal_event_indices = tuple(p[0] for p in scipy_recorded_pairs)
                scipy_recorded_terminal_event_names = tuple(p[1] for p in scipy_recorded_pairs)

                matching_terminal_indices = list(scipy_recorded_indices)
                matching_terminal_names = list(scipy_recorded_names)

                # 2. Scale-independent coincidence detection for events truncated by SciPy.
                # When multiple terminal events have coincident roots, SciPy only records the first
                # in sol.t_events (due to its active_events[:t+1] slice). To avoid false unique
                # attribution, we independently compute roots in affine parameter space over the
                # final accepted integration step using the solver's dense interpolant.
                #
                # Interpolation domain and non-extrapolation guarantee:
                # Step bounds hierarchy:
                # 1. Primary: Continuous dense interpolant `sol.sol.interpolants[-1]`
                #    (a subclass of `scipy.integrate._ivp.base.DenseOutput`). Its valid domain is
                #    [interp.t_min, interp.t_max], accepted only when containing final_lambda within root_time_atol.
                # 2. Secondary: If interpolants is missing, use internal solver-step timestamps `sol.sol.ts[-2:]`
                #    only if they reliably define the final step containing final_lambda.
                # 3. Defensive cutoff: If neither source provides trustworthy final accepted-step bounds,
                #    coincidence recovery is NOT attempted. Output grid samples (lambdas) or whole-span
                #    intervals ([lambda_start, final_lambda]) are never substituted for step bounds.
                #    All omitted registered terminal events are conservatively marked as unresolved.
                if hasattr(sol, "sol") and sol.sol is not None and not is_initial_point:
                    dense_eval = None
                    step_bounds_available = False

                    # 1. Primary: Use final accepted-step interpolant and its bounds when available and valid
                    if (
                        hasattr(sol.sol, "interpolants")
                        and hasattr(sol.sol.interpolants, "__len__")
                        and len(sol.sol.interpolants) > 0
                    ):
                        interp = sol.sol.interpolants[-1]
                        if (
                            hasattr(interp, "t_min")
                            and hasattr(interp, "t_max")
                            and hasattr(interp, "t_old")
                            and hasattr(interp, "t")
                            and callable(interp)
                        ):
                            cand_min = float(interp.t_min)
                            cand_max = float(interp.t_max)
                            if cand_min - root_time_atol <= final_lambda <= cand_max + root_time_atol:
                                step_min = cand_min
                                step_max = cand_max
                                step_t_old = float(interp.t_old)
                                step_t_new = float(interp.t)
                                dense_eval = interp
                                step_bounds_available = True

                    # 2. Secondary: Use sol.sol.ts[-2:] only if those timestamps reliably describe
                    # the final accepted step and contain the actual terminal root.
                    if not step_bounds_available and callable(sol.sol):
                        if hasattr(sol.sol, "ts") and hasattr(sol.sol.ts, "__len__") and len(sol.sol.ts) >= 2:
                            try:
                                cand_t_old = float(sol.sol.ts[-2])
                                cand_t_new = float(sol.sol.ts[-1])
                                cand_min = min(cand_t_old, cand_t_new)
                                cand_max = max(cand_t_old, cand_t_new)
                                if cand_min - root_time_atol <= final_lambda <= cand_max + root_time_atol:
                                    step_t_old = cand_t_old
                                    step_t_new = cand_t_new
                                    step_min = cand_min
                                    step_max = cand_max
                                    dense_eval = sol.sol
                                    step_bounds_available = True
                            except Exception:
                                pass

                    if step_bounds_available:
                        h_step = step_max - step_min

                        for idx, ev in enumerate(event_list):
                            if idx in matching_terminal_indices:
                                continue
                            is_terminal = bool(getattr(ev, "terminal", False))
                            if not is_terminal:
                                continue

                            raw_name = getattr(ev, "name", None) or getattr(ev, "__name__", None)
                            ev_name = str(raw_name).strip() if raw_name else f"event_{idx}"

                            # Search for root coincident with final_lambda strictly within [step_min, step_max]
                            coincident_root_found = False
                            ev_dir = int(getattr(ev, "direction", 0))

                            # Candidate Bracket 1: Full accepted step [step_t_old, step_t_new]
                            # Exactly matches the bracket used by SciPy's solve_event_equation.
                            try:
                                val_old = float(ev(step_t_old, dense_eval(step_t_old)))
                                val_new = float(ev(step_t_new, dense_eval(step_t_new)))

                                # Along integration progression from step_t_old to step_t_new
                                if step_t_new > step_t_old:
                                    val_start_step, val_end_step = val_old, val_new
                                else:
                                    val_start_step, val_end_step = val_new, val_old

                                valid_step_bracket = False
                                if ev_dir == 1 and (val_start_step <= 0.0 and val_end_step >= 0.0):
                                    valid_step_bracket = True
                                elif ev_dir == -1 and (val_start_step >= 0.0 and val_end_step <= 0.0):
                                    valid_step_bracket = True
                                elif ev_dir == 0 and (
                                    (val_start_step <= 0.0 and val_end_step >= 0.0)
                                    or (val_start_step >= 0.0 and val_end_step <= 0.0)
                                ):
                                    valid_step_bracket = True

                                if valid_step_bracket:
                                    root_val = brentq(
                                        lambda t: ev(t, dense_eval(t)),
                                        step_min,
                                        step_max,
                                        xtol=4 * eps,
                                        rtol=4 * eps,
                                    )
                                    if abs(root_val - final_lambda) <= root_time_atol:
                                        coincident_root_found = True
                            except Exception:
                                pass

                            # Candidate Bracket 2: Local bracket around final_lambda strictly within [step_min, step_max]
                            # Resolves multiple-root / non-monotonic events where endpoint signs over the full step
                            # may be identical despite a zero crossing at final_lambda.
                            if not coincident_root_found and h_step > 0.0:
                                try:
                                    delta_local = 0.1 * h_step
                                    t_loc_a = max(step_min, final_lambda - delta_local)
                                    t_loc_b = min(step_max, final_lambda + delta_local)

                                    if t_loc_b > t_loc_a:
                                        val_a = float(ev(t_loc_a, dense_eval(t_loc_a)))
                                        val_b = float(ev(t_loc_b, dense_eval(t_loc_b)))

                                        # Along integration progression from step_t_old to step_t_new
                                        if step_t_new > step_t_old:
                                            val_start_loc, val_end_loc = val_a, val_b
                                        else:
                                            val_start_loc, val_end_loc = val_b, val_a

                                        valid_local_bracket = False
                                        if ev_dir == 1 and (val_start_loc <= 0.0 and val_end_loc >= 0.0):
                                            valid_local_bracket = True
                                        elif ev_dir == -1 and (val_start_loc >= 0.0 and val_end_loc <= 0.0):
                                            valid_local_bracket = True
                                        elif ev_dir == 0 and (
                                            (val_start_loc <= 0.0 and val_end_loc >= 0.0)
                                            or (val_start_loc >= 0.0 and val_end_loc <= 0.0)
                                        ):
                                            valid_local_bracket = True

                                        if valid_local_bracket:
                                            root_val_loc = brentq(
                                                lambda t: ev(t, dense_eval(t)),
                                                t_loc_a,
                                                t_loc_b,
                                                xtol=4 * eps,
                                                rtol=4 * eps,
                                            )
                                            if abs(root_val_loc - final_lambda) <= root_time_atol:
                                                coincident_root_found = True
                                except Exception:
                                    pass

                            if coincident_root_found:
                                matching_terminal_indices.append(idx)
                                inferred_indices.append(idx)
                                matching_terminal_names.append(ev_name)
                            else:
                                # Any omitted registered terminal event that is not numerically identified
                                # as coincident within root_time_atol cannot be certified as non-coincident
                                # on a rigorous, scale-invariant mathematical basis without ungrounded heuristics.
                                # It is therefore conservatively recorded as unresolved.
                                unresolved_indices_list.append(idx)
                                unresolved_names_list.append(ev_name)
                    else:
                        # Dense output exists but lacks trustworthy final accepted-step bounds.
                        # Do not fall back to output grid samples or whole-span intervals;
                        # conservatively mark all omitted registered terminal events as unresolved.
                        for idx, ev in enumerate(event_list):
                            if idx in matching_terminal_indices:
                                continue
                            is_terminal = bool(getattr(ev, "terminal", False))
                            if not is_terminal:
                                continue
                            raw_name = getattr(ev, "name", None) or getattr(ev, "__name__", None)
                            ev_name = str(raw_name).strip() if raw_name else f"event_{idx}"
                            unresolved_indices_list.append(idx)
                            unresolved_names_list.append(ev_name)
                elif is_initial_point:
                    # Initial-point root case (terminal event coincided with lambda_start)
                    t_init = float(lambda_start)
                    for idx, ev in enumerate(event_list):
                        if idx in matching_terminal_indices:
                            continue
                        is_terminal = bool(getattr(ev, "terminal", False))
                        if not is_terminal:
                            continue
                        raw_name = getattr(ev, "name", None) or getattr(ev, "__name__", None)
                        ev_name = str(raw_name).strip() if raw_name else f"event_{idx}"
                        try:
                            val_init = float(ev(t_init, y0))
                            if val_init == 0.0:
                                matching_terminal_indices.append(idx)
                                inferred_indices.append(idx)
                                matching_terminal_names.append(ev_name)
                            else:
                                unresolved_indices_list.append(idx)
                                unresolved_names_list.append(ev_name)
                        except Exception:
                            unresolved_indices_list.append(idx)
                            unresolved_names_list.append(ev_name)
                else:
                    # Multi-step integration where dense output is unavailable (sol.sol is None or missing).
                    # Continuous root finding over the final accepted step cannot be performed;
                    # all omitted registered terminal events must be conservatively marked as unresolved.
                    for idx, ev in enumerate(event_list):
                        if idx in matching_terminal_indices:
                            continue
                        is_terminal = bool(getattr(ev, "terminal", False))
                        if not is_terminal:
                            continue
                        raw_name = getattr(ev, "name", None) or getattr(ev, "__name__", None)
                        ev_name = str(raw_name).strip() if raw_name else f"event_{idx}"
                        unresolved_indices_list.append(idx)
                        unresolved_names_list.append(ev_name)
            else:
                # Defensive handling for inconsistent solver output:
                # sol.status == 1 was reported, but no terminal event recorded roots in sol.t_events.
                # Do NOT fabricate or infer a terminal root parameter from output grid samples (lambdas[-1])
                # or from lambda_start. Do not attempt coincidence recovery.
                # Conservatively mark all registered terminal candidates as unresolved.
                scipy_recorded_terminal_event_indices = ()
                scipy_recorded_terminal_event_names = ()
                matching_terminal_indices = []
                matching_terminal_names = []
                inferred_indices = []
                unresolved_indices_list = []
                unresolved_names_list = []

                for idx, ev in enumerate(event_list):
                    is_terminal = bool(getattr(ev, "terminal", False))
                    if not is_terminal:
                        continue
                    raw_name = getattr(ev, "name", None) or getattr(ev, "__name__", None)
                    ev_name = str(raw_name).strip() if raw_name else f"event_{idx}"
                    unresolved_indices_list.append(idx)
                    unresolved_names_list.append(ev_name)

            # Sort coincident terminal indices and names
            sorted_pairs = sorted(
                zip(matching_terminal_indices, matching_terminal_names),
                key=lambda p: p[0],
            )
            terminal_event_indices = tuple(p[0] for p in sorted_pairs)
            terminal_event_names = tuple(p[1] for p in sorted_pairs)
            inferred_coincident_terminal_indices = tuple(sorted(inferred_indices))
            unresolved_terminal_indices = tuple(sorted(unresolved_indices_list))
            unresolved_terminal_names = tuple(unresolved_names_list)

            # Completeness determination:
            # Completeness is True if and only if no registered terminal event remains unresolved
            # under the documented numerical identification policy, AND if termination occurred,
            # at least one terminal event was actually identified.
            if terminal_event_occurred and len(terminal_event_indices) == 0:
                terminal_event_identity_complete = False
            else:
                terminal_event_identity_complete = (len(unresolved_terminal_indices) == 0)

            # Conservative identity assignment:
            # A unique terminal identity is reported if and only if completeness is True under the
            # numerical policy and exactly one terminal event occurred.
            if terminal_event_identity_complete and len(terminal_event_indices) == 1:
                terminal_event_index = terminal_event_indices[0]
                terminal_event_name = terminal_event_names[0]
            else:
                terminal_event_index = None
                terminal_event_name = None

    return GeodesicIntegrationResult(
        lambdas=lambdas,
        states=states,
        success=bool(sol.success),
        status=int(sol.status),
        message=str(sol.message),
        nfev=int(sol.nfev),
        method=method,
        rtol=rtol,
        atol=atol,
        raw_solution=sol,
        t_events=t_events_tuple,
        y_events=y_events_tuple,
        event_names=event_names_tuple,
        triggered_events=triggered_records,
        terminal_event_occurred=terminal_event_occurred,
        terminal_event_name=terminal_event_name,
        terminal_event_index=terminal_event_index,
        terminal_event_indices=terminal_event_indices,
        terminal_event_names=terminal_event_names,
        scipy_recorded_terminal_event_indices=scipy_recorded_terminal_event_indices,
        scipy_recorded_terminal_event_names=scipy_recorded_terminal_event_names,
        inferred_coincident_terminal_indices=inferred_coincident_terminal_indices,
        terminal_event_identity_complete=terminal_event_identity_complete,
        unresolved_terminal_indices=unresolved_terminal_indices,
        unresolved_terminal_names=unresolved_terminal_names,
    )
