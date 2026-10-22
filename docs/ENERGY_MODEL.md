# Energy Model Documentation

## First-Order Radio Model

This simulator implements the standard first-order radio energy model for Wireless Sensor Networks.

## Energy Consumption Formulas

### Transmission Energy

```
E_tx(k, d) = k · E_elec + k · E_amp · d²
```

- `k`: Number of bits (packet_size × 8)
- `E_elec`: Energy per bit for transmitter/receiver electronics (nJ/bit)
- `E_amp`: Energy per bit for transmit amplifier (nJ/bit/m²)
- `d`: Transmission distance (meters)

### Reception Energy

```
E_rx(k) = k · E_elec
```

- Distance-independent
- Only electronics energy

### Total Hop Energy

For a successful hop (both TX and RX):
```
E_hop = E_tx + E_rx = 2 · k · E_elec + k · E_amp · d²
```

## Units

- All energy parameters in **nanojoules (nJ)**
- Distances in **meters (m)**
- Final results converted to **joules (J)** by dividing by 1e9

## Configuration Parameters

```yaml
energy:
  initial_energy: 1.0      # Joules per sensor node
  E_elec: 50.0             # nJ/bit
  E_amp: 0.0013            # nJ/bit/m²
  packet_size: 512         # bytes
```

## Worked Example

Given:
- `E_elec = 50 nJ/bit`
- `E_amp = 0.0013 nJ/bit/m²`
- `packet_size = 512 bytes = 4096 bits`
- `distance = 10 m`

**Transmission Cost**:
```
E_tx = 4096 × 50 + 4096 × 0.0013 × 10²
     = 204,800 + 532.48
     = 205,332.48 nJ
     = 0.00020533248 J
```

**Reception Cost**:
```
E_rx = 4096 × 50 = 204,800 nJ = 0.0002048 J
```

**Total Hop Cost** (TX + RX):
```
E_hop = 205,332.48 + 204,800 = 410,132.48 nJ = 0.00041013248 J
```

**Node Lifetime Estimate**:
With initial energy = 1.0 J:
```
Packets per node at 10m = 1.0 / 0.00041013248 ≈ 2,438 packets
```

## Base Station Energy

- Base station has **infinite energy** (`float('inf')`)
- Never dies, never consumes energy
- Always available for reception
- Normalized energy = 1.0 for routing calculations

## Failed-Hop Energy Accounting

The simulator implements **exactly three cases** for energy consumption:

### Case 1: Failed Before Transmission
- Transmitter dead OR insufficient energy for TX
- **TX Energy**: NOT consumed
- **RX Energy**: NOT consumed
- **Result**: Packet LOST

### Case 2: Successful TX, Dead Receiver
- Transmitter has energy, transmits successfully
- Receiver is dead (is_alive = False)
- **TX Energy**: CONSUMED
- **RX Energy**: NOT consumed
- **Result**: Packet LOST

### Case 3: Successful TX, Successful RX
- Both transmitter and receiver alive with sufficient energy
- **TX Energy**: CONSUMED
- **RX Energy**: CONSUMED
- **Result**: Packet DELIVERED or continues to next hop

## Implementation

### EnergyModel Class (`energy_routing/simulation/energy_model.py`)

```python
class EnergyModel:
    def __init__(self, config: EnergyConfig):
        self.config = config
    
    def _bits(self) -> int:
        return self.config.packet_size * 8
    
    def transmit_cost(self, distance: float) -> float:
        k = self._bits()
        e_tx_nj = k * (self.config.E_elec + self.config.E_amp * distance ** 2)
        return e_tx_nj / 1e9  # nJ → J
    
    def receive_cost(self) -> float:
        k = self._bits()
        e_rx_nj = k * self.config.E_elec
        return e_rx_nj / 1e9  # nJ → J
```

### Node Energy Consumption (`energy_routing/models/node.py`)

```python
class Node:
    def consume_energy(self, amount: float) -> bool:
        if not self.is_alive:
            return False
        self.remaining_energy -= amount
        if self.remaining_energy <= 0:
            self.is_alive = False
            self.remaining_energy = 0.0
            return True  # Node died
        return False
    
    def can_transmit(self, energy_cost: float) -> bool:
        return self.is_alive and self.remaining_energy >= energy_cost
```

## Validation

All energy calculations are validated against the worked example in tests:
- `tests/test_simulation/test_energy_model.py::TestEnergyModelWorkedExample::test_plan_worked_example`

## Assumptions

1. **Ideal channel**: No retransmissions, no interference
2. **Constant packet size**: All packets same size
3. **No idle listening**: Energy only for TX/RX
4. **No sleep mode**: Nodes always ready to receive
5. **Perfect synchronization**: No clock drift energy cost
6. **Static topology**: Node positions fixed, only energy changes