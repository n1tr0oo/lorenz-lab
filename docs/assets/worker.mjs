import { simulate } from './solver.mjs';
self.onmessage = ({ data }) => {
  try {
    const result = simulate(data);
    self.postMessage({ ok: true, result }, [result.values.buffer]);
  } catch (error) {
    self.postMessage({ ok: false, error: error.message });
  }
};
