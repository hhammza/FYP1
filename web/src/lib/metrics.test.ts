import { compact, pct, pyFixed, summarizeMetrics } from './metrics';

const LGBM = {
  trained: true,
  default_threshold: 0.15,
  metrics: {
    run_id: 'D3_forecaster_deploy_v7',
    algorithm: 'LightGBM',
    threshold_rule: 'VME <= 10% on validation genomes',
    evaluation: { split: 'genome-grouped split' },
    test: { auc_roc: 0.7741, auc_roc_ci: [0.7702, 0.778], recall: 0.9, very_major_error: 0.1, major_error: 0.42 },
    data: { train_rows: 6271378, train_genomes: 20000, test_genomes: 4285, antibiotics: 126, genera: ['a', 'b', 'c'] },
  },
};

describe('summarizeMetrics', () => {
  it('formats a measured model as the Flask frontend did', () => {
    const s = summarizeMetrics(LGBM);
    expect(s.measured).toBe(true);
    expect(s.auc).toBe('0.774');
    expect(s.auc_ci).toBe('0.774 [0.770–0.778]');
    expect(s.recall).toBe('90.0%');
    expect(s.very_major_error).toBe('10.0%');
    expect(s.threshold).toBe(0.15);
    expect(s.train_rows).toBe('6,271,378');
    expect(s.train_rows_short).toBe('6.3M');
    expect(s.genera).toBe(3);
    expect(s.genomes_total).toBe('24,285');
    expect(s.split).toBe('genome-grouped split');
    expect(s.run_id).toBe('D3_forecaster_deploy_v7');
  });

  it('never falls back to an old figure when the metrics are missing', () => {
    for (const status of [undefined, null, {}, { trained: true }]) {
      const s = summarizeMetrics(status);
      expect(s.measured).toBe(false);
      expect(s.auc).toBe('not measured');
      expect(s.auc_ci).toBe('not measured');
      expect(s.recall).toBe('not measured');
      expect(s.train_rows).toBe('not measured');
      expect(s.train_rows_short).toBe('n/a');
      expect(s.genomes_total).toBe('n/a');
    }
  });

  it('uses the AUC alone when there is no confidence interval', () => {
    expect(summarizeMetrics({ metrics: { test: { auc_roc: 0.935 } } }).auc_ci).toBe('0.935');
  });

  it('takes the threshold from the metrics file when health gives none', () => {
    expect(summarizeMetrics({ metrics: { threshold: 0.43 } }).threshold).toBe(0.43);
  });
});

describe('number helpers', () => {
  it('compacts counts for narrow tiles', () => {
    expect(compact(1217307)).toBe('1.2M');
    expect(compact(6002)).toBe('6.0K');
    expect(compact(999)).toBe('999');
    expect(compact(0)).toBe('n/a');
    expect(compact(undefined)).toBe('n/a');
  });

  it('formats a fraction as a percentage', () => {
    expect(pct(0.0951)).toBe('9.5%');
    expect(pct('0.1')).toBe('not measured');
    expect(pct(NaN)).toBe('not measured');
  });
});

describe('pyFixed', () => {
  it('rounds an exact tie to the even digit, as Python does', () => {
    expect(pyFixed(23.25, 1)).toBe('23.2');      // toFixed gives 23.3
    expect(pyFixed(23.35, 1)).toBe('23.4');      // 23.35 is not exact in binary: above the tie
    expect(pyFixed(0.125, 2)).toBe('0.12');
    expect(pyFixed(0.375, 2)).toBe('0.38');
    expect(pyFixed(2.5, 0)).toBe('2');
    expect(pyFixed(3.5, 0)).toBe('4');
    expect(pyFixed(9.95, 1)).toBe('9.9');        // binary 9.9499…: below the tie, both agree
    expect(pyFixed(99.5, 0)).toBe('100');
    expect(pyFixed(-0.125, 2)).toBe('-0.12');
  });

  it('agrees with toFixed away from ties', () => {
    for (const x of [0.7741, 0.0951, 12.3456, 1e-7, 6271378 / 1e6]) {
      for (const d of [0, 1, 3]) expect(pyFixed(x, d)).toBe(x.toFixed(d));
    }
  });
});
