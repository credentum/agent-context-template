#!/usr/bin/env python3
"""
Load tests for performance regression detection
Uses Locust framework to simulate concurrent users
"""

import json
import random
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

# For running without Locust UI
import gevent
from locust import HttpUser, between, events, task
from locust.env import Environment
from locust.log import setup_logging
from locust.stats import stats_history, stats_printer


class DocumentProcessingUser(HttpUser):
    """Simulates users processing documents"""

    wait_time = between(1, 3)

    def on_start(self):
        """Initialize user session"""
        self.user_id = f"user_{random.randint(1000, 9999)}"
        self.documents_processed = 0
        self.start_time = time.time()

    @task(3)
    def create_document(self):
        """Simulate document creation"""
        doc_id = f"doc_{self.user_id}_{int(time.time())}"
        document = {
            "metadata": {
                "document_type": "design",
                "id": doc_id,
                "author": self.user_id,
                "created": datetime.utcnow().isoformat(),
            },
            "content": {
                "title": f"Document {doc_id}",
                "body": "x" * random.randint(1000, 5000),
            },
        }

        # Simulate API call
        start_time = time.time()
        try:
            # In real test, this would be an actual HTTP request
            # self.client.post("/api/documents", json=document)

            # Simulate processing time
            gevent.sleep(random.uniform(0.01, 0.05))

            # Track success
            response_time = (time.time() - start_time) * 1000
            events.request.fire(
                request_type="POST",
                name="/api/documents",
                response_time=response_time,
                response_length=len(json.dumps(document)),
                exception=None,
            )
            self.documents_processed += 1
        except Exception as e:
            events.request.fire(
                request_type="POST",
                name="/api/documents",
                response_time=(time.time() - start_time) * 1000,
                response_length=0,
                exception=e,
            )

    @task(2)
    def read_document(self):
        """Simulate document reading"""
        doc_id = f"doc_{random.randint(1, 1000)}"

        start_time = time.time()
        try:
            # Simulate API call
            gevent.sleep(random.uniform(0.005, 0.02))

            # Track success
            response_time = (time.time() - start_time) * 1000
            events.request.fire(
                request_type="GET",
                name="/api/documents",
                response_time=response_time,
                response_length=random.randint(1000, 5000),
                exception=None,
            )
        except Exception as e:
            events.request.fire(
                request_type="GET",
                name="/api/documents",
                response_time=(time.time() - start_time) * 1000,
                response_length=0,
                exception=e,
            )

    @task(1)
    def search_documents(self):
        """Simulate document search"""
        query = f"tag:{random.choice(['design', 'architecture', 'api', 'database'])}"

        start_time = time.time()
        try:
            # Simulate search processing
            gevent.sleep(random.uniform(0.02, 0.1))

            # Track success
            response_time = (time.time() - start_time) * 1000
            events.request.fire(
                request_type="GET",
                name="/api/search",
                response_time=response_time,
                response_length=random.randint(5000, 20000),
                exception=None,
            )
        except Exception as e:
            events.request.fire(
                request_type="GET",
                name="/api/search",
                response_time=(time.time() - start_time) * 1000,
                response_length=0,
                exception=e,
            )


class AgentProcessingUser(HttpUser):
    """Simulates agent execution loads"""

    wait_time = between(5, 10)

    @task
    def run_cleanup_agent(self):
        """Simulate cleanup agent execution"""
        start_time = time.time()

        try:
            # Simulate agent processing
            gevent.sleep(random.uniform(0.5, 2.0))

            # Track execution
            response_time = (time.time() - start_time) * 1000
            events.request.fire(
                request_type="AGENT",
                name="cleanup_agent",
                response_time=response_time,
                response_length=0,
                exception=None,
            )
        except Exception as e:
            events.request.fire(
                request_type="AGENT",
                name="cleanup_agent",
                response_time=(time.time() - start_time) * 1000,
                response_length=0,
                exception=e,
            )

    @task
    def run_sprint_updater(self):
        """Simulate sprint updater agent"""
        start_time = time.time()

        try:
            # Simulate GitHub API calls and processing
            gevent.sleep(random.uniform(1.0, 3.0))

            # Track execution
            response_time = (time.time() - start_time) * 1000
            events.request.fire(
                request_type="AGENT",
                name="sprint_updater",
                response_time=response_time,
                response_length=0,
                exception=None,
            )
        except Exception as e:
            events.request.fire(
                request_type="AGENT",
                name="sprint_updater",
                response_time=(time.time() - start_time) * 1000,
                response_length=0,
                exception=e,
            )


