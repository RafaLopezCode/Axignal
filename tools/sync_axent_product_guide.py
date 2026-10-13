"""Generate the standalone web snapshot from packaged AXENT product guidance."""

from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    source = root / "application/axent/product-guide.json"
    target = root / "apps/web/experience/lib/axent-product-guide.json"
    target.write_bytes(source.read_bytes())


if __name__ == "__main__":
    main()
