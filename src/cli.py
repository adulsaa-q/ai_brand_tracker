import argparse
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.migrate_v1_to_v3 import migrate_csv_to_stores
from src.engines.model_registry import OpenRouterModelRegistry
from src.runner import run_intelligence_pipeline
from src.universe import QueryUniverseGenerator


def main():
    parser = argparse.ArgumentParser(description="🇹🇭 Thailand AI Market & Decision Intelligence CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # generate
    gen_parser = subparsers.add_parser("generate", help="Generate Thai consumer queries")
    gen_parser.add_argument("--count", type=int, default=10, help="Number of queries to generate")
    gen_parser.add_argument("--seed", type=int, default=42, help="Random seed")
    gen_parser.add_argument("--control", action="store_true", help="Include invariant 30 benchmark control set")

    # run
    run_parser = subparsers.add_parser("run", help="Run full observation pipeline")
    run_parser.add_argument("--count", type=int, default=15, help="Number of queries to audit")
    run_parser.add_argument(
        "--engine",
        type=str,
        default="mock",
        choices=["mock", "gemini", "openrouter", "tavily", "serper"],
        help="Observation Engine",
    )
    run_parser.add_argument("--seed", type=int, default=42, help="Random seed")
    run_parser.add_argument(
        "--control", action="store_true", default=True, help="Include invariant control benchmark set"
    )

    # migrate
    mig_parser = subparsers.add_parser("migrate", help="Migrate legacy v1/v2 results CSV to DuckDB & SQLite")
    mig_parser.add_argument("--csv", type=str, default="sample_output/results_sample.csv", help="Source CSV file")

    # models
    subparsers.add_parser("models", help="Discover free AI models on OpenRouter")

    # dashboard
    subparsers.add_parser("dashboard", help="Launch Executive Streamlit Dashboard")

    # web
    subparsers.add_parser("web", help="Launch Modern HTML5/JS Executive Web Command Center (Style Q)")

    args = parser.parse_args()

    if args.command == "generate":
        gen = QueryUniverseGenerator()
        queries = gen.generate_queries(count=args.count, seed=args.seed, include_control=args.control)
        print(f"\n🎯 Generated {len(queries)} Queries:")
        for q in queries:
            tag = "[CONTROL]" if q.get("is_control_set") else "[EXPLORATORY]"
            print(f"- {tag} [{q['query_id']}] ({q['category']}): {q['text_th']}")

    elif args.command == "run":
        run_intelligence_pipeline(
            count=args.count, seed=args.seed, engine_type=args.engine, include_control=args.control
        )

    elif args.command == "migrate":
        migrate_csv_to_stores(csv_path=args.csv)

    elif args.command == "models":
        reg = OpenRouterModelRegistry()
        free_models = reg.get_free_tier_candidates()
        print(f"\n🤖 Discovered {len(free_models)} Free Models on OpenRouter:")
        for m in free_models:
            print(f" - {m['id']}: {m['name']} (Context: {m['context_length']})")

    elif args.command == "dashboard":
        import subprocess

        print("🚀 Launching Streamlit Executive Dashboard...")
        subprocess.run(["streamlit", "run", "dashboard/app.py"])

    elif args.command == "web":
        import http.server
        import os
        import socketserver
        import webbrowser

        web_dir = os.path.abspath("dashboard/web")
        os.chdir(web_dir)
        PORT = 8080
        handler = http.server.SimpleHTTPRequestHandler
        print(f"🌐 Modern Executive Web Command Center (Style Q) running at http://localhost:{PORT}")
        webbrowser.open(f"http://localhost:{PORT}")
        with socketserver.TCPServer(("", PORT), handler) as httpd:
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\nWeb server stopped.")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
