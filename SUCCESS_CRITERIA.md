# Success Criteria

This document defines measurable performance benchmarks, SLOs, and profiling
practices for the Kimberly project. Use these baselines to track improvements,
detect regressions, and ensure quality before releases.

## Performance Baselines

### Latency Targets

All latency targets are measured under standard load conditions (single user,
warm cache, warm model).

| Metric | p50 Target | p95 Target | p99 Target | Notes |
| ------ | ---------- | ---------- | ---------- | ----- |
| Chat response | <500ms | <1000ms | <2000ms | Warm model inference |
| Initial model load | N/A | <30s | <45s | Cold start scenario |
| Memory retrieval | <200ms | <500ms | <750ms | Vector similarity search |
| Agent delegation | <2s | <5s | <8s | Task handoff to agent |
| Meditation job | N/A | <10min | <15min | Nightly scoring/pruning |
| API health check | <50ms | <100ms | <150ms | /health endpoint |
| Authentication | <100ms | <200ms | <300ms | JWT validation |

### Throughput Targets

| Metric | Target | Notes |
| ------ | ------ | ----- |
| Concurrent users | 10 | MVP single-instance target |
| Daily interactions | 1000+ | Expected daily message volume |
| API requests/sec | 50 | Sustained load capacity |
| Memory writes/sec | 10 | Memory tier operations |

### Availability & Uptime Targets

| Environment | Target Uptime | Max Planned Downtime | Notes |
| ----------- | ------------- | -------------------- | ----- |
| Development | N/A | N/A | No SLA |
| Staging | 95% | 4h/week | Maintenance windows allowed |
| Production (MVP) | 99% | 7h/month | Target for initial release |
| Production (GA) | 99.9% | 43min/month | Future target |

### Error Rate Targets

| Metric | Target | Notes |
| ------ | ------ | ----- |
| API error rate (5xx) | <1% | Server-side errors |
| API error rate (4xx) | <5% | Client errors (validation) |
| Model inference failures | <0.5% | LLM generation errors |
| Memory corruption | 0% | Critical data integrity |

## Profiling & Performance Analysis

### Recommended Profiling Tools

Use these tools to identify and resolve performance bottlenecks:

#### Python Profiling

- **py-spy**: Low-overhead sampling profiler for production use

  ```bash
  # Profile a running process
  py-spy top --pid <PID>

  # Record flame graph
  py-spy record -o profile.svg --pid <PID>

  # Profile a specific script
  py-spy record -o profile.svg -- python app.py
  ```

- **cProfile**: Built-in deterministic profiler for development

  ```bash
  python -m cProfile -o profile.pstats app.py
  python -c "import pstats; p = pstats.Stats('profile.pstats'); \
    p.sort_stats('cumulative').print_stats(20)"
  ```

- **memory-profiler**: Memory usage analysis

  ```bash
  pip install memory-profiler
  python -m memory_profiler app.py
  ```

- **line_profiler**: Line-by-line timing

  ```bash
  pip install line-profiler
  # Decorate functions with @profile and run:
  kernprof -l -v script.py
  ```

#### API & Network Profiling

- **locust**: Load testing for API endpoints
- **httpx** with timing: Request-level latency measurement
- **prometheus-client**: Metrics collection and export

### When to Profile

1. **Before releases**: Run profiling on staging to validate targets
2. **After feature additions**: Check for performance regressions
3. **When latency spikes**: Investigate using py-spy sampling
4. **Memory issues**: Use memory-profiler to find leaks
5. **CI validation**: Automated benchmarks in test suite

## CI Regression Monitoring

### Automated Performance Checks

Add performance validation to CI pipelines to prevent regressions:

```yaml
# Example GitHub Actions step for performance monitoring
- name: Run performance benchmarks
  run: |
    pip install pytest-benchmark
    PYTHONPATH=. pytest tests/benchmarks/ --benchmark-json=benchmark.json

- name: Check for regressions
  run: |
    # Compare against baseline and fail if >10% regression
    python scripts/check_benchmark_regression.py benchmark.json
```

### Benchmark Test Structure

Create benchmark tests in `tests/benchmarks/` directory:

```python
# tests/benchmarks/test_performance.py
import pytest

def test_health_endpoint_latency(benchmark):
    """Ensure /health responds within p95 target."""
    result = benchmark(call_health_endpoint)
    assert result.status_code == 200
    # pytest-benchmark handles timing automatically

def test_memory_retrieval_latency(benchmark):
    """Memory queries should complete within p95 target."""
    result = benchmark(query_memory, query="test query")
    assert len(result) >= 0
```

### Metrics to Track in CI

| Metric | Baseline Storage | Alert Threshold |
| ------ | ---------------- | --------------- |
| Test suite duration | Previous run | >20% increase |
| Memory usage peak | Baseline file | >15% increase |
| Endpoint latency p95 | Baseline JSON | >10% increase |
| Cold start time | Baseline file | >25% increase |

### Dashboard Integration

Export metrics to observability stack for long-term tracking:

- **Prometheus**: Scrape metrics from `/metrics` endpoint
- **Grafana**: Visualize latency percentiles and error rates
- **Alerting**: Configure alerts for SLO breaches

## Validation Checklist

Before each release, verify:

- [ ] All latency targets met under expected load
- [ ] No memory leaks detected (stable memory over 1h run)
- [ ] Error rates within acceptable thresholds
- [ ] CI benchmark tests passing without regressions
- [ ] Profiling completed for new features
- [ ] Staging environment tested for at least 24h

## References

- Performance targets from `ARCHITECTURE.md` (constraints section)
- KPIs defined in `docs/PM_CADENCE_AND_METRICS.md`
- Risk analysis in `SECURITY_AND_RISKS.md` (R-002: SLO validation)
- Related issues: `tune/slo-definition-and-benchmarks`
