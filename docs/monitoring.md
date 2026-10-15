# Interpret resource measurements

The collector runs inside the HA container once per minute through the command_line integration. It reads `/proc` and publishes JSON. A small cache stores previous counters for rate calculations; it contains no credentials.

| Metric | Definition |
|---|---|
| Pi CPU | Busy time as a fraction of aggregate CPU time across all cores; idle and I/O wait are excluded from busy time |
| HA CPU | HA process user + system CPU ticks divided by the aggregate CPU tick delta |
| Pi memory | MemTotal minus MemAvailable, in MiB |
| HA resident memory | VmRSS, in MiB |
| HA proportional memory | PSS from smaps_rollup, best effort, in MiB |

On four cores, one fully occupied HA core is about 25% of total capacity. This is intentional. Linux load average counts runnable or I/O-waiting tasks; dividing it by core count does not turn it into CPU utilization percent.

RSS includes resident shared pages. PSS apportions them. Neither equals total system pressure; also inspect available memory and swap. A large virtual address space is not resident RAM. Docker image size is storage, not process RAM.

## History and thresholds

Sampling once per minute catches sustained changes and averages away short spikes. Compare charts with automation timestamps to form a hypothesis; correlation is not proof. A single before/after sample cannot establish a leak or a memory improvement.

The installed warning helpers are editable. Their configured maximum is not the active warning threshold. CPU uses a five-minute delay and HA memory a ten-minute delay; they are dashboard indicators, not automatic restarts.

The raw multiplexed sensor is excluded from recorder to avoid duplicating attributes. Derived numeric sensors have measurement metadata. Detailed history currently lasts seven days; hourly statistics can cover longer periods after they accumulate.

## Collector contract

The first valid sample after process identity changes has unavailable CPU rates. Current memory and temperature still work. Identity includes boot ID, process ID and process start time. Invalid or unexpected cache data is rebuilt. The cache uses atomic replacement; concurrent invocations still share a temporary filename, so keep one scheduled collector instance.

`scripts/resource_sample.py` defaults to a cache under `/config`; `HA_RESOURCE_CACHE` can override it. Run it inside Linux where the target HA process and host `/proc` counters are visible. It is not a portable Mac resource collector.

## Benchmark

Compare at equal warm-up times and representative workloads. For offloaded integrations, measure HA + broker + adapter combined PSS, plus CPU, latency and failures. Disable all native entries for the migrated protocol and restart HA before evaluating library-removal savings. An unload may leave imported modules in memory.

Sources: [Linux load average](https://man7.org/linux/man-pages/man5/proc_loadavg.5.html), [HA command_line](https://www.home-assistant.io/integrations/command_line/), [Docker pruning](https://docs.docker.com/engine/manage-resources/pruning/).
