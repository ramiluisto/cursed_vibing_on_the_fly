from typing import Annotated

from pydantic import BaseModel, Field

from cursed_vibing_on_the_fly import ai_implement


# Example 1: Simple types
@ai_implement
def check_if_integer_is_prime(n: int) -> bool:
    """Check if n is a prime number."""
    pass

# Example 2: Annotated descriptions
@ai_implement
def calculate_compound_interest(
    principal: Annotated[float, "Initial investment amount"],
    rate: Annotated[float, "Annual interest rate as decimal (e.g., 0.05 for 5%)"],
    years: Annotated[int, "Number of years"],
    compounds_per_year: Annotated[int, "Compounding frequency"] = 12,
) -> Annotated[float, "Final amount after interest"]:
    """Calculate compound interest."""
    pass

# Example 3: Pydantic models
class Point(BaseModel):
    x: float = Field(description="X coordinate")
    y: float = Field(description="Y coordinate")

class LineSegment(BaseModel):
    start: Point = Field(description="Starting point")
    end: Point = Field(description="Ending point")
    length: float = Field(description="Euclidean length of segment")

@ai_implement
def create_line_segment(
    p1: Annotated[Point, "First point"],
    p2: Annotated[Point, "Second point"],
) -> Annotated[
    LineSegment, "Line segment connecting the points with computed length"
]:
    """Create a line segment between two points, computing the length."""
    pass

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("TESTING AI-IMPLEMENTED FUNCTIONS")
    print("=" * 60)

    print(f"\n🔢 Is 17 prime? {check_if_integer_is_prime(17)}")
    print(f"🔢 Is 18 prime? {check_if_integer_is_prime(18)}")  # Uses cache

    result = calculate_compound_interest(1000, 0.05, 10)
    print(f"\n💰 $1000 at 5% for 10 years = ${result:.2f}")

    segment = create_line_segment(Point(x=0, y=0), Point(x=3, y=4))
    print(f"\n📏 Segment: {segment}")
    print(f"   Length: {segment.length}")  # Should be 5.0

