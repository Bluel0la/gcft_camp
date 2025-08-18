from typing import Optional
def beds_required(no_children: Optional[int]) -> int:
    if not no_children or no_children < 3:
        return 1
    return 2

