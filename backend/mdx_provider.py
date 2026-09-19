import os
from .models import ValuationContext, DatabaseDriver


def get_demo_context(portfolio_id: str) -> ValuationContext:
    return ValuationContext(
        portfolio_id=portfolio_id,
        area="Credit",
        sector="Securitized Products",
        product="European ABS",
        valuation_date="2026-09-19",
        valuation_movement=4.3,
        currency="USD",
        unit="m",
        top_drivers=[
            DatabaseDriver(name="CDS spreads", amount=3.8, direction="positive"),
            DatabaseDriver(name="New trades", amount=0.7, direction="positive"),
            DatabaseDriver(name="Other", amount=-0.2, direction="negative"),
        ],
    )


def get_context_from_mdx(portfolio_id: str) -> ValuationContext:
    """
    Production hook for an SSAS/MDX query.

    Keep database-specific code here so the rest of the application remains
    independent of your cube implementation.
    """
    if os.getenv("MDX_ENABLED", "false").lower() != "true":
        return get_demo_context(portfolio_id)

    connection_string = os.getenv("MDX_CONNECTION_STRING", "")
    if not connection_string:
        raise RuntimeError("MDX_ENABLED=true but MDX_CONNECTION_STRING is empty.")

    try:
        from pyadomd import Pyadomd
    except ImportError as exc:
        raise RuntimeError(
            "pyadomd is required when MDX_ENABLED=true."
        ) from exc

    # Replace this with your real cube, dimensions and measures.
    mdx = f"""
    SELECT
        {{ [Measures].[Valuation Movement] }} ON COLUMNS
    FROM [YourCube]
    WHERE ([Portfolio].[Portfolio].&[{portfolio_id}])
    """

    with Pyadomd(connection_string) as conn:
        with conn.cursor().execute(mdx) as cur:
            row = cur.fetchone()

    if not row:
        raise RuntimeError(f"No valuation data returned for {portfolio_id}.")

    movement = float(row[0])

    # Add your real Area/Sector/Product/top-driver extraction here.
    return ValuationContext(
        portfolio_id=portfolio_id,
        area="Credit",
        sector="Securitized Products",
        product="European ABS",
        valuation_date="2026-09-19",
        valuation_movement=movement,
        currency="USD",
        unit="m",
        top_drivers=[],
    )
