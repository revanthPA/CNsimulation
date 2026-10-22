# Algorithm Documentation

## Routing Algorithms

### Shortest-Path Routing (Dijkstra)

**Algorithm**: Standard Dijkstra's shortest path algorithm using Euclidean distance as edge weights.

**Implementation**: `energy_routing/routing/shortest_path.py`

**Path Cost**: Sum of Euclidean distances between consecutive nodes
```
cost(path) = Σ distance(node_i, node_{i+1})
```

**Characteristics**:
- Minimizes total transmission distance
- Ignores node energy levels
- May create energy holes (nodes near base station deplete faster)

### Energy-Aware Routing

**Algorithm**: Modified Dijkstra with composite edge cost function.

**Implementation**: `energy_routing/routing/energy_aware.py`

**Edge Cost Function**:
```
cost(u, v) = α · (distance(u, v) / max_distance) + β · (1 - normalized_energy(v))
```

Where:
- `α` (alpha): Distance weight (0 ≤ α ≤ 1)
- `β` (beta): Energy weight (0 ≤ β ≤ 1), α + β = 1
- `distance(u, v)`: Euclidean distance between nodes
- `max_distance`: Maximum communication range (normalization)
- `normalized_energy(v)`: remaining_energy(v) / initial_energy(v) for node v
  - Base station: normalized_energy = 1.0 (infinite energy)
  - Dead nodes: excluded from graph (not in alive subgraph)

**Weight Interpretation**:
- Higher α → more distance-sensitive (closer to shortest path)
- Higher β → more energy-sensitive (prefers nodes with higher residual energy)
- α = 1.0, β = 0.0 → Pure shortest path
- α = 0.0, β = 1.0 → Pure energy-aware (maximize residual energy)

**Component Bounds**:
- Distance component: `distance / max_distance` ∈ [0, 1]
- Energy component: `1 - normalized_energy` ∈ [0, 1]
- Total edge cost: ∈ [0, 1] when α + β = 1

**Base Station Handling**: Explicitly returns normalized_energy = 1.0,
giving energy component 0.0 (base station always preferred as receiver).

## Energy Model

### First-Order Radio Model

**Implementation**: `energy_routing/simulation/energy_model.py`

**Transmission Energy**:
```
E_tx(k, d) = k · E_elec + k · E_amp · d²
```

**Reception Energy**:
```
E_rx(k) = k · E_elec
```

Where:
- `k` = packet_size × 8 (bits)
- `E_elec` = Electronics energy (nJ/bit)
- `E_amp` = Amplifier energy (nJ/bit/m²)
- `d` = Distance (meters)
- Result converted from nJ to Joules (÷ 1e9)

**Worked Example** (from plan):
- E_elec = 50 nJ/bit
- E_amp = 0.0013 nJ/bit/m²
- packet_size = 512 bytes = 4096 bits
- distance = 10 m

```
E_tx = 4096 × 50 + 4096 × 0.0013 × 10²
     = 204,800 + 532.48
     = 205,332.48 nJ = 0.00020533248 J

E_rx = 4096 × 50 = 204,800 nJ = 0.0002048 J

Total per hop = 0.00041013248 J
```

## Failed-Hop Energy Accounting (CRITICAL)

The simulator implements **exactly three cases** for energy consumption per hop:

| Case | Condition | TX Energy | RX Energy | Packet Status |
|------|-----------|-----------|-----------|---------------|
| 1 | Failed before TX (transmitter dead or insufficient energy) | ❌ NO | ❌ NO | LOST |
| 2 | Successful TX + dead receiver | ✅ YES | ❌ NO | LOST |
| 3 | Successful TX + successful RX | ✅ YES | ✅ YES | DELIVERED/continues |

**Implementation** (`simulator.py:_deliver_hop`):
```python
def _deliver_hop(self, current, next_hop, distance):
    tx_cost = energy_model.transmit_cost(distance)
    
    # CASE 1: Failed before TX
    if not nodes[current].can_transmit(tx_cost):
        return False  # NO TX, NO RX
    
    # CASE 2 & 3: TX energy consumed
    nodes[current].consume_energy(tx_cost)
    
    # CASE 2: Dead receiver
    if not nodes[next_hop].is_alive:
        return False  # TX consumed, RX NOT consumed
    
    # CASE 3: Successful RX
    rx_cost = energy_model.receive_cost()
    nodes[next_hop].consume_energy(rx_cost)
    return True  # Both consumed
```

## Simulation Loop

**Implementation**: `energy_routing/simulation/simulator.py`

**Per Round**:
1. For each alive sensor node:
   - Generate `packets_per_round` packets
   - Route each packet to base station:
     - Find path using routing strategy on alive subgraph
     - For each hop: attempt delivery with 3-case energy accounting
     - If any hop fails: packet LOST
     - If all hops succeed: packet DELIVERED
2. Collect round metrics (alive nodes, energy, packets)
3. Check termination conditions (all nodes dead)

**Termination**:
- Maximum rounds reached, OR
- All sensor nodes dead (LND reached)

## Metrics Calculation

### Network Lifetime Metrics

- **FND** (First Node Death): First round where ≥1 sensor node dead
- **HND** (Half Node Death): First round where alive nodes ≤ floor(N/2)
- **LND** (Last Node Death): First round where all sensor nodes dead

### Packet Metrics

- **PDR** (Packet Delivery Ratio): delivered / generated
- **Avg Hop Count**: Mean hops per delivered packet
- **Total Route Distance**: Sum of Euclidean distances for all delivered packets

### Energy Metrics

- Total remaining energy (all sensor nodes)
- Total energy consumed (all sensor nodes)
- Per-node energy tracking

## Experiment Methodology

### Routing Comparison (Main Experiment)

- **Algorithms**: Shortest Path vs Energy-Aware (α=0.5, β=0.5)
- **Seeds**: 5 seeds (42, 43, 44, 45, 46)
- **Fair Comparison**: Same seed → same topology → different routing
- **Statistical Significance**: Mean ± std across seeds

### Network Size Experiment

- **Node Counts**: 20, 50, 100, 200
- **Seed**: Same seed (42) for all sizes
- **Topology**: Different for each size (as per plan)
- **Purpose**: Scaling behavior analysis

### Parameter Sweep Experiments

- **Energy-Aware Params**: α ∈ {0.0, 0.25, 0.5, 0.75, 1.0} with complementary β
- **Communication Range**: 15, 20, 25, 30 meters
- **Initial Energy**: 0.5, 1.0, 2.0, 5.0 Joules
- **Seeds**: 3 per parameter combination