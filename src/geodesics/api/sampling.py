"""Trajectory decimation and sampling algorithm for Kerr Geodesics Lab.

Enforces a strict upper bound of 500 trajectory points while unconditionally
preserving initial conditions, terminal states, and exact event trigger locations.
"""

from typing import List, Optional, Sequence, Tuple

import numpy as np

from geodesics.integrator import EventTriggerRecord


def decimate_trajectory(
    lambdas: np.ndarray,
    states: np.ndarray,
    triggered_events: Optional[Sequence[EventTriggerRecord]] = None,
    max_points: int = 500,
) -> Tuple[np.ndarray, np.ndarray]:
    """Decimates an integration trajectory to at most `max_points` points.

    Sampling Policy
    ---------------
    1. Mandatory Preservation:
       - Initial state y(lambda_0) at index 0.
       - Terminal state y(lambda_final) at index -1.
       - Exact event trigger roots (lambda_ev, y_ev) recorded in `triggered_events`.
    2. Event Root Precedence:
       - The integration engine's Brent root-solver calculates high-precision event
         states that may fall between solver time steps. These exact event roots are
         injected into the trajectory with higher priority than nearby solver steps.
    3. Mandatory Point Overflow Policy:
       - If the total number of mandatory points (2 endpoints + N_events) exceeds
         `max_points`, initial and final endpoints are strictly preserved, and event
         points are downsampled deterministically via uniform index spacing to fill
         the remaining (max_points - 2) slots.
    4. Intermediate Point Allocation:
       - When mandatory points are fewer than `max_points`, intermediate accepted solver
         steps from (lambdas, states) are selected using uniform index spacing across
         the interior steps to fill the remaining budget.
    5. Deduplication and Monotonicity:
       - All points are sorted by affine parameter lambda.
       - Points with |lambda_i - lambda_j| <= 1e-12 are deduplicated, giving precedence
         to exact event roots over regular ODE steps, and ensuring strict monotonicity
         lambda_0 < lambda_1 < ... < lambda_{N-1} while guaranteeing the final point
         is preserved.
    6. Safety Cap:
       - The output length is strictly verified to be <= `max_points`.

    Parameters
    ----------
    lambdas : np.ndarray
        1D array of shape (N,) containing raw affine parameter values.
    states : np.ndarray
        2D array of shape (N, 8) containing raw phase-space states.
    triggered_events : Optional[Sequence[EventTriggerRecord]]
        Event records from `GeodesicIntegrationResult.triggered_events`.
    max_points : int, default 500
        Maximum allowed number of returned trajectory samples.

    Returns
    -------
    Tuple[np.ndarray, np.ndarray]
        (decimated_lambdas, decimated_states) where len(decimated_lambdas) <= max_points.
    """
    if len(lambdas) == 0:
        return np.empty(0, dtype=np.float64), np.empty((0, 8), dtype=np.float64)

    if len(lambdas) == 1:
        return np.asarray(lambdas[:1], dtype=np.float64), np.asarray(states[:1], dtype=np.float64)

    # 1. Collect all event roots as mandatory points
    event_lambdas: List[float] = []
    event_states: List[np.ndarray] = []
    if triggered_events:
        for rec in triggered_events:
            for l_val, s_val in zip(rec.lambdas, rec.states):
                event_lambdas.append(float(l_val))
                event_states.append(np.asarray(s_val, dtype=np.float64))

    n_events = len(event_lambdas)
    mandatory_limit = max_points - 2  # slots reserved for endpoints

    # 2. Check for event overflow
    if n_events > mandatory_limit:
        # Downsample events deterministically
        selected_event_indices = np.round(
            np.linspace(0, n_events - 1, mandatory_limit)
        ).astype(int)
        sampled_event_lambdas = [event_lambdas[i] for i in selected_event_indices]
        sampled_event_states = [event_states[i] for i in selected_event_indices]

        cand_l_list = [np.array([lambdas[0]]), np.array(sampled_event_lambdas), np.array([lambdas[-1]])]
        cand_s_list = [states[0:1], np.array(sampled_event_states), states[-1:]]
        flags_list = [np.array([False]), np.array([True] * len(sampled_event_lambdas)), np.array([False])]

        cand_lambdas = np.concatenate(cand_l_list)
        cand_states = np.vstack(cand_s_list)
        is_event_flag = np.concatenate(flags_list)
    else:
        # All events fit
        rem_budget = max_points - (2 + n_events)
        n_interior = len(lambdas) - 2

        cand_l_list = [np.array([lambdas[0]])]
        cand_s_list = [states[0:1]]
        flags_list = [np.array([False])]

        if n_events > 0:
            cand_l_list.append(np.array(event_lambdas))
            cand_s_list.append(np.array(event_states))
            flags_list.append(np.array([True] * n_events))

        if rem_budget > 0 and n_interior > 0:
            interior_take = min(rem_budget, n_interior)
            # Uniform interior index selection
            interior_indices = np.round(
                np.linspace(1, len(lambdas) - 2, interior_take)
            ).astype(int)
            interior_indices = np.unique(interior_indices)

            cand_l_list.append(lambdas[interior_indices])
            cand_s_list.append(states[interior_indices])
            flags_list.append(np.array([False] * len(interior_indices)))

        cand_l_list.append(np.array([lambdas[-1]]))
        cand_s_list.append(states[-1:])
        flags_list.append(np.array([False]))

        cand_lambdas = np.concatenate(cand_l_list)
        cand_states = np.vstack(cand_s_list)
        is_event_flag = np.concatenate(flags_list)

    # 3. Sort by lambda
    sort_idx = np.argsort(cand_lambdas, kind="mergesort")
    cand_lambdas = cand_lambdas[sort_idx]
    cand_states = cand_states[sort_idx]
    is_event_flag = is_event_flag[sort_idx]

    # 4. Strict deduplication with event precedence
    tol = 1e-12
    out_lambdas: List[float] = [float(cand_lambdas[0])]
    out_states: List[np.ndarray] = [cand_states[0]]

    for i in range(1, len(cand_lambdas)):
        lam = float(cand_lambdas[i])
        st = cand_states[i]
        is_ev = is_event_flag[i]

        if lam - out_lambdas[-1] > tol:
            out_lambdas.append(lam)
            out_states.append(st)
        else:
            # Duplicate / near-duplicate. If this is an exact event, give it precedence.
            if is_ev:
                out_lambdas[-1] = lam
                out_states[-1] = st

    # Guarantee terminal point is preserved exactly as last element
    final_raw_lam = float(lambdas[-1])
    if abs(out_lambdas[-1] - final_raw_lam) > tol:
        out_lambdas.append(final_raw_lam)
        out_states.append(states[-1])
    else:
        out_lambdas[-1] = final_raw_lam
        out_states[-1] = states[-1]

    # 5. Safety cap if deduplication left > max_points
    if len(out_lambdas) > max_points:
        cap_indices = np.round(np.linspace(0, len(out_lambdas) - 1, max_points)).astype(int)
        cap_indices[0] = 0
        cap_indices[-1] = len(out_lambdas) - 1
        cap_indices = np.unique(cap_indices)
        out_lambdas = [out_lambdas[i] for i in cap_indices]
        out_states = [out_states[i] for i in cap_indices]

    return np.asarray(out_lambdas, dtype=np.float64), np.asarray(out_states, dtype=np.float64)