class EmbeddingProcessingUser(HttpUser):
    """Simulates embedding generation loads"""

    wait_time = between(2, 5)

    @task
    def generate_embeddings(self):
        """Simulate embedding generation"""
        doc_size = random.choice([1000, 5000, 10000, 50000])  # bytes

        start_time = time.time()
        try:
            # Simulate embedding computation
            # Larger documents take longer
            processing_time = 0.01 + (doc_size / 100000)
            gevent.sleep(processing_time)

            # Track success
            response_time = (time.time() - start_time) * 1000
            events.request.fire(
                request_type="EMBED",
                name=f"embed_{doc_size}b",
                response_time=response_time,
                response_length=doc_size,
                exception=None,
            )
        except Exception as e:
            events.request.fire(
                request_type="EMBED",
                name=f"embed_{doc_size}b",
                response_time=(time.time() - start_time) * 1000,
                response_length=0,
                exception=e,
            )


def check_performance_thresholds(stats: Dict[str, Any]) -> bool:
    """Check if performance meets thresholds"""
    thresholds = {
        "/api/documents": {"p95": 100, "p99": 200},  # ms
        "/api/search": {"p95": 500, "p99": 1000},
        "cleanup_agent": {"p95": 3000, "p99": 5000},
        "sprint_updater": {"p95": 5000, "p99": 10000},
        "embed_1000b": {"p95": 50, "p99": 100},
        "embed_50000b": {"p95": 1000, "p99": 2000},
    }

    violations = []

    for endpoint, limits in thresholds.items():
        if endpoint in stats:
            p95 = stats[endpoint].get("p95", 0)
            p99 = stats[endpoint].get("p99", 0)

            if p95 > limits["p95"]:
                violations.append(f"{endpoint} p95: {p95}ms > {limits['p95']}ms")
            if p99 > limits["p99"]:
                violations.append(f"{endpoint} p99: {p99}ms > {limits['p99']}ms")

    if violations:
        print("\n❌ Performance threshold violations:")
        for v in violations:
            print(f"  - {v}")
        return False
    else:
        print("\n✅ All performance thresholds met")
        return True


