export const defaults = Object.freeze({ sigma: 10, rho: 28, beta: 8 / 3,
  initial: [1, 1, 1], duration: 30, sample_step: 0.01, transient: 5 });

export function validate(input) {
  const c = { ...defaults, ...input };
  const bounds = { sigma: [0, 100, true], rho: [0, 200, false],
    beta: [0, 50, true], duration: [0, 50, true], sample_step: [0.005, 0.25, false] };
  for (const [name, [min, max, strict]] of Object.entries(bounds)) {
    const v = c[name];
    if (typeof v !== 'number' || !Number.isFinite(v) || v > max || (strict ? v <= min : v < min))
      throw new Error(`Недопустимое значение ${name}.`);
  }
  if (!Array.isArray(c.initial) || c.initial.length !== 3 ||
      c.initial.some(v => typeof v !== 'number' || !Number.isFinite(v) || Math.abs(v) > 100))
    throw new Error('Начальные координаты должны быть числами от −100 до 100.');
  if (typeof c.transient !== 'number' || !Number.isFinite(c.transient) ||
      c.transient < 0 || c.transient >= c.duration)
    throw new Error('Скрываемый начальный интервал должен быть меньше длительности расчёта.');
  if (Math.ceil(c.duration / c.sample_step) + 1 > 10001)
    throw new Error('Слишком много отсчётов. Увеличьте интервал вывода.');
  c.initial = [...c.initial];
  return c;
}

export function derivative([x, y, z], c) {
  return [c.sigma * (y - x), x * (c.rho - z) - y, x * y - c.beta * z];
}

export function rk4(state, h, c) {
  const add = (a, b, factor) => a.map((v, i) => v + factor * b[i]);
  const k1 = derivative(state, c);
  const k2 = derivative(add(state, k1, h / 2), c);
  const k3 = derivative(add(state, k2, h / 2), c);
  const k4 = derivative(add(state, k3, h), c);
  return state.map((v, i) => v + h * (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i]) / 6);
}

export function simulate(input, maxStep = 0.001) {
  const config = validate(input);
  if (!Number.isFinite(maxStep) || maxStep <= 0 || maxStep > 0.001)
    throw new Error('Недопустимый шаг интегрирования.');
  const intervals = Math.ceil(config.duration / config.sample_step);
  const dt = config.duration / intervals;
  const substeps = Math.ceil(dt / maxStep - 1e-10);
  const h = dt / substeps;
  if (intervals * substeps > 100000)
    throw new Error('Превышен лимит шагов интегрирования.');
  const values = new Float64Array((intervals + 1) * 4);
  let state = [...config.initial];
  values.set([0, ...state], 0);
  for (let i = 1; i <= intervals; i++) {
    for (let j = 0; j < substeps; j++) {
      state = rk4(state, h, config);
      if (state.some(v => !Number.isFinite(v) || Math.abs(v) >= 1e6))
        throw new Error('Расчёт вышел за пределы численной устойчивости. Измените параметры.');
    }
    values.set([i === intervals ? config.duration : i * dt, ...state], i * 4);
  }
  return { config, values, samples: intervals + 1, step: h,
    effective_sample_step: dt, evaluations: intervals * substeps * 4, solver: 'RK4' };
}
