"""Run the bundled deterministic offline dodge scenarios."""
from offline_data import load_maps, load_scenarios, plan_dodge


def main():
    maps = load_maps()
    scenarios = load_scenarios()
    for scenario in scenarios:
        arena = maps[scenario["map"]]
        result = plan_dodge(scenario, arena)
        dx, dy = result["direction"]
        print("%-24s direction=(%+.3f, %+.3f) cost=%.3f" %
              (scenario["id"], dx, dy, result["cost"]))
    print("Completed %d offline scenarios." % len(scenarios))


if __name__ == "__main__":
    main()
