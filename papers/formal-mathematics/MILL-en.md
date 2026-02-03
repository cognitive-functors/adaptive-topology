This document presents the semantics of Multiplicative Intuitionistic Linear Logic (MILL) in the context of distributed processes with true concurrency.

## Main Idea

In the semantics of distributed processes, linear logic types are interpreted as **interaction protocols** between processes, and proofs are interpreted as **processes** that implement these protocols.

## Tensor Product (tensor)

The type `A tensor B` represents the **parallel composition** of two independent protocols:

- **Semantically**: A process of type `A tensor B` consists of two subprocesses executing in parallel -- one implementing protocol `A`, the other implementing protocol `B`
- **Operationally**: `P : A tensor B` means `P = P_1 | P_2`, where `P_1 : A` and `P_2 : B`, and `|` denotes parallel composition
- **Key property**: The resources `A` and `B` exist **simultaneously** and can be used **independently**

### Rules for tensor:

```
Gamma |- P : A    Delta |- Q : B
--------------------------------- (tensor-intro)
Gamma, Delta |- P | Q : A tensor B

Gamma, x:A, y:B |- P : C    Delta |- Q : A tensor B
----------------------------------------------------- (tensor-elim)
Gamma, Delta |- let x tensor y = Q in P : C
```

In the process interpretation:
- `P | Q` is the parallel composition of processes
- `let x tensor y = Q in P` is a process that waits until `Q` produces a pair of values, then binds them to `x` and `y` and continues as `P`

## Linear Implication (lollipop)

The type `A lollipop B` represents a **functional dependency** with resource consumption:

- **Semantically**: A process of type `A lollipop B` is a process that **waits** for an incoming message of type `A`, **consumes** it, and then behaves as a process of type `B`
- **Operationally**: This is realized through a channel or port mechanism
- **Key property**: The resource `A` is **consumed** exactly once to produce `B`

### Rules for lollipop:

```
Gamma, x:A |- P : B
--------------------- (lollipop-intro)
Gamma |- lambda x.P : A lollipop B

Gamma |- P : A lollipop B    Delta |- Q : A
--------------------------------------------- (lollipop-elim)
Gamma, Delta |- P Q : B
```

In the process interpretation:
- `lambda x.P` is a process awaiting an incoming message on channel `x`
- `P Q` is application: process `Q` sends a message to process `P`

## Example: Client-Server Protocol

Consider a simple protocol:
```
Request tensor (Response lollipop Done)
```

This means:
1. The client sends a request (`Request`)
2. **In parallel** with this, a channel for the response is created
3. The server must send a response (`Response`) over this channel
4. After the response is received, the protocol terminates (`Done`)

## Key Differences from Sequential Semantics

In true concurrency:

1. **Causal independence**: In `A tensor B`, the processes for `A` and `B` are causally independent and may execute on different network nodes

2. **Asynchrony**: The composition `P | Q` does not require synchronization between `P` and `Q`; they interact only through explicit channels

3. **Locality**: Each process has access only to its local resources; there is no global state

4. **Linearity as channel uniqueness**: Each channel is used exactly once for sending and exactly once for receiving

## Connection with the pi-calculus

This semantics is closely related to the typed pi-calculus:
- Types = session protocols
- tensor = parallel composition with independent channels
- lollipop = input/output prefix with continuation
- Linearity = each channel is used exactly once

This ensures strict guarantees of deadlock freedom and protocol correctness in distributed systems.


Can one say that a variable of type A is a channel of type A?
And that a type is a specification of a channel?
This is a key observation for understanding the process semantics of linear logic.

## Variables as Channels

In the process interpretation:
- **Variable `x : A`** = **channel `x` over which messages are transmitted according to protocol `A`**
- **Type `A`** = **specification of the interaction protocol over the channel**

## Duality in Communication

An important point: channels have **two ends** with dual types:
- If one end has type `A`, the other end has type `A^perp` (the dual type)
- For example:
  - The sender sees the channel as `A` (can send `A`)
  - The receiver sees the same channel as `A^perp` (can receive `A`)

## Interpretation Examples

### 1. Base types
```
x : Int
```
- `x` is a channel over which an integer may be transmitted
- Protocol: a single transmission of a value of type `Int`

### 2. Tensor product
```
x : A tensor B
```
- `x` is a channel over which a pair of channels `(a, b)` is transmitted
- `a` has protocol `A`, `b` has protocol `B`
- Both subchannels may be used in parallel

### 3. Linear function
```
f : A lollipop B
```
- `f` is a channel that first accepts a channel of type `A`, then behaves as a channel of type `B`
- This is a **higher-order channel** -- a channel for transmitting channels

## Typing Rules as Channel Usage Rules

### Rule for variables:
```
---------- (Ax)
x:A |- x:A
```
Interpretation: "If we have a channel `x` with protocol `A`, we can use it according to protocol `A`"

### Rule for lollipop-elimination:
```
Gamma |- P : A lollipop B    Delta |- Q : A
---------------------------------------------
Gamma, Delta |- P Q : B
```
Interpretation:
- `P` is a process owning a channel that awaits a channel of type `A` and then behaves as `B`
- `Q` is a process owning a channel of type `A`
- `P Q` is the transfer of a channel from `Q` to `P`

## Linearity = Unique Channel Ownership

Linearity in this interpretation means:
- Each channel has **exactly one owner** at any given moment
- A channel may be **transferred** to another process (transfer of ownership)
- After transfer, the previous owner **cannot** use the channel any longer

## Example: Session Types

```
Protocol = Request lollipop (Response tensor Protocol)
```

This is a recursive protocol:
1. The server awaits a request on the channel
2. It responds by creating two channels:
   - One for the response (`Response`)
   - Another for continuing the dialogue (`Protocol`)

In code:
```
server : Protocol
server = lambda req.
  let result = process(req) in
  (result, server) -- return the response and a new channel for the next request
```

## Compositionality

Types as channel specifications ensure:
- **Safety**: It is impossible to send a message of the wrong type
- **Liveness**: If the protocol requires a response, it will be received
- **Compositionality**: Complex protocols are built from simple ones

This interpretation makes linear logic a powerful tool for the design and verification of distributed systems.
