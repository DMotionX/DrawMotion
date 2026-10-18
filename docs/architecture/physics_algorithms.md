# Physics Algorithms in the Writing Engine

The Writing Engine of DrawMotion uses various physics-based algorithms to simulate the process of drawing paths and writing text. These algorithms determine how the length of a stroke (`strokeDashoffset`) changes over time (`t`), giving the animation a specific visual character.

## 1. Linear (Steady) Algorithm
**Concept:** Constant velocity. The stroke is drawn at a perfectly even speed from start to finish.
**Mathematical Model:**
`Velocity (v) = Constant`
`Position (p) = p0 + v * t`

**Implementation:**
The `linear` algorithm simply maps the normalized time `t` (from `0.0` to `1.0`) directly to the path progression.

## 2. Minimum Jerk Model (Smooth)
**Concept:** Simulates smooth, robotic, or highly controlled human motion. It minimizes the rate of change of acceleration (jerk) over the duration of the movement.
**Mathematical Model:**
The progression `p(t)` for `t` in `[0, 1]` is defined by the polynomial:
`p(t) = 10*t^3 - 15*t^4 + 6*t^5`

**Implementation:**
This formula ensures that the velocity and acceleration are zero at the start and end of the stroke, resulting in a gentle ease-in and ease-out effect.

## 3. Two-Thirds Power Law (Natural Human)
**Concept:** Based on empirical studies of human handwriting. It posits that human drawing speed is inversely proportional to the curvature of the path. When drawing a tight curve, the hand slows down; when drawing a straight line, the hand speeds up.
**Mathematical Model:**
`Velocity (v) ∝ Curvature (K)^(-1/3)`
Therefore, `Angular Velocity (A) ∝ K^(2/3)`

**Implementation in the Engine:**
In `core.writing_engine.algorithms.physics_algorithms`, since calculating the exact curvature dynamically for every point is computationally expensive in real-time for QPainterPath, the implementation uses an approximation that combines a minimum jerk profile with sinusoidal variations to simulate the micro-pauses and accelerations typical of human handwriting.

## 4. Stop and Go
**Concept:** Simulates a hesitant drawing style, where the pen frequently stops and starts.
**Mathematical Model:**
This is achieved by applying a quantized or stepped function over time, layered with a smoothing interpolation.
`t_effective = floor(t * steps) / steps + smoothstep(fract(t * steps))`

## 5. Ornstein-Uhlenbeck Noise (Organic Sketch)
**Concept:** Introduces mean-reverting stochastic noise to the drawing velocity, simulating an organic, slightly erratic, or sketched feel.
**Mathematical Model:**
The Ornstein-Uhlenbeck process models the velocity of a massive Brownian particle under the influence of friction.
`dx_t = theta * (mu - x_t) * dt + sigma * dW_t`
Where:
*   `theta`: Rate of mean reversion.
*   `mu`: Long-term mean (the target steady velocity).
*   `sigma`: Volatility or randomness.
*   `dW_t`: Wiener process (Brownian motion increment).

**Implementation:**
The engine uses a pre-calculated noise array or a simplified Perlin/Simplex noise function mapped over the normalized time `t` to perturb the standard linear progression, causing the stroke to speed up and slow down unpredictably while maintaining an overall forward trajectory.
