import argparse
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.universe import QueryUniverseGenerator
from src.runner import run_intelligence_pipeline

def main():
    parser = argparse.ArgumentParser(description="Thailand AI Market & Decision Intelligence CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    gen_parser = subparsers.add_parser("generate", help="Generate Thai consumer queries")
    gen_parser.add_argument("--count", type=int, default=10, help="Number of queries to generate")
    gen_parser.add_argument("--seed", type=int, default=42, help="Random seed")

    run_parser = subparsers.add_parser("run", help="Run full observation pipeline")
    run_parser.add_argument("--count", type=int, default=10, help="Number of queries to audit")
    run_parser.add_argument("--engine", type=str, default="mock", choices=["mock", "gemini", "openrouter"], help="Observation Engine")
    run_parser.add_argument("--seed", type=int, default=42, help="Random seed")

    args = parser.parse_args()

    if args.command == "generate":
        gen = QueryUniverseGenerator()
        queries = gen.generate_queries(count=args.count, seed=args.seed)
        print(f"\n🎯 Generated {len(queries)} Queries:")
        for q in queries:
            print(f"- [{q['query_id']}] ({q['category']}): {q['text_th']}")

    elif args.command == "run":
        run_intelligence_pipeline(count=args.count, seed=args.seed, engine_type=args.engine)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