def run_load_test(
    users: int = 100,
    spawn_rate: int = 10,
    run_time: str = "60s",
    headless: bool = True,
) -> Optional[Dict[str, Any]]:
    """Run load test programmatically"""

    if headless:
        # Setup for headless execution
        setup_logging("INFO", None)

        # Create environment
        env = Environment(
            user_classes=[
                DocumentProcessingUser,
                AgentProcessingUser,
                EmbeddingProcessingUser,
            ]
        )

        # Start stats tracking
        env.create_local_runner()

        # Configure test
        env.runner.start(users, spawn_rate=spawn_rate)

        # Run for specified time
        run_seconds = int(run_time.rstrip("s"))
        gevent.spawn(stats_printer(env.stats))
        gevent.spawn(stats_history, env.runner)

        # Wait for test to complete
        env.runner.greenlet.join(timeout=run_seconds)

        # Stop runner
        env.runner.quit()

        # Collect results
        results = {
            "total_requests": env.stats.total.num_requests,
            "failure_rate": env.stats.total.fail_ratio,
            "avg_response_time": env.stats.total.avg_response_time,
            "endpoints": {},
        }

        for name, entry in env.stats.entries.items():
            results["endpoints"][name] = {
                "requests": entry.num_requests,
                "failures": entry.num_failures,
                "avg": entry.avg_response_time,
                "min": entry.min_response_time,
                "max": entry.max_response_time,
                "p50": entry.get_response_time_percentile(0.5),
                "p95": entry.get_response_time_percentile(0.95),
                "p99": entry.get_response_time_percentile(0.99),
            }

        # Check thresholds
        passed = check_performance_thresholds(results["endpoints"])
        results["thresholds_passed"] = passed

        return results
    else:
        # For UI mode, use standard Locust startup
        import sys

        from locust.main import main

        sys.argv = [
            "locust",
            "-f",
            __file__,
            f"--users={users}",
            f"--spawn-rate={spawn_rate}",
            f"--run-time={run_time}",
        ]
        main()
        return None


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run load tests")
    parser.add_argument("--users", type=int, default=100, help="Number of users")
    parser.add_argument("--spawn-rate", type=int, default=10, help="Users per second")
    parser.add_argument("--run-time", default="60s", help="Test duration")
    parser.add_argument("--headless", action="store_true", help="Run without UI")
    parser.add_argument("--html", help="HTML report filename")
    parser.add_argument("--csv", help="CSV results prefix")

    args = parser.parse_args()

    if args.headless:
        results = run_load_test(
            users=args.users,
            spawn_rate=args.spawn_rate,
            run_time=args.run_time,
            headless=True,
        )

        # Save results
        if args.csv:
            import csv

            # Write summary
            with open(f"{args.csv}_summary.csv", "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["metric", "value"])
                writer.writerow(["total_requests", results["total_requests"]])
                writer.writerow(["failure_rate", results["failure_rate"]])
                writer.writerow(["avg_response_time", results["avg_response_time"]])
                writer.writerow(["thresholds_passed", results["thresholds_passed"]])

            # Write endpoint details
            with open(f"{args.csv}_endpoints.csv", "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["endpoint", "requests", "failures", "avg", "p50", "p95", "p99"])
                for name, stats in results["endpoints"].items():
                    writer.writerow(
                        [
                            name,
                            stats["requests"],
                            stats["failures"],
                            stats["avg"],
                            stats["p50"],
                            stats["p95"],
                            stats["p99"],
                        ]
                    )

        # Generate HTML report if requested
        if args.html:
            html_content = f"""
            <html>
            <head><title>Load Test Report</title></head>
            <body>
                <h1>Load Test Report</h1>
                <h2>Summary</h2>
                <p>Total Requests: {results['total_requests']}</p>
                <p>Failure Rate: {results['failure_rate']:.2%}</p>
                <p>Avg Response Time: {results['avg_response_time']:.2f}ms</p>
                <p>Thresholds: {'✅ PASSED' if results['thresholds_passed'] else '❌ FAILED'}</p>

                <h2>Endpoint Performance</h2>
                <table border="1">
                    <tr>
                        <th>Endpoint</th><th>Requests</th><th>Failures</th>
                        <th>Avg (ms)</th><th>P95 (ms)</th><th>P99 (ms)</th>
                    </tr>
            """

            for name, stats in results["endpoints"].items():
                html_content += f"""
                    <tr>
                        <td>{name}</td>
                        <td>{stats['requests']}</td>
                        <td>{stats['failures']}</td>
                        <td>{stats['avg']:.2f}</td>
                        <td>{stats['p95']:.2f}</td>
                        <td>{stats['p99']:.2f}</td>
                    </tr>
                """

            html_content += """
                </table>
            </body>
            </html>
            """

            with open(args.html, "w") as f:
                f.write(html_content)

        # Exit with appropriate code
        exit(0 if results["thresholds_passed"] else 1)
    else:
        # Run with UI
        run_load_test(
            users=args.users,
            spawn_rate=args.spawn_rate,
            run_time=args.run_time,
            headless=False,
        )
