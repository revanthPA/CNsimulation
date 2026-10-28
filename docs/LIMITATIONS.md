# Limitations and Assumptions

## Model Limitations

### 1. Network Model
- **Static topology**: Nodes never move; positions fixed at initialization
- **Single base station**: One sink at fixed position; no multi-sink or mobile sink support
- **Homogeneous nodes**: All sensor nodes have identical hardware, initial energy, and capabilities
- **No node failure modes**: Only energy depletion causes node death; no hardware failures

### 2. Traffic Model
- **Constant rate**: Exactly `packets_per_round` packets per node per round
- **No event-driven traffic**: No bursty or event-triggered data generation
- **No prioritization**: All packets treated equally
- **No data aggregation**: Each packet routed independently; no in-network processing

### 3. Communication Model
- **Ideal MAC layer**: No collisions, no retransmissions, no backoff
- **Perfect links**: No packet loss due to channel errors (only energy-related loss)
- **Symmetric links**: If A can reach B, B can reach A (same communication range)
- **No interference**: Simultaneous transmissions don't affect each other
- **No propagation delay**: Instantaneous transmission

### 4. Energy Model
- **First-order radio model**: Simplified TX/RX energy (no sleep, idle, or startup costs)
- **No battery effects**: Linear discharge; no recovery, leakage, or temperature effects
- **Infinite base station energy**: Base station never depletes
- **No energy harvesting**: No solar, vibration, or other energy sources
- **Constant packet size**: All packets identical size

### 5. Routing Model
- **Global topology knowledge**: Routing algorithms have full network view
- **Instant route computation**: No routing protocol overhead or convergence time
- **Static routes per packet**: Route computed once per packet; no adaptive re-routing mid-path
- **No routing loops**: Dijkstra guarantees loop-free paths

### 6. Simulation Model
- **Discrete rounds**: Time divided into synchronous rounds
- **Deterministic execution**: Same seed always produces identical results
- **No real-time constraints**: Simulation runs as fast as possible
- **No clock drift**: Perfect synchronization across nodes

## Simplifications vs. Real WSNs

| Aspect | Simulator | Real WSN |
|--------|-----------|----------|
| Node mobility | Static | Mobile/Random |
| MAC layer | Ideal (no collisions) | CSMA/CA, TDMA, collisions |
| Channel | Perfect, symmetric | Fading, asymmetric, interference |
| Battery | Linear, ideal | Non-linear, temperature-sensitive |
| Traffic | Constant rate | Event-driven, bursty |
| Routing | Centralized, global view | Distributed, local info |
| Base station | Single, infinite energy | Multiple, finite energy |
| Data aggregation | None | Often used |
| Time | Discrete rounds | Continuous/asynchronous |

## Impact on Results

### Energy-Aware Routing May Appear Better Because:
1. No MAC overhead penalizes longer paths in shortest-path
2. No interference means multi-hop doesn't suffer from contention
3. Perfect links mean no retransmission energy waste
4. Global knowledge gives energy-aware unfair advantage

### Shortest-Path May Appear Better Because:
1. No route discovery overhead
2. No stale routing information
3. No control packet energy cost

### Generalizability Concerns:
- Results specific to simulated conditions
- Real-world performance may differ significantly
- Sensitivity coverage is limited. Earlier α/β sweep outputs are invalidated
  by an algorithm-selection bug and should be regenerated.

## Known Issues

### 1. Energy Accounting Edge Cases
- Base station infinite energy handled explicitly (no inf/inf)
- Dead nodes excluded from alive subgraph (not removed from topology)
- Case 2 (dead receiver) consumes TX but not RX - may create "energy black holes"

### 2. Metric Definitions
- FND/HND/LND based on sensor nodes only (excludes base station)
- HND uses floor(N/2) - for odd N, HND triggers when alive ≤ floor(N/2)
- If event never occurs, returns None (not 0 or max_rounds)

### 3. Visualization Limitations
- Matplotlib backend must be set to 'Agg' for headless environments
- Large networks (200+ nodes) may produce cluttered plots
- Dashboard visualizations are interactive; exported experiment plots are
  static PNG files.

### 4. Performance
- Simulation scales as O(nodes × rounds × packets)
- 200 nodes × 1000 rounds × 1 packet ≈ few seconds
- Memory usage grows with round metrics storage

## Future Improvements (Out of Scope)

1. **MAC layer simulation**: Add CSMA/CA, duty cycling
2. **Mobility support**: Random waypoint, Gauss-Markov models
3. **Heterogeneous nodes**: Different energy, capabilities, roles
4. **Data aggregation**: In-network processing, clustering
5. **Adaptive routing**: AODV, DSR, or other on-demand protocols
6. **Energy harvesting**: Solar, RF, vibration models
7. **Multi-sink**: Multiple base stations, anycast routing
8. **QoS metrics**: Latency, jitter, reliability
9. **Security**: Attacks, encryption energy overhead
10. **3D deployment**: Elevation, underground/underwater

## Validation Status

All implemented algorithms and models validated against:
- Worked examples from literature (energy model)
- Unit tests for each component (178 tests passing)
- Determinism checks (same seed → same results)
- Energy accounting verification (3 cases)

See `tests/` directory for complete test coverage.
